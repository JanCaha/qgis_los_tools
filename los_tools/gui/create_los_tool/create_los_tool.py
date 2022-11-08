import numpy as np
from functools import partial

from qgis.PyQt.QtWidgets import (QWidget, QAction)
from qgis.PyQt.QtCore import (Qt, pyqtSignal)
from qgis.PyQt.QtGui import (QKeyEvent)
from qgis.core import (QgsWkbTypes, QgsGeometry, QgsVectorLayer, QgsPointLocator, Qgis, QgsPoint,
                       QgsPointXY, QgsVertexId)
from qgis.gui import (QgisInterface, QgsMapMouseEvent, QgsSnapIndicator,
                      QgsMapToolAdvancedDigitizing)

from los_tools.classes import ListOfRasters
from los_tools.gui import LoSSettings
from los_tools.gui import RasterValidations
from los_tools.processing.tools.util_functions import get_max_decimal_numbers, round_all_values

from .create_los_widget import LoSNoTargetInputWidget
from .los_tasks import LoSExtractionTaskManager, PrepareLoSWithoutTargetTask, PrepareLoSTask


class CreateLoSMapTool(QgsMapToolAdvancedDigitizing):

    featuresAdded = pyqtSignal()

    def __init__(self,
                 iface: QgisInterface,
                 raster_validation_dialog: RasterValidations,
                 los_settings_dialog: LoSSettings,
                 los_layer: QgsVectorLayer = None,
                 add_result_action: QAction = None) -> None:

        super().__init__(iface.mapCanvas(), iface.cadDockWidget())
        self._iface = iface
        self._canvas = self._iface.mapCanvas()

        self.task_manager = LoSExtractionTaskManager()

        self._los_layer = los_layer

        self._raster_validation_dialog = raster_validation_dialog
        self._los_settings_dialog = los_settings_dialog

        self.add_result_action = add_result_action

        self._start_point: QgsPointXY = None

        self._last_towards_point: QgsPointXY = None

        self._snapper = self._canvas.snappingUtils()
        self.snap_marker = QgsSnapIndicator(self._canvas)

        self._los_rubber_band = self.createRubberBand(QgsWkbTypes.LineGeometry)

        self._widget: QWidget = None

    def set_los_layer(self, layer: QgsVectorLayer) -> None:
        self._los_layer = layer

    def create_widget(self):
        self.delete_widget()

        self._widget = LoSNoTargetInputWidget()
        self._iface.addUserInputWidget(self._widget)
        self._widget.setFocus(Qt.TabFocusReason)

        self._widget.valuesChanged.connect(partial(self.draw_los, None))
        self._widget.saveToLayerClicked.connect(self.add_los_to_layer)

    def delete_widget(self):
        if self._widget:
            self._widget.releaseKeyboard()
            self._widget.deleteLater()
            self._widget = None

    def activate(self) -> None:
        super(CreateLoSMapTool, self).activate()
        self.create_widget()
        self.messageDiscarded.emit()
        self._canvas = self._iface.mapCanvas()
        self._snapper = self._canvas.snappingUtils()
        if self._canvas.mapSettings().destinationCrs().isGeographic():
            self.messageEmitted.emit(
                "Tool only works if canvas is in projected CRS. Currently canvas is in geographic CRS.",
                Qgis.Critical)
            self.hide_widgets()
            self.deactivate()
            return
        if not ListOfRasters.validate(self._raster_validation_dialog.list_of_selected_rasters):
            self.messageEmitted.emit("Tool needs valid setup in `Raster Validatations` dialog.",
                                     Qgis.Critical)
            self.deactivate()
            return

    def clean(self) -> None:
        if self._widget:
            self._widget.disableAddLos()
        self.snap_marker.setVisible(False)
        self._los_rubber_band.hide()
        self._start_point = None

    def deactivate(self) -> None:
        self.clean()
        self.delete_widget()
        self._iface.mapCanvas().unsetMapTool(self)
        super(CreateLoSMapTool, self).deactivate()

    def canvasReleaseEvent(self, e: QgsMapMouseEvent) -> None:
        if e.button() == Qt.RightButton:
            self.clean()
        elif e.button() == Qt.LeftButton:
            if self._start_point is None:
                if self._snap_point:
                    self._start_point = self._snap_point
                else:
                    self._start_point = e.mapPoint()
            else:
                self.draw_los(self._snap_point)
                self._widget.enableAddLos()
                self._start_point = None

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        result = self._snapper.snapToMap(event.pos())
        self.snap_marker.setMatch(result)
        if result.type() == QgsPointLocator.Vertex:
            self._snap_point = result.point()
        else:
            self._snap_point = event.mapPoint()

        if self._start_point is not None:
            self.draw_los(self._snap_point)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key_Escape:
            self.deactivate()
            self._iface.mapCanvas().unsetMapTool(self)
        return super().keyPressEvent(e)

    def draw_los(self, towards_point: QgsPointXY):

        if towards_point is None:
            towards_point = self._last_towards_point

        canvas_crs = self._canvas.mapSettings().destinationCrs()

        if canvas_crs.isGeographic():
            self._iface.messageBar().pushMessage(
                "LoS can be drawn only for projected CRS. Canvas is currently in geographic CRS.",
                Qgis.Critical,
                duration=5)
            return

        if self._start_point and towards_point:

            self._los_rubber_band.hide()

            rasters_extent = self._raster_validation_dialog.listOfRasters.extent_polygon()

            if self._widget.los_local or self._widget.los_global:

                if self._widget.los_local:
                    line = QgsGeometry.fromPolylineXY([self._start_point, towards_point])

                if self._widget.los_global:
                    line = QgsGeometry.fromPolylineXY([self._start_point, towards_point])

                    if self._start_point.distance(towards_point) > 0:
                        line = line.extendLine(
                            0,
                            self._raster_validation_dialog.listOfRasters.maximal_diagonal_size())

                        # insert target point
                        line.get().insertVertex(QgsVertexId(0, 0, 1),
                                                QgsPoint(towards_point.x(), towards_point.y()))

                line = line.intersection(rasters_extent)

                self._los_rubber_band.setToGeometry(line,
                                                    self._canvas.mapSettings().destinationCrs())

            if self._widget.los_no_target:

                self._los_rubber_band.setToGeometry(QgsGeometry(),
                                                    self._canvas.mapSettings().destinationCrs())

                maximal_length_distance = self._los_settings_dialog.los_maximal_length()

                if maximal_length_distance is None:
                    maximal_length = self._raster_validation_dialog.listOfRasters.maximal_diagonal_size(
                    )
                else:
                    maximal_length = maximal_length_distance.inUnits(
                        self._los_layer.crs().mapUnits())

                angle = self._start_point.azimuth(towards_point)

                angles = np.arange(
                    angle - self._widget.angle_difference,
                    angle + self._widget.angle_difference + 0.000000001 * self._widget.angle_step,
                    self._widget.angle_step).tolist()
                round_digits = get_max_decimal_numbers([
                    angle - self._widget.angle_difference,
                    angle + self._widget.angle_difference + 0.000000001 * self._widget.angle_step,
                    self._widget.angle_step
                ])
                angles = round_all_values(angles, round_digits)
                size_constant = 1
                for angle in angles:
                    new_point = self._start_point.project(size_constant, angle)
                    line = QgsGeometry.fromPolylineXY([self._start_point, new_point])
                    line = line.extendLine(0, maximal_length - size_constant)

                    line = line.intersection(rasters_extent)

                    self._los_rubber_band.addGeometry(line,
                                                      self._canvas.mapSettings().destinationCrs())

            self._los_rubber_band.show()

        if towards_point:
            self._last_towards_point = QgsPointXY(towards_point.x(), towards_point.y())

    def set_result_action_active(self, active: bool) -> None:
        if self.add_result_action:
            self.add_result_action.setEnabled(active)

    def add_los_to_layer(self) -> None:
        los_geometry = self._los_rubber_band.asGeometry()

        list_of_rasters = self._raster_validation_dialog.listOfRasters

        # text = self.add_result_action.text()
        # self.add_result_action.setText("Obtaining data ...")
        self.set_result_action_active(False)

        if los_geometry.get().partCount() == 1:

            task = PrepareLoSTask(
                los_geometry,
                self._widget.sampling_distance.inUnits(self._los_layer.crs().mapUnits()),
                self._los_layer, list_of_rasters, self._widget.observer_offset,
                self._widget.target_offset, self._widget.los_global,
                self._iface.mapCanvas().mapSettings().destinationCrs())

        else:

            task = PrepareLoSWithoutTargetTask(
                los_geometry, self._los_layer, list_of_rasters, self._los_settings_dialog,
                self._widget.observer_offset, self._widget.angle_step,
                self._iface.mapCanvas().mapSettings().destinationCrs())

        task.taskCompleted.connect(self.task_finished)

        self.task_manager.addTask(task)

    def task_finished(self) -> None:
        self.featuresAdded.emit()
        if self.task_manager.all_los_tasks_finished():
            self.set_result_action_active(True)
        self._iface.messageBar().pushMessage("LoS Without Target Processing Finished",
                                             Qgis.MessageLevel.Info, 2)
