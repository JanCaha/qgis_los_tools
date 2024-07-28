import math
from enum import Enum
from functools import partial
from typing import List

from qgis._3d import QgsLayoutItem3DMap
from qgis.core import (
    QgsMapLayerProxyModel,
    QgsMasterLayoutInterface,
    QgsPointLocator,
    QgsPointXY,
    QgsProject,
    QgsRasterLayer,
    QgsSettings,
    QgsVector3D,
    QgsWkbTypes,
)
from qgis.gui import (
    QgisInterface,
    QgsMapCanvas,
    QgsMapLayerComboBox,
    QgsMapMouseEvent,
    QgsMapToolEmitPoint,
    QgsRubberBand,
    QgsVertexMarker,
)
from qgis.PyQt.QtCore import QPoint, Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from los_tools.processing.tools.util_functions import bilinear_interpolated_value


class PointType(Enum):
    OBSERVER = 1
    TARGET = 2


class SetCameraTool(QDialog):
    observer: QgsPointXY = None
    target: QgsPointXY = None

    active_button: QToolButton

    layout: QgsMasterLayoutInterface = None
    layout_item_3d: QgsLayoutItem3DMap = None

    info_update = pyqtSignal()

    def __init__(self, parent, canvas: QgsMapCanvas, iface: QgisInterface):
        super().__init__()

        self.iface = iface

        self.canvas = canvas

        self.prev_map_tool = self.canvas.mapTool()
        self.prev_cursor = self.canvas.cursor()

        self.snapper = self.canvas.snappingUtils()

        self.layout_manager = QgsProject.instance().layoutManager()

        layouts = [x.name() for x in self.layout_manager.layouts()]

        self.item_cb = QComboBox()
        self.item_cb.currentIndexChanged.connect(self.set_item_3d)

        self.layout_cb = QComboBox()
        self.layout_cb.currentIndexChanged.connect(self.set_layout)
        self.layout_cb.addItems(layouts)

        self.observer_btn = QPushButton()
        self.observer_btn.setText("Choose observer point on the map")
        self.observer_btn.clicked.connect(partial(self.select_point, PointType.OBSERVER))

        self.dsm_cb = QgsMapLayerComboBox()
        self.dsm_cb.setFilters(QgsMapLayerProxyModel.RasterLayer)

        self.offset_sb = QDoubleSpinBox()
        self.offset_sb.setDecimals(2)
        self.offset_sb.setMinimum(0)
        self.offset_sb.setValue(1.6)

        self.observer_coordinate = QLineEdit()
        self.observer_coordinate.setEnabled(False)

        self.hlayout1 = QHBoxLayout()
        self.hlayout1.addWidget(self.observer_btn)
        self.hlayout1.addWidget(self.observer_coordinate)

        self.target_btn = QPushButton()
        self.target_btn.setText("Choose target point on the map")
        self.target_btn.clicked.connect(partial(self.select_point, PointType.TARGET))

        self.target_coordinate = QLineEdit()
        self.target_coordinate.setEnabled(False)

        self.hlayout2 = QHBoxLayout()
        self.hlayout2.addWidget(self.target_btn)
        self.hlayout2.addWidget(self.target_coordinate)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok, self)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(
            QLabel("Layout and layout item (3D Map) along with both observer and target point need to be selected.")
        )
        self.vlayout.addWidget(QLabel("Select layout with 3D Map"))
        self.vlayout.addWidget(self.layout_cb)
        self.vlayout.addWidget(QLabel("Select layout item 3D Map to set the camera for"))
        self.vlayout.addWidget(self.item_cb)
        self.vlayout.addWidget(QLabel("Select raster with elevations to use"))
        self.vlayout.addWidget(self.dsm_cb)
        self.vlayout.addWidget(QLabel("Observer offset above raster"))
        self.vlayout.addWidget(self.offset_sb)
        self.vlayout.addLayout(self.hlayout1)
        self.vlayout.addLayout(self.hlayout2)
        self.vlayout.addWidget(self.button_box)

        self.setLayout(self.vlayout)

        self.info_update.connect(self.update_ok_button)

    def update_ok_button(self) -> None:
        if self.is_complete():
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)

    def is_complete(self) -> bool:
        if self.observer and self.target and self.layout and self.layout_item_3d and self.dsm_cb.currentLayer():
            return True

        return False

    def set_layout(self) -> None:
        self.layout = self.layout_manager.layoutByName(self.layout_cb.currentText())

        items_3d = [x.displayName() for x in self.get_item_names_of_type_from_layout()]

        self.item_cb.addItems(items_3d)

        self.info_update.emit()

    def set_item_3d(self) -> None:
        items_3d = self.get_item_names_of_type_from_layout()

        for item in items_3d:
            if item.displayName() == self.item_cb.currentText():
                self.layout_item_3d = item
                break

        self.info_update.emit()

    def get_item_names_of_type_from_layout(self) -> List[QgsLayoutItem3DMap]:
        items = [x for x in self.layout.items() if isinstance(x, QgsLayoutItem3DMap)]

        return items

    def accept(self) -> None:
        self.update_camera_position()
        super().accept()

    def reject(self) -> None:
        self.restore_canvas_tools()
        super().reject()

    def select_point(self, point_type: PointType) -> None:
        self.hide()

        self.mapTool = PointCaptureMapTool(self.canvas)

        self.mapTool.canvasClicked.connect(partial(self.update_point, point_type=point_type))

        self.mapTool.complete.connect(self.restore_canvas_tools)

        self.canvas.setMapTool(self.mapTool)

    def update_point(self, point, point_type: PointType):

        canvas_crs = self.canvas.mapSettings().destinationCrs()

        point = self.mapTool.get_point()

        if self.mapTool.is_point_snapped():
            msg = "Snapped to point at {} {} from layer {}.".format(point.x(), point.y(), self.mapTool.snap_layer())
        else:
            msg = "Point at {} {} selected.".format(point.x(), point.y())

        self.iface.messageBar().pushMessage("Point defined", msg, duration=5)

        text_point = "{:.3f};{:.3f}[{}]".format(point.x(), point.y(), canvas_crs.authid())

        if point_type == PointType.OBSERVER:
            self.observer = point
            self.observer_coordinate.setText(text_point)

        if point_type == PointType.TARGET:
            self.target = point
            self.target_coordinate.setText(text_point)

        self.info_update.emit()

    def restore_canvas_tools(self) -> None:
        self.show()
        self.canvas.setMapTool(self.prev_map_tool)
        self.canvas.setCursor(self.prev_cursor)

    def update_camera_position(self) -> None:
        settings = self.layout_item_3d.mapSettings()
        camera_pose = self.layout_item_3d.cameraPose()

        current_layer: QgsRasterLayer = self.dsm_cb.currentLayer()

        observer_z = bilinear_interpolated_value(current_layer.dataProvider(), self.observer) + self.offset_sb.value()

        target_z = bilinear_interpolated_value(current_layer.dataProvider(), self.target)

        look_at_point = settings.mapToWorldCoordinates(QgsVector3D(self.target.x(), self.target.y(), target_z))
        look_from_point = settings.mapToWorldCoordinates(QgsVector3D(self.observer.x(), self.observer.y(), observer_z))

        start_point = QgsPointXY(look_at_point.x(), look_at_point.z())
        end_point = QgsPointXY(look_from_point.x(), look_from_point.z())

        angle = start_point.azimuth(end_point)

        distance = look_at_point.distance(look_from_point)

        vert_angle = math.degrees(math.atan((look_from_point.y() - look_at_point.y()) / distance))

        vert_angle = 90 - (vert_angle)

        camera_pose.setCenterPoint(look_at_point)
        camera_pose.setHeadingAngle(angle)
        camera_pose.setDistanceFromCenterPoint(distance)
        camera_pose.setPitchAngle(vert_angle)

        self.layout_item_3d.setCameraPose(camera_pose)
        self.layout_item_3d.refresh()

        msg = "Layout item `{}` in layout `{}` camera settings updated.".format(
            self.layout_item_3d.displayName(), self.layout.name()
        )

        self.iface.messageBar().pushMessage("Layout item updated", msg, duration=5)


class PointCaptureMapTool(QgsMapToolEmitPoint):
    complete = pyqtSignal()

    _current_point: QgsPointXY = None
    _snapped: bool = False
    _snap_layer_name: str = ""
    _canvas: QgsMapCanvas

    def __init__(self, canvas: QgsMapCanvas):
        QgsMapToolEmitPoint.__init__(self, canvas)

        self._canvas = canvas
        self.cursor = Qt.CrossCursor

        self.snapper = self._canvas.snappingUtils()

        self.rubber = QgsRubberBand(self._canvas, QgsWkbTypes.PointGeometry)

        settings = QgsSettings()
        self.snap_color = settings.value("/qgis/digitizing/snap_color", QColor("#ff00ff"))

        self.snap_marker = QgsVertexMarker(self._canvas)

    def deactivate(self):
        self.update_snap_marker()
        QgsMapToolEmitPoint.deactivate(self)

    def activate(self):
        self._canvas.setCursor(self.cursor)

    def canvasReleaseEvent(self, event):
        self.complete.emit()

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
        self._canvas.scene().removeItem(self.snap_marker)

        if snapped_point is None:
            return

        self.create_vertex_marker(snapped_point)

    def create_vertex_marker(self, snapped_point: QgsPointXY):
        self.snap_marker = QgsVertexMarker(self._canvas)

        self.snap_marker.setCenter(snapped_point)
        self.snap_marker.setIconSize(16)
        self.snap_marker.setIconType(QgsVertexMarker.ICON_BOX)
        self.snap_marker.setPenWidth(3)
        self.snap_marker.setColor(self.snap_color)
