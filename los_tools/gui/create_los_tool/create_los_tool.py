from functools import partial

import numpy as np
from qgis.core import Qgis, QgsGeometry, QgsPoint, QgsPointXY, QgsVectorLayer, QgsVertexId
from qgis.gui import QgisInterface, QgsMapMouseEvent
from qgis.PyQt.QtCore import Qt, pyqtSignal

from los_tools.classes.list_raster import ListOfRasters
from los_tools.gui.create_los_tool.create_los_widget import LoSInputWidget
from los_tools.gui.create_los_tool.los_digitizing_tool_with_widget import LoSDigitizingToolWithWidget
from los_tools.gui.create_los_tool.los_tasks import (
    LoSExtractionTaskManager,
    PrepareLoSTask,
    PrepareLoSWithoutTargetTask,
)
from los_tools.gui.dialog_los_settings import LoSSettings
from los_tools.processing.tools.util_functions import get_max_decimal_numbers, round_all_values


class CreateLoSMapTool(LoSDigitizingToolWithWidget):
    featuresAdded = pyqtSignal()
    addLoSStatusChanged = pyqtSignal(bool)

    def __init__(
        self,
        iface: QgisInterface,
        raster_list: ListOfRasters,
        los_settings_dialog: LoSSettings,
        los_layer: QgsVectorLayer = None,
    ) -> None:
        super().__init__(iface)

        self.task_manager = LoSExtractionTaskManager()

        self._los_layer = los_layer

        self._raster_list = raster_list
        self._los_settings_dialog = los_settings_dialog

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

        self.addLoSStatusChanged.connect(self._widget.setAddLoSEnabled)
        self._widget.valuesChanged.connect(partial(self.draw_los, None))
        self._widget.saveToLayerClicked.connect(self.add_los_to_layer)

    def activate(self) -> None:
        super().activate()

        if not ListOfRasters.validate(self._raster_list.rasters):
            self.messageEmitted.emit(
                "Tool needs valid setup in `Raster Validations` dialog.",
                Qgis.Critical,
            )
            self.deactivate()
            return

    def clean(self) -> None:
        super().clean()
        if self._widget:
            self._widget.setAddLoSEnabled(False)
        self._start_point = None
        self._last_towards_point = None

    def canvasReleaseEvent(self, e: QgsMapMouseEvent) -> None:
        if e.button() == Qt.RightButton and self._start_point is None and self._los_rubber_band.size() == 0:
            self.deactivate()
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
                self.addLoSStatusChanged.emit(True)
                self._start_point = None

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        self._set_snap_point(event)

        if self._start_point is not None:
            self.draw_los(self._snap_point)

    def draw_los(self, towards_point: QgsPointXY):
        if towards_point is None:
            towards_point = self._last_towards_point

        if not self.canvas_crs_is_projected():
            return

        if self._start_point and towards_point:
            self._los_rubber_band.hide()

            rasters_extent = self._raster_list.extent_polygon()

            if self._widget.los_local or self._widget.los_global:
                if self._widget.los_local:
                    line = QgsGeometry.fromPolylineXY([self._start_point, towards_point])

                if self._widget.los_global:
                    line = QgsGeometry.fromPolylineXY([self._start_point, towards_point])

                    if self._start_point.distance(towards_point) > 0:
                        line = line.extendLine(
                            0,
                            self._raster_list.maximal_diagonal_size(),
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
                    maximal_length = self._raster_list.maximal_diagonal_size()
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

    def add_los_to_layer(self) -> None:
        los_geometry = self._los_rubber_band.asGeometry()

        self.addLoSStatusChanged.emit(False)

        if los_geometry.get().partCount() == 1:
            task = PrepareLoSTask(
                los_geometry,
                self._widget.sampling_distance.inUnits(self._los_layer.crs().mapUnits()),
                self._los_layer,
                self._raster_list,
                self._widget.observer_offset,
                self._widget.target_offset,
                self._widget.los_global,
                self._iface.mapCanvas().mapSettings().destinationCrs(),
            )

        else:
            task = PrepareLoSWithoutTargetTask(
                los_geometry,
                self._los_layer,
                self._raster_list,
                self._los_settings_dialog,
                self._widget.observer_offset,
                self._widget.angle_step,
                self._iface.mapCanvas().mapSettings().destinationCrs(),
            )

        task.taskCompleted.connect(self.task_finished)
        task.taskFinishedTime.connect(self.task_finished_message)

        self.task_manager.addTask(task)
        self.clean()

    def task_finished(self) -> None:
        self.featuresAdded.emit()
        if self.task_manager.all_los_tasks_finished():
            self.addLoSStatusChanged.emit(True)

    def task_finished_message(self, milliseconds: int) -> None:
        self._iface.messageBar().pushMessage(
            "LoS Added",
            f"LoS Processing Finished. Lasted {milliseconds / 1000} seconds.",
            Qgis.MessageLevel.Info,
            duration=2,
        )
