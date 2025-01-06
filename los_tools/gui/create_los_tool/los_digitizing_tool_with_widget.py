from qgis.core import Qgis, QgsPointLocator, QgsPointXY
from qgis.gui import QgisInterface, QgsMapMouseEvent, QgsMapToolEdit, QgsSnapIndicator
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QKeyEvent
from qgis.PyQt.QtWidgets import QWidget


class LoSDigitizingToolWithWidget(QgsMapToolEdit):

    _widget: QWidget

    def __init__(self, iface: QgisInterface) -> None:
        super().__init__(iface.mapCanvas())

        self._iface = iface
        self._canvas = self._iface.mapCanvas()

        self._snapper = self._canvas.snappingUtils()
        self.snap_marker = QgsSnapIndicator(self._canvas)

        self._los_rubber_band = self.createRubberBand(Qgis.GeometryType.Line)

        self._snap_point: QgsPointXY = None
        self._selected_point: QgsPointXY = None

    def activate(self) -> None:

        self.create_widget()

        self.messageDiscarded.emit()

        self._snapper = self._canvas.snappingUtils()

        if self._canvas.mapSettings().destinationCrs().isGeographic():
            self.messageEmitted.emit(
                "Tool only works if canvas is in projected CRS. Currently canvas is in geographic CRS.",
                Qgis.MessageLevel.Critical,
            )
            self.deactivate()
            return

        super().activate()

    def deactivate(self) -> None:
        self.clean()
        self.delete_widget()
        self._iface.mapCanvas().unsetMapTool(self)
        super().deactivate()

    def create_widget(self):
        self._iface.addUserInputWidget(self._widget)
        self._widget.setFocus(Qt.TabFocusReason)
        self._widget.show()

    def delete_widget(self):
        if self._widget:
            self._widget.hide()
            self._widget.releaseKeyboard()
            self._widget.deleteLater()
            self._widget = None

    def clean(self) -> None:
        self.snap_marker.setVisible(False)
        self._los_rubber_band.reset()

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key_Escape or e.key() == Qt.Key_Backspace:
            self.deactivate()
            self._iface.mapCanvas().unsetMapTool(self)
        return super().keyPressEvent(e)

    def _set_snap_point(self, event: QgsMapMouseEvent) -> None:
        result = self._snapper.snapToMap(event.mapPoint())
        self.snap_marker.setMatch(result)
        if result.type() == QgsPointLocator.Vertex:
            self._snap_point = result.point()
        else:
            self._snap_point = None

    def canvas_crs_is_projected(self) -> bool:
        if self._canvas.mapSettings().destinationCrs().isGeographic():
            self._iface.messageBar().pushMessage(
                "Can't Drawn LoS",
                "LoS can be drawn only for projected CRS. Canvas is currently in geographic CRS.",
                Qgis.Critical,
                duration=5,
            )
            return False
        return True
