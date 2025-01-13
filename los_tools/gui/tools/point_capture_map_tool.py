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
            point = self.toMapCoordinates(event.pos())
            self.canvasClicked.emit(point, event.button())

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        result = self.canvas().snappingUtils().snapToMap(event.mapPoint())
        self._snap_indicator = QgsSnapIndicator(self.canvas())

        if result.isValid() and result.type() == QgsPointLocator.Vertex:
            self._current_point = result.point()
            self._snapped = True
            self._snap_layer_name = result.layer().name()
            self._snap_indicator.setMatch(result)

        else:
            self._current_point = event.mapPoint()
            self._snapped = False
            self._snap_layer_name = ""

    def get_point(self) -> QgsPointXY:
        return self._current_point

    def is_point_snapped(self) -> bool:
        return self._snapped

    def snap_layer(self) -> str:
        return self._snap_layer_name
