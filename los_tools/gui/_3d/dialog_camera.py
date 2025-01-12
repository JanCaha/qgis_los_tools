from functools import partial

from qgis.core import QgsPointXY
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QLabel, QLineEdit, QPushButton, QWidget

from los_tools.classes.list_raster import ListOfRasters
from los_tools.constants.enums import PointType
from los_tools.gui.tools.point_capture_map_tool import PointCaptureMapTool


class DialogCameraSetting(QDialog):

    point_observer: QgsPointXY = QgsPointXY()
    point_target: QgsPointXY = QgsPointXY()

    observer_coordinate: QLineEdit = None
    target_coordinate: QLineEdit = None
    button_box: QDialogButtonBox = None
    raster_names: QLabel = None

    map_tool: PointCaptureMapTool = None

    valuesChanged = pyqtSignal()

    def __init__(self, list_of_rasters: ListOfRasters, iface: QgisInterface = None, parent: QWidget = None) -> None:
        if parent is None:
            parent = iface.mainWindow()
        super().__init__(parent)

        self._iface = iface

        self._list_of_rasters = list_of_rasters

        self.snapper = self._iface.mapCanvas().snappingUtils()

        self.init_gui()
        self.sync_to_project()

    def init_gui(self):
        self.observer_btn = QPushButton()
        self.observer_btn.setText("Choose observer point on the map")
        self.observer_btn.clicked.connect(partial(self.select_point, PointType.OBSERVER))

        self.observer_coordinate = QLineEdit()
        self.observer_coordinate.setEnabled(False)

        self.target_btn = QPushButton()
        self.target_btn.setText("Choose target point on the map")
        self.target_btn.clicked.connect(partial(self.select_point, PointType.TARGET))

        self.target_coordinate = QLineEdit()
        self.target_coordinate.setEnabled(False)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok, self)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.observer_offset = QDoubleSpinBox()
        self.observer_offset.setDecimals(2)
        self.observer_offset.setMinimum(0)
        self.observer_offset.setValue(1.6)

        self.raster_names = QLineEdit()
        self.raster_names.setReadOnly(True)

    def sync_to_project(self):
        self.rasters_crs = self._list_of_rasters.crs()

        self.raster_names.setText(self._list_of_rasters.raster_to_use())

    def update_point(self, point: QgsPointXY, point_type: PointType):
        point = self.map_tool.get_point()

        text_point = (
            f"{point.x():.3f};{point.y():.3f} [{self._iface.mapCanvas().mapSettings().destinationCrs().authid()}]"
        )

        if point_type == PointType.OBSERVER:
            self.point_observer = point
            self.observer_coordinate.setText(text_point)

        if point_type == PointType.TARGET:
            self.point_target = point
            self.target_coordinate.setText(text_point)

        self.valuesChanged.emit()

    def select_point(self, point_type: PointType) -> None:
        self.hide()

        self.map_tool = PointCaptureMapTool(self._iface.mapCanvas())

        self.map_tool.canvasClicked.connect(partial(self.update_point, point_type=point_type))
        self.map_tool.canvasClicked.connect(self.map_tool.deactivate)
        self.map_tool.deactivated.connect(self.show)

        self._iface.mapCanvas().setMapTool(self.map_tool)

    def set_acceptable(self) -> None:
        if self.point_observer.isEmpty():
            return
        if self.point_target.isEmpty():
            return

        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
