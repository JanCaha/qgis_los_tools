from qgis._3d import Qgs3DMapCanvas
from qgis.PyQt.QtWidgets import QGridLayout, QLabel, QLineEdit

from los_tools.gui._3d.dialog_camera import DialogCameraSetting
from los_tools.gui._3d.utils import set_camera_to_position_and_look


class Create3DView(DialogCameraSetting):

    def init_gui(self):
        super().init_gui()

        self.setMinimumWidth(600)
        self.setWindowTitle("Create 3D View")

        layout = QGridLayout(self)
        self.setLayout(layout)

        self.name_3d_view = QLineEdit()
        self.name_3d_view.textChanged.connect(lambda: self.valuesChanged.emit())

        layout.addWidget(QLabel("Name of 3D View:"), 0, 0)
        layout.addWidget(self.name_3d_view, 0, 1)
        layout.addWidget(QLabel("Project terrain type is:"), 1, 0)
        layout.addWidget(self.terrain_type, 1, 1)
        layout.addWidget(self.observer_btn, 2, 0)
        layout.addWidget(self.observer_coordinate, 2, 1)
        layout.addWidget(QLabel("Observer Offset:"), 3, 0)
        layout.addWidget(self.observer_offset, 3, 1)

        layout.addWidget(self.target_btn, 4, 0)
        layout.addWidget(self.target_coordinate, 4, 1)

        layout.addWidget(self.button_box, 5, 0, 1, 2)

        self.valuesChanged.connect(self.check_valid)

    def check_valid(self) -> None:
        if not self.name_3d_view.text():
            return
        return super().set_acceptable()

    def create_3d_view(self) -> None:
        canvas_3d: Qgs3DMapCanvas = self._iface.createNewMapCanvas3D(self.name_3d_view.text())

        camera_controller = canvas_3d.cameraController()

        camera_pose = set_camera_to_position_and_look(
            canvas_3d.mapSettings(),
            camera_controller.cameraPose(),
            self.elevation_provider,
            self._iface.mapCanvas().mapSettings().destinationCrs(),
            self.point_observer,
            self.point_target,
            self.observer_offset.value(),
        )

        camera_controller.setCameraPose(camera_pose)

    def accept(self):
        self.create_3d_view()
        return super().accept()
