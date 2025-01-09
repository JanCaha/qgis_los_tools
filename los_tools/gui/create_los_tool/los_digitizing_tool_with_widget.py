from qgis.core import Qgis, QgsPointLocator, QgsPointXY, QgsVectorLayer
from qgis.gui import QgisInterface, QgsMapMouseEvent, QgsMapToolEdit, QgsSnapIndicator
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QKeyEvent
from qgis.PyQt.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QProgressBar, QPushButton, QWidget

from los_tools.classes.list_raster import ListOfRasters
from los_tools.gui.create_los_tool.los_tasks import AbstractPrepareLoSTask, LoSExtractionTaskManager


class LoSDigitizingToolWidget(QWidget):
    valuesChanged = pyqtSignal()
    saveToLayerClicked = pyqtSignal()

    _add_los_to_layer: QPushButton
    _rasters: QLineEdit = None

    def clickedAddLosToLayer(self) -> None:
        self.saveToLayerClicked.emit()
        self.setAddLoSEnabled(False)

    def setAddLoSEnabled(self, enabled: bool) -> None:
        self._add_los_to_layer.setEnabled(enabled)

    def set_using_rasters(self, rasters: str) -> None:
        if self._rasters:
            self._rasters.setText(rasters)


class LoSDigitizingToolWithWidget(QgsMapToolEdit):

    _widget: LoSDigitizingToolWidget = None

    featuresAdded = pyqtSignal()
    addLoSStatusChanged = pyqtSignal(bool)

    def __init__(
        self,
        iface: QgisInterface,
        raster_list: ListOfRasters,
        los_layer: QgsVectorLayer = None,
    ) -> None:
        super().__init__(iface.mapCanvas())

        self._iface = iface
        self._canvas = self._iface.mapCanvas()

        self._snapper = self._canvas.snappingUtils()
        self.snap_marker = QgsSnapIndicator(self._canvas)

        self._los_rubber_band = self.createRubberBand(Qgis.GeometryType.Line)

        self.task_manager = LoSExtractionTaskManager()

        self._raster_list = raster_list
        self._los_layer = los_layer

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

        if not ListOfRasters.validate(self._raster_list.rasters):
            self.messageEmitted.emit(
                "Tool needs valid setup in `Raster Validations` dialog.",
                Qgis.Critical,
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

        self.addLoSStatusChanged.connect(self._widget.setAddLoSEnabled)

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

    def set_list_of_rasters(self, raster_list: ListOfRasters) -> None:
        self._raster_list = raster_list

    def prepare_task(self) -> AbstractPrepareLoSTask:
        return AbstractPrepareLoSTask()

    def _push_message_bar_widget(self) -> None:
        self.widget = QWidget()
        layout = QHBoxLayout()
        self.progress_bar = QProgressBar(self.widget)
        self.progress_bar.setRange(0, 0)
        self.label = QLabel("Saving LoS to layer ...")
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        layout.addStretch(1)
        self.widget.setLayout(layout)
        self._iface.messageBar().pushWidget(self.widget)

    def add_los_to_layer(self) -> None:

        self.addLoSStatusChanged.emit(False)

        task = self.prepare_task()

        task.taskCompleted.connect(self.task_finished)
        task.taskFinishedTime.connect(self.task_finished_message)

        self._push_message_bar_widget()
        self.task_manager.addTask(task)
        self.clean()

    def task_finished(self) -> None:
        self.featuresAdded.emit()

    def task_finished_message(self, milliseconds: int) -> None:
        self._iface.messageBar().popWidget()
        self._iface.messageBar().pushMessage(
            "LoS Added",
            f"LoS Processing Finished. Lasted {milliseconds / 1000} seconds.",
            Qgis.MessageLevel.Info,
            duration=2,
        )

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        self._set_snap_point(event)

    def reactivate(self):
        if self._widget:
            self._widget.set_using_rasters(self._raster_list.raster_to_use())
        return super().reactivate()
