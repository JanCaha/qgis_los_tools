from qgis.core import Qgis, QgsPointLocator, QgsPointXY, QgsVectorLayer
from qgis.gui import QgisInterface, QgsMapMouseEvent, QgsMapToolEdit, QgsMessageBarItem, QgsSnapIndicator
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QKeyEvent
from qgis.PyQt.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QProgressBar, QPushButton, QWidget

from los_tools.classes.list_raster import ListOfRasters
from los_tools.gui.los_tasks import AbstractPrepareLoSTask, LoSExtractionTaskManager


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

    def load_settings(self) -> None:
        pass


class LoSDigitizingToolWithWidget(QgsMapToolEdit):

    _widget: LoSDigitizingToolWidget = None
    _progress_bar: QProgressBar = None

    featuresAdded = pyqtSignal()
    addLoSStatusChanged = pyqtSignal(bool)

    _message_bar_item: QgsMessageBarItem = None

    def __init__(
        self,
        iface: QgisInterface,
        raster_list: ListOfRasters,
        los_layer: QgsVectorLayer = None,
    ) -> None:
        super().__init__(iface.mapCanvas())

        self._iface = iface

        self._snap_indicator = QgsSnapIndicator(self.canvas())

        self._los_rubber_band = self.createRubberBand(Qgis.GeometryType.Line)

        self._task_manager = LoSExtractionTaskManager()

        self._raster_list = raster_list
        self._los_layer = los_layer

        self._snap_point: QgsPointXY = None
        self._start_point: QgsPointXY = None
        self._end_point: QgsPointXY = None
        self._direction_point: QgsPointXY = None

    def activate(self) -> None:

        self.create_widget()

        self.messageDiscarded.emit()

        if self.canvas().mapSettings().destinationCrs().isGeographic():
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
        self._widget.load_settings()
        self._widget.set_using_rasters(self._raster_list.raster_to_use())
        self._widget.saveToLayerClicked.connect(self.add_los_to_layer)

        self._iface.addUserInputWidget(self._widget)
        self._widget.setFocus(Qt.TabFocusReason)

        self.addLoSStatusChanged.connect(self._widget.setAddLoSEnabled)

    def delete_widget(self):
        if self._widget:
            self._widget.hide()
            self._widget.releaseKeyboard()
            self._widget.deleteLater()
            self._widget = None

    def clean(self) -> None:
        self._start_point = None
        self._end_point = None
        self._direction_point = None
        self._snap_indicator.setVisible(False)
        self._los_rubber_band.reset()

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key_Escape or e.key() == Qt.Key_Backspace:
            self.deactivate()
        return super().keyPressEvent(e)

    def _set_snap_point(self, event: QgsMapMouseEvent) -> None:
        result = self.canvas().snappingUtils().snapToMap(event.mapPoint())
        self._snap_indicator.setMatch(result)

        if result.isValid() and result.type() == QgsPointLocator.Vertex:
            self._snap_point = result.point()
        else:
            self._snap_point = None

    def canvas_crs_is_projected(self) -> bool:
        if self.canvas().mapSettings().destinationCrs().isGeographic():
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
        self._widget_message_bar_progress_bar = QWidget()
        layout = QHBoxLayout()
        self._progress_bar = QProgressBar(self._widget_message_bar_progress_bar)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setMinimumWidth(200)
        self._progess_bar_label = QLabel("Saving LoS to layer ...")
        layout.addWidget(self._progess_bar_label)
        layout.addWidget(self._progress_bar)
        layout.addStretch(1)
        self._widget_message_bar_progress_bar.setLayout(layout)
        self._message_bar_item = self._iface.messageBar().pushWidget(self._widget_message_bar_progress_bar)

    def add_los_to_layer(self) -> None:

        self.addLoSStatusChanged.emit(False)

        task = self.prepare_task()

        task.taskCompleted.connect(self.task_finished)
        task.taskFinishedTime.connect(self.task_finished_message)

        self._push_message_bar_widget()

        task.progressChanged.connect(self.set_progress)

        self._task_manager.addTask(task)
        self.clean()

    def task_finished(self) -> None:
        self.featuresAdded.emit()

    def task_finished_message(self, milliseconds: int) -> None:
        if self._message_bar_item:
            self._iface.messageBar().popWidget(self._message_bar_item)
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

    def set_progress(self, value: float) -> None:
        if self._progress_bar:
            self._progress_bar.setValue(int(value))
