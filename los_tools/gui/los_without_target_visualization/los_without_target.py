import numpy as np
from qgis.core import Qgis, QgsGeometry
from qgis.gui import QgisInterface, QgsMapMouseEvent
from qgis.PyQt.QtCore import Qt

from los_tools.gui.create_los_tool.los_digitizing_tool_with_widget import LoSDigitizingToolWithWidget
from los_tools.gui.los_without_target_visualization.los_without_target_widget import LoSNoTargetInputWidget
from los_tools.processing.tools.util_functions import get_max_decimal_numbers, round_all_values


class LosNoTargetMapTool(LoSDigitizingToolWithWidget):

    def __init__(self, iface: QgisInterface) -> None:
        super().__init__(iface)

        self._widget = LoSNoTargetInputWidget()
        self._widget.load_settings()
        self._widget.hide()

        self._distance_limits_rubber_band = self.createRubberBand(Qgis.GeometryType.Line)
        self._distance_limits_rubber_band.setColor(Qt.GlobalColor.darkGreen)

    def create_widget(self):
        if not self._widget:
            self._widget = LoSNoTargetInputWidget()
            self._widget.load_settings()
        super().create_widget()

        self._widget.valuesChanged.connect(self.draw)

    def canvasMoveEvent(self, e: QgsMapMouseEvent) -> None:
        self._set_snap_point(e)
        return super().canvasMoveEvent(e)

    def canvasReleaseEvent(self, e: QgsMapMouseEvent) -> None:
        if e.button() == Qt.RightButton and self._los_rubber_band.size() == 0:
            self.deactivate()
        if e.button() == Qt.RightButton:
            self.clean()
        if e.button() == Qt.LeftButton:
            self._selected_point = e.mapPoint()
            self.draw()

    def draw(self) -> None:
        self.draw_los()
        if self._widget.show_distance_limits:
            self.draw_limits()
        else:
            self._distance_limits_rubber_band.reset()

    def clean(self) -> None:
        super().clean()
        self._distance_limits_rubber_band.reset()

    def draw_los(self):

        if self._snap_point:
            self._selected_point = self._snap_point

        if not self.canvas_crs_is_projected():
            return

        if self._selected_point:
            self._los_rubber_band.reset()
            angles = np.arange(
                self._widget.min_angle,
                self._widget.max_angle + 0.000000001 * self._widget.angle_step,
                step=self._widget.angle_step,
            ).tolist()
            round_digits = get_max_decimal_numbers(
                [
                    self._widget.min_angle,
                    self._widget.max_angle,
                    self._widget.angle_step,
                ]
            )
            angles = round_all_values(angles, round_digits)
            size_constant = 1
            for angle in angles:
                new_point = self._selected_point.project(size_constant, angle)
                geom = QgsGeometry.fromPolylineXY([self._selected_point, new_point])
                geom = geom.extendLine(0, self._widget.length - size_constant)
                self._los_rubber_band.addGeometry(geom, self._canvas.mapSettings().destinationCrs())
            self._los_rubber_band.show()

    def draw_limits(self) -> None:

        if self._snap_point:
            self._selected_point = self._snap_point

        if not self.canvas_crs_is_projected():
            return

        if self._selected_point:

            self._distance_limits_rubber_band.reset()

            angles = np.arange(
                self._widget.min_angle,
                self._widget.max_angle + 0.000000001 * self._widget.angle_step,
                step=self._widget.angle_step,
            ).tolist()

            if self._widget.max_angle > 359:
                angles.append(angles[0])

            round_digits = get_max_decimal_numbers(
                [
                    self._widget.min_angle,
                    self._widget.max_angle,
                    self._widget.angle_step,
                ]
            )
            angles = round_all_values(angles, round_digits)

            for dist in self._widget.distance_limits:
                line = []
                for angle in angles:
                    new_point = self._selected_point.project(dist, angle)
                    line.append(new_point)

                geom = QgsGeometry.fromPolylineXY(line)
                self._distance_limits_rubber_band.addGeometry(geom, self._canvas.mapSettings().destinationCrs())

            self._distance_limits_rubber_band.show()
