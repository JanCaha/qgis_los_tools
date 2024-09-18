from functools import partial

import numpy as np
from qgis.core import Qgis, QgsGeometry, QgsPoint, QgsPointLocator, QgsPointXY, QgsVectorLayer, QgsVertexId
from qgis.gui import QgisInterface, QgsMapMouseEvent
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QAction

from los_tools.classes.list_raster import ListOfRasters
from los_tools.gui.create_los_tool.create_los_widget import LoSInputWidget
from los_tools.gui.create_los_tool.los_digitizing_tool_with_widget import LoSDigitizingToolWithWidget
from los_tools.gui.dialog_los_settings import LoSSettings
from los_tools.gui.dialog_raster_validations import RasterValidations
from los_tools.processing.tools.util_functions import get_max_decimal_numbers, round_all_values

from .los_tasks import LoSExtractionTaskManager, PrepareLoSTask, PrepareLoSWithoutTargetTask


class CreateLoSMapTool(LoSDigitizingToolWithWidget):
    featuresAdded = pyqtSignal()

    def __init__(
        self,
        iface: QgisInterface,
        raster_validation_dialog: RasterValidations,
        los_settings_dialog: LoSSettings,
        los_layer: QgsVectorLayer = None,
        add_result_action: QAction = None,
    ) -> None:
        super().__init__(iface)

        self.task_manager = LoSExtractionTaskManager()

        self._los_layer = los_layer

        self._raster_validation_dialog = raster_validation_dialog
        self._los_settings_dialog = los_settings_dialog

        self.add_result_action = add_result_action

        self._start_point: QgsPointXY = None

        self._last_towards_point: QgsPointXY = None

        self._widget = LoSInputWidget()
        self._widget.hide()

    def set_los_layer(self, layer: QgsVectorLayer) -> None:
        self._los_layer = layer

    def create_widget(self):
        if not self._widget:
            self._widget = LoSInputWidget()

        super().create_widget()

        self._widget.valuesChanged.connect(partial(self.draw_los, None))
        self._widget.saveToLayerClicked.connect(self.add_los_to_layer)

    def activate(self) -> None:
        super().activate()

        if not ListOfRasters.validate(self._raster_validation_dialog.list_of_selected_rasters):
            self.messageEmitted.emit(
                "Tool needs valid setup in `Raster Validations` dialog.",
                Qgis.Critical,
            )
            self.deactivate()
            return

    def clean(self) -> None:
        super().clean()
        if self._widget:
            self._widget.disableAddLos()
        self._start_point = None

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

    def draw_los(self, towards_point: QgsPointXY):
        if towards_point is None:
            towards_point = self._last_towards_point

        if not self.canvas_crs_is_projected():
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
                            self._raster_validation_dialog.listOfRasters.maximal_diagonal_size(),
                        )

                        # insert target point
                        line.get().insertVertex(
                            QgsVertexId(0, 0, 1),
                            QgsPoint(towards_point.x(), towards_point.y()),
                        )

                line = line.intersection(rasters_extent)

                self._los_rubber_band.setToGeometry(line, self._canvas.mapSettings().destinationCrs())

            if self._widget.los_no_target:
                self._los_rubber_band.setToGeometry(QgsGeometry(), self._canvas.mapSettings().destinationCrs())

                maximal_length_distance = self._los_settings_dialog.los_maximal_length()

                if maximal_length_distance is None:
                    maximal_length = self._raster_validation_dialog.listOfRasters.maximal_diagonal_size()
                else:
                    maximal_length = maximal_length_distance.inUnits(self._los_layer.crs().mapUnits())

                angle = self._start_point.azimuth(towards_point)

                angles = np.arange(
                    angle - self._widget.angle_difference,
                    angle + self._widget.angle_difference + 0.000000001 * self._widget.angle_step,
                    self._widget.angle_step,
                ).tolist()
                round_digits = get_max_decimal_numbers(
                    [
                        angle - self._widget.angle_difference,
                        angle + self._widget.angle_difference + 0.000000001 * self._widget.angle_step,
                        self._widget.angle_step,
                    ]
                )
                angles = round_all_values(angles, round_digits)
                size_constant = 1
                for angle in angles:
                    new_point = self._start_point.project(size_constant, angle)
                    line = QgsGeometry.fromPolylineXY([self._start_point, new_point])
                    line = line.extendLine(0, maximal_length - size_constant)

                    line = line.intersection(rasters_extent)

                    self._los_rubber_band.addGeometry(line, self._canvas.mapSettings().destinationCrs())

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
                self._los_layer,
                list_of_rasters,
                self._widget.observer_offset,
                self._widget.target_offset,
                self._widget.los_global,
                self._iface.mapCanvas().mapSettings().destinationCrs(),
            )

        else:
            task = PrepareLoSWithoutTargetTask(
                los_geometry,
                self._los_layer,
                list_of_rasters,
                self._los_settings_dialog,
                self._widget.observer_offset,
                self._widget.angle_step,
                self._iface.mapCanvas().mapSettings().destinationCrs(),
            )

        task.taskCompleted.connect(self.task_finished)
        task.taskFinishedTime.connect(self.task_finished_message)

        self.task_manager.addTask(task)

    def task_finished(self) -> None:
        self.featuresAdded.emit()
        if self.task_manager.all_los_tasks_finished():
            self.set_result_action_active(True)

    def task_finished_message(self, milliseconds: int) -> None:
        self._iface.messageBar().pushMessage(
            f"LoS Processing Finished. Lasted {milliseconds / 1000} seconds.",
            Qgis.MessageLevel.Info,
            2,
        )
