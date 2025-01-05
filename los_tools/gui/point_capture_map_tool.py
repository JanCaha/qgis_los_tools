from qgis.core import QgsPointLocator, QgsPointXY, QgsSettings
from qgis.gui import QgsMapCanvas, QgsMapMouseEvent, QgsMapToolEmitPoint, QgsVertexMarker
from qgis.PyQt.QtCore import QPoint, Qt
from qgis.PyQt.QtGui import QColor


class PointCaptureMapTool(QgsMapToolEmitPoint):

    _current_point: QgsPointXY = None
    _snapped: bool = False
    _snap_layer_name: str = ""

    def __init__(self, canvas: QgsMapCanvas):
        QgsMapToolEmitPoint.__init__(self, canvas)

        self.cursor = Qt.CursorShape.CrossCursor

        self.snapper = self.canvas().snappingUtils()

        settings = QgsSettings()
        self.snap_color = settings.value("/qgis/digitizing/snap_color", QColor("#ff00ff"))

        self.snap_marker = QgsVertexMarker(self.canvas())

        self._previous_settings()

    def _previous_settings(self):
        self._prev_cursor = self.canvas().cursor()
        self._prev_map_tool = self.canvas().mapTool()

    def deactivate(self):
        self.canvas().scene().removeItem(self.snap_marker)
        self.canvas().setCursor(self._prev_cursor)
        self.canvas().setMapTool(self._prev_map_tool)
        QgsMapToolEmitPoint.deactivate(self)

    def activate(self):
        self.snapper = self.canvas().snappingUtils()
        self._previous_settings()
        self.canvas().setCursor(self.cursor)

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        x = event.pos().x()
        y = event.pos().y()
        point = QPoint(x, y)

        result = self.snapper.snapToMap(point)

        if result.type() == QgsPointLocator.Vertex:
            self._current_point = result.point()
            self._snapped = True
            self._snap_layer_name = result.layer().name()

            self.update_snap_marker(result.point())

        else:
            self.update_snap_marker()

            self._current_point = self.toMapCoordinates(point)
            self._snapped = False
            self._snap_layer_name = ""

    def get_point(self) -> QgsPointXY:
        return self._current_point

    def is_point_snapped(self) -> bool:
        return self._snapped

    def snap_layer(self) -> str:
        return self._snap_layer_name

    def update_snap_marker(self, snapped_point: QgsPointXY = None):
        self.canvas().scene().removeItem(self.snap_marker)

        if snapped_point:
            self.create_vertex_marker(snapped_point)

    def create_vertex_marker(self, snapped_point: QgsPointXY):
        self.snap_marker = QgsVertexMarker(self.canvas())

        self.snap_marker.setCenter(snapped_point)
        self.snap_marker.setIconSize(16)
        self.snap_marker.setIconType(QgsVertexMarker.ICON_BOX)
        self.snap_marker.setPenWidth(3)
        self.snap_marker.setColor(self.snap_color)
