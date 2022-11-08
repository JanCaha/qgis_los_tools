import numpy as np

from qgis.PyQt.QtCore import (Qt)
from qgis.PyQt.QtGui import (QKeyEvent)
from qgis.PyQt.QtWidgets import (QWidget)
from qgis.core import (QgsWkbTypes, QgsGeometry, QgsPointLocator, Qgis)
from qgis.gui import (QgisInterface, QgsMapToolAdvancedDigitizing, QgsMapMouseEvent,
                      QgsSnapIndicator)

from los_tools.processing.tools.util_functions import get_max_decimal_numbers, round_all_values
from .los_without_target_widget import LoSNoTargetInputWidget


class LosNoTargetMapTool(QgsMapToolAdvancedDigitizing):

    def __init__(self, iface: QgisInterface) -> None:
        super().__init__(iface.mapCanvas(), iface.cadDockWidget())
        self._iface = iface
        self._canvas = self._iface.mapCanvas()

        self._point = None

        self._snapper = self._canvas.snappingUtils()
        self.snap_marker = QgsSnapIndicator(self._canvas)

        self._los_rubber_band = self.createRubberBand(QgsWkbTypes.LineGeometry)

        self._widget: QWidget = None

    def create_widget(self):
        self.delete_widget()

        self._widget = LoSNoTargetInputWidget()
        self._iface.addUserInputWidget(self._widget)
        self._widget.setFocus(Qt.TabFocusReason)

        self._widget.valuesChanged.connect(self.draw_los)

    def delete_widget(self):
        if self._widget:
            self._widget.releaseKeyboard()
            self._widget.deleteLater()
            self._widget = None

    def activate(self) -> None:
        super(LosNoTargetMapTool, self).activate()
        self.create_widget()
        self.messageDiscarded.emit()
        self._canvas = self._iface.mapCanvas()
        self._snapper = self._canvas.snappingUtils()
        if self._canvas.mapSettings().destinationCrs().isGeographic():
            self.messageEmitted.emit(
                "Tool only works if canvas is in projected CRS. Currently canvas is in geographic CRS.",
                Qgis.Critical)
            self.deactivate()
            return
        self._widget.setUnit(self._canvas.mapSettings().destinationCrs().mapUnits())

    def clean(self) -> None:
        self.snap_marker.setVisible(False)
        self._los_rubber_band.hide()

    def deactivate(self) -> None:
        self.clean()
        self.delete_widget()
        self._iface.mapCanvas().unsetMapTool(self)
        super(LosNoTargetMapTool, self).deactivate()

    def canvasReleaseEvent(self, e: QgsMapMouseEvent) -> None:
        if e.button() == Qt.RightButton:
            self.deactivate()
        elif e.button() == Qt.LeftButton:
            if self._snap_point:
                self._point = self._snap_point
            else:
                self._point = e.mapPoint()
            self.draw_los()

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        result = self._snapper.snapToMap(event.pos())
        self.snap_marker.setMatch(result)
        if result.type() == QgsPointLocator.Vertex:
            self._snap_point = result.point()
        else:
            self._snap_point = None

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key_Escape:
            self.deactivate()
            self._iface.mapCanvas().unsetMapTool(self)
        return super().keyPressEvent(e)

    def draw_los(self):

        canvas_crs = self._canvas.mapSettings().destinationCrs()

        if canvas_crs.isGeographic():
            self._iface.messageBar().pushMessage(
                "LoS can be drawn only for projected CRS. Canvas is currently in geographic CRS.",
                Qgis.Critical,
                duration=5)
            return

        if self._point:
            self._los_rubber_band.hide()
            self._los_rubber_band.setToGeometry(QgsGeometry(),
                                                self._canvas.mapSettings().destinationCrs())
            angles = np.arange(self._widget.min_angle,
                               self._widget.max_angle + 0.000000001 * self._widget.angle_step,
                               step=self._widget.angle_step).tolist()
            round_digits = get_max_decimal_numbers(
                [self._widget.min_angle, self._widget.max_angle, self._widget.angle_step])
            angles = round_all_values(angles, round_digits)
            size_constant = 1
            for angle in angles:
                new_point = self._point.project(size_constant, angle)
                geom = QgsGeometry.fromPolylineXY([self._point, new_point])
                geom = geom.extendLine(0, self._widget.length - size_constant)
                self._los_rubber_band.addGeometry(geom,
                                                  self._canvas.mapSettings().destinationCrs())
            self._los_rubber_band.show()
