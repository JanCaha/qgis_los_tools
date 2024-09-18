import numpy as np
from qgis.core import QgsGeometry
from qgis.gui import QgisInterface, QgsMapMouseEvent
from qgis.PyQt.QtCore import Qt

from los_tools.gui.create_los_tool.los_digitizing_tool_with_widget import LoSDigitizingToolWithWidget
from los_tools.gui.los_without_target_visualization.los_without_target_widget import LoSNoTargetInputWidget
from los_tools.processing.tools.util_functions import get_max_decimal_numbers, round_all_values


class LosNoTargetMapTool(LoSDigitizingToolWithWidget):

    def __init__(self, iface: QgisInterface) -> None:
        super().__init__(iface)

        self._widget = LoSNoTargetInputWidget()
        self._widget.hide()

    def create_widget(self):
        if not self._widget:
            self._widget = LoSNoTargetInputWidget()
        super().create_widget()

        self._widget.valuesChanged.connect(self.draw_los)

    def canvasReleaseEvent(self, e: QgsMapMouseEvent) -> None:
        if e.button() == Qt.LeftButton:
            self.draw_los()

    def draw_los(self):

        if not self.canvas_crs_is_projected():
            return

        if self._snap_point:
            self._los_rubber_band.hide()
            self._los_rubber_band.setToGeometry(QgsGeometry(), self._canvas.mapSettings().destinationCrs())
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
                new_point = self._snap_point.project(size_constant, angle)
                geom = QgsGeometry.fromPolylineXY([self._snap_point, new_point])
                geom = geom.extendLine(0, self._widget.length - size_constant)
                self._los_rubber_band.addGeometry(geom, self._canvas.mapSettings().destinationCrs())
            self._los_rubber_band.show()
