import typing

import numpy as np
from qgis.core import Qgis, QgsGeometry, QgsPointXY, QgsTask, QgsVectorLayer
from qgis.gui import QgisInterface, QgsMapMouseEvent
from qgis.PyQt.QtCore import Qt

from los_tools.classes.list_raster import ListOfRasters
from los_tools.classes.sampling_distance_matrix import SamplingDistanceMatrix
from los_tools.gui.los_tasks import PrepareLoSWithoutTargetTask
from los_tools.gui.los_without_target_visualization.los_without_target_widget import (
    LoSNoTargetDefinitionType,
    LoSNoTargetInputWidget,
)
from los_tools.gui.tools.los_digitizing_tool_with_widget import LoSDigitizingToolWithWidget
from los_tools.processing.tools.util_functions import get_max_decimal_numbers, round_all_values


class LosNoTargetMapTool(LoSDigitizingToolWithWidget):

    def __init__(
        self,
        iface: QgisInterface,
        raster_list: ListOfRasters,
        sampling_distance_matrix: SamplingDistanceMatrix,
        los_layer: QgsVectorLayer = None,
    ) -> None:
        super().__init__(iface, raster_list, los_layer)

        self._sampling_distance_matrix = sampling_distance_matrix

        self.create_widget()

        self._distance_limits_rubber_band = self.createRubberBand(Qgis.GeometryType.Line)
        self._distance_limits_rubber_band.setColor(Qt.GlobalColor.darkGreen)

    def create_widget(self):
        self._widget = LoSNoTargetInputWidget()
        self._widget.valuesChanged.connect(self.draw)
        super().create_widget()

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        super().canvasMoveEvent(event)

        if self._widget.los_type_definition == LoSNoTargetDefinitionType.DIRECTION_ANGLE_WIDTH:
            if self._start_point:
                if self._snap_point:
                    self._direction_point = self._snap_point
                else:
                    self._direction_point = event.mapPoint()
                self._los_rubber_band.reset()
                self._distance_limits_rubber_band.reset()
                self.draw()

    def canvasReleaseEvent(self, e: typing.Optional[QgsMapMouseEvent]) -> None:
        if e.button() == Qt.MouseButton.RightButton and self._los_rubber_band.size() == 0:
            self.deactivate()
        if e.button() == Qt.MouseButton.RightButton:
            self.clean()
            self.addLoSStatusChanged.emit(False)
        if e.button() == Qt.MouseButton.LeftButton:
            if self._widget.los_type_definition == LoSNoTargetDefinitionType.AZIMUTHS:
                if self._snap_point:
                    self._start_point = self._snap_point
                else:
                    self._start_point = e.mapPoint()
                self.draw()
                self.addLoSStatusChanged.emit(True)
            else:
                if self._start_point is None or (self._start_point and self._end_point):
                    self._end_point = None
                    if self._snap_point:
                        self._start_point = self._snap_point
                    else:
                        self._start_point = e.mapPoint()
                elif self._start_point and self._end_point is None:
                    if self._snap_point:
                        self._end_point = self._snap_point
                    else:
                        self._end_point = e.mapPoint()
                    self.draw()
                    self.addLoSStatusChanged.emit(True)

    def draw(self) -> None:
        if not self.canvas_crs_is_projected():
            return

        self.draw_los()

        if self._widget.show_distance_limits:
            self.draw_limits()
        else:
            self._distance_limits_rubber_band.reset()

    def clean(self) -> None:
        super().clean()
        self._distance_limits_rubber_band.reset()

    def draw_los(self):

        if self._widget.los_type_definition == LoSNoTargetDefinitionType.AZIMUTHS:

            if self._start_point:

                self._los_rubber_band.reset()

                angles = self.los_angles(self._widget.min_angle, self._widget.max_angle, self._widget.angle_step)

                size_constant = 1
                for angle in angles:
                    new_point = self._start_point.project(size_constant, angle)
                    geom = QgsGeometry.fromPolylineXY([self._start_point, new_point])
                    geom = geom.extendLine(0, self._raster_list.maximal_diagonal_size() - size_constant)
                    geom = geom.intersection(self._raster_list.extent_polygon())
                    self._los_rubber_band.addGeometry(geom, self.canvas().mapSettings().destinationCrs())
                self._los_rubber_band.show()

        else:
            if self._start_point and self.end_point():

                self._los_rubber_band.reset()

                maximal_length = self._raster_list.maximal_diagonal_size()

                angle = self._start_point.azimuth(self.end_point())

                angles = self.los_angles(
                    angle - (self._widget.angle_width / 2),
                    angle + (self._widget.angle_width / 2),
                    self._widget.angle_step,
                )

                size_constant = 1
                for angle in angles:
                    new_point = self._start_point.project(size_constant, angle)
                    line = QgsGeometry.fromPolylineXY([self._start_point, new_point])
                    line = line.extendLine(0, maximal_length - size_constant)
                    line = line.intersection(self._raster_list.extent_polygon())
                    self._los_rubber_band.addGeometry(line, self.canvas().mapSettings().destinationCrs())
                self._los_rubber_band.show()

    def draw_limits(self) -> None:

        angles: typing.List[float] = []
        point: QgsPointXY = None

        if self._widget.los_type_definition == LoSNoTargetDefinitionType.AZIMUTHS:
            if not self._start_point:
                return
            point = self._start_point
            angles = self.los_angles(self._widget.min_angle, self._widget.max_angle, self._widget.angle_step)
            if self._widget.max_angle > 359:
                angles.append(angles[0])
        else:
            if not self._start_point or not self.end_point():
                return

            point = self._start_point
            angle = self._start_point.azimuth(self.end_point())

            angles = self.los_angles(
                angle - (self._widget.angle_width / 2),
                angle + (self._widget.angle_width / 2),
                self._widget.angle_step,
            )

        self._distance_limits_rubber_band.reset()

        for dist in self._widget.distance_limits:
            line = []
            for angle in angles:
                new_point = point.project(dist, angle)
                line.append(new_point)

            geom = QgsGeometry.fromPolylineXY(line)
            self._distance_limits_rubber_band.addGeometry(geom, self.canvas().mapSettings().destinationCrs())

        self._distance_limits_rubber_band.show()

    @staticmethod
    def los_angles(min_angle: float, max_angle: float, angle_step: float) -> typing.List[float]:
        angles = np.arange(
            min_angle,
            max_angle + 0.000000001 * angle_step,
            step=angle_step,
        ).tolist()
        round_digits = get_max_decimal_numbers(
            [
                min_angle,
                max_angle,
                angle_step,
            ]
        )
        angles = round_all_values(angles, round_digits)
        return angles

    def prepare_task(self) -> QgsTask:
        task = PrepareLoSWithoutTargetTask(
            self._los_rubber_band.asGeometry(),
            self._los_layer,
            self._raster_list,
            self._sampling_distance_matrix,
            self._widget.observer_offset,
            self._widget.angle_step,
            self._iface.mapCanvas().mapSettings().destinationCrs(),
        )
        return task

    def end_point(self) -> QgsPointXY:
        if self._end_point:
            end_point = self._end_point
        elif self._direction_point:
            end_point = self._direction_point
        else:
            end_point = None

        return end_point
