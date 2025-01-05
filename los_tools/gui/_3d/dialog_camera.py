from functools import partial

from qgis.core import (
    QgsAbstractTerrainProvider,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsPointXY,
    QgsProject,
)
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QLabel, QLineEdit, QPushButton, QWidget

from los_tools.constants.enums import PointType
from los_tools.gui.point_capture_map_tool import PointCaptureMapTool


class DialogCameraSetting(QDialog):

    crs_terrain: QgsCoordinateReferenceSystem
    point_observer: QgsPointXY = QgsPointXY()
    point_target: QgsPointXY = QgsPointXY()
    elevation_provider = QgsAbstractTerrainProvider

    observer_coordinate: QLineEdit = None
    target_coordinate: QLineEdit = None
    button_box: QDialogButtonBox = None
    terrain_type: QLabel = None

    valuesChanged = pyqtSignal()

    def __init__(self, iface: QgisInterface = None, parent: QWidget = None) -> None:
        if parent is None:
            parent = iface.mainWindow()
        super().__init__(parent)

        self._iface = iface

        self.prev_map_tool = self._iface.mapCanvas().mapTool()
        self.prev_cursor = self._iface.mapCanvas().cursor()

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

        self.terrain_type = QLabel()

    def sync_to_project(self):
        self.elevation_provider = QgsProject.instance().elevationProperties().terrainProvider()

        self.terrain_crs = self.elevation_provider.crs()

        elevation_description = ""

        if self.elevation_provider.type() == "flat":
            elevation_description = f"Flat terrain ({self.elevation_provider.offset()})"
        elif self.elevation_provider.type() == "raster":
            elevation_description = f"Raster layer ({self.elevation_provider.layer().name()})"
        elif self.elevation_provider.type() == "mesh":
            elevation_description = f"Mesh terrain ({self.elevation_provider.layer().name()})"

        self.terrain_type.setText(elevation_description)

    def update_point(self, point: QgsPointXY, point_type: PointType):
        point = self.mapTool.get_point()

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

        self.mapTool = PointCaptureMapTool(self._iface.mapCanvas())

        self.mapTool.canvasClicked.connect(partial(self.update_point, point_type=point_type))

        self.mapTool.complete.connect(self.close_point_selection_tool)

        self._iface.mapCanvas().setMapTool(self.mapTool)

    def convert_point_from_canvas_crs_to_elevation_provider_crs(self, point: QgsPointXY) -> QgsPointXY:

        transform = QgsCoordinateTransform(
            self._iface.mapCanvas().mapSettings().destinationCrs(), self.terrain_crs, QgsProject.instance()
        )

        return transform.transform(point)

    def close_point_selection_tool(self) -> None:
        self.show()
        self.restore_canvas_tools()

    def restore_canvas_tools(self) -> None:
        self._iface.mapCanvas().setMapTool(self.prev_map_tool)
        self._iface.mapCanvas().setCursor(self.prev_cursor)

    def set_acceptable(self) -> None:
        if self.point_observer.isEmpty():
            return
        if self.point_target.isEmpty():
            return

        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)

    def reject(self) -> None:
        self.restore_canvas_tools()
        super().reject()
