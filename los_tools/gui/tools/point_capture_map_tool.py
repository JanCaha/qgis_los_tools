from qgis.core import QgsPointLocator, QgsPointXY
from qgis.gui import QgsMapCanvas, QgsMapMouseEvent, QgsMapToolEmitPoint, QgsSnapIndicator
from qgis.PyQt.QtCore import Qt


class PointCaptureMapTool(QgsMapToolEmitPoint):

    _current_point: QgsPointXY = None
    _snapped: bool = False
    _snap_layer_name: str = ""

    def __init__(self, canvas: QgsMapCanvas):
        QgsMapToolEmitPoint.__init__(self, canvas)

        self.setCursor(Qt.CrossCursor)

        self._snap_indicator = QgsSnapIndicator(self.canvas())

    def deactivate(self):
        self._snap_indicator.setVisible(False)
        self.canvas().unsetMapTool(self)
        QgsMapToolEmitPoint.deactivate(self)

    def canvasPressEvent(self, event: QgsMapMouseEvent) -> None:
        pass

    def canvasReleaseEvent(self, event: QgsMapMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self.deactivate()
        else:
            self.canvasClicked.emit(self._current_point, event.button())

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        match = self.canvas().snappingUtils().snapToMap(event.originalMapPoint())

        if match.isValid() and match.type() == QgsPointLocator.Vertex:
            self._snap_indicator.setMatch(match)
            self._snap_indicator.setVisible(True)
            self._current_point = match.point()
            self._snapped = True
            self._snap_layer_name = match.layer().name()
        else:
            self._snap_indicator.setVisible(False)
            self._current_point = event.originalMapPoint()
            self._snapped = False
            self._snap_layer_name = ""

    def get_point(self) -> QgsPointXY:
        return self._current_point

    def is_point_snapped(self) -> bool:
        return self._snapped

    def snap_layer(self) -> str:
        return self._snap_layer_name
