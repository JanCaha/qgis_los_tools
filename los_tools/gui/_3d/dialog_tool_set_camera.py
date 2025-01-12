from typing import List

from qgis._3d import QgsLayoutItem3DMap
from qgis.core import QgsMasterLayoutInterface, QgsProject
from qgis.PyQt.QtWidgets import QComboBox, QGridLayout, QLabel

from los_tools.constants.enums import PointType
from los_tools.gui._3d.dialog_camera import DialogCameraSetting
from los_tools.gui._3d.utils import set_camera_to_position_and_look


class SetCameraDialog(DialogCameraSetting):

    layout: QgsMasterLayoutInterface = None
    layout_item_3d: QgsLayoutItem3DMap = None

    def init_gui(self):
        super().init_gui()

        self.setMinimumWidth(600)
        self.setWindowTitle("Set layout item Camera Position")

        layout = QGridLayout(self)
        self.setLayout(layout)

        self.item_cb = QComboBox()
        self.item_cb.currentIndexChanged.connect(self.set_item_3d)

        self.layout_cb = QComboBox()
        self.layout_cb.currentIndexChanged.connect(self.set_layout)

        layout.addWidget(QLabel("Select layout with 3D Map"), 0, 0)
        layout.addWidget(self.layout_cb, 0, 1)
        layout.addWidget(QLabel("Select layout item 3D Map to set the camera for"), 1, 0)
        layout.addWidget(self.item_cb, 1, 1)
        layout.addWidget(QLabel("Rasters"), 2, 0)
        layout.addWidget(self.raster_names, 2, 1)
        layout.addWidget(self.observer_btn, 3, 0)
        layout.addWidget(self.observer_coordinate, 3, 1)
        layout.addWidget(QLabel("Observer Offset"), 4, 0)
        layout.addWidget(self.observer_offset, 4, 1)

        layout.addWidget(self.target_btn, 5, 0)
        layout.addWidget(self.target_coordinate, 5, 1)

        layout.addWidget(self.button_box, 6, 0, 1, 2)

        self.valuesChanged.connect(self.check_valid)

    def sync_to_project(self):
        super().sync_to_project()

        layout_manager = QgsProject.instance().layoutManager()

        layouts = [x.name() for x in layout_manager.layouts()]

        self.layout_cb.addItems(layouts)

    def check_valid(self) -> None:
        if not self.layout:
            return
        if not self.layout_item_3d:
            return
        super().set_acceptable()

    def set_layout(self) -> None:
        self.layout = QgsProject.instance().layoutManager().layoutByName(self.layout_cb.currentText())

        items_3d = [x.displayName() for x in self.get_item_names_of_type_from_layout()]

        self.item_cb.addItems(items_3d)

        self.valuesChanged.emit()

    def set_item_3d(self) -> None:
        items_3d = self.get_item_names_of_type_from_layout()

        for item in items_3d:
            if item.displayName() == self.item_cb.currentText():
                self.layout_item_3d = item
                break

        self.valuesChanged.emit()

    def get_item_names_of_type_from_layout(self) -> List[QgsLayoutItem3DMap]:
        items = [x for x in self.layout.items() if isinstance(x, QgsLayoutItem3DMap)]

        return items

    def accept(self) -> None:
        self.update_camera_position()
        super().accept()

    def update_point(self, point, point_type: PointType):
        super().update_point(point, point_type)

        if self.map_tool.is_point_snapped():
            msg = f"Snapped to point at {point.x()} {point.y()} from layer {self.map_tool.snap_layer()}."
        else:
            msg = f"Point at {point.x()} {point.y()} selected."

        self._iface.messageBar().pushMessage("Point defined", msg, duration=5)

    def update_camera_position(self) -> None:
        camera_pose = set_camera_to_position_and_look(
            self.layout_item_3d.mapSettings(),
            self.layout_item_3d.cameraPose(),
            self._list_of_rasters,
            self._iface.mapCanvas().mapSettings().destinationCrs(),
            self.point_observer,
            self.point_target,
            self.observer_offset.value(),
        )

        self.layout_item_3d.setCameraPose(camera_pose)
        self.layout_item_3d.refresh()

        msg = (
            f"Layout item `{self.layout_item_3d.displayName()}` in layout `{self.layout.name()}` "
            "camera settings updated."
        )

        self._iface.messageBar().pushMessage("Layout item updated", msg, duration=5)
