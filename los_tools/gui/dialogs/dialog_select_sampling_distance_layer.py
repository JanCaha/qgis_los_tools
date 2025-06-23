import typing

from qgis.core import Qgis, QgsMapLayer, QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QWidget

from los_tools.constants.plugin import PluginConstants


class SelectSamplingDistanceLayerDialog(QDialog):

    def __init__(
        self,
        parent: typing.Optional[QWidget] = None,
        flags: typing.Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowType.Dialog,
    ) -> None:
        super().__init__(parent, flags)

        self.init_gui()

    def init_gui(self) -> None:
        self.setWindowTitle("Select Distance Sampling Layer")
        self.setMinimumWidth(600)

        layout = QFormLayout(self)
        self.setLayout(layout)

        project = QgsProject.instance()
        layers_ids = project.mapLayers(True)

        selectedLayers: typing.List[QgsMapLayer] = []

        for layer_id in layers_ids:
            layer = project.mapLayer(layer_id)
            if isinstance(layer, QgsVectorLayer):
                if (
                    layer.geometryType() == Qgis.GeometryType.Null
                    and layer.customProperty(PluginConstants.sampling_distance_layer)
                    == PluginConstants.sampling_distance_layer_value
                ):
                    selectedLayers.append(layer)

        self.layer_cb = QComboBox(self)
        self.layer_cb.currentIndexChanged.connect(self.on_layer_changed)

        self.buttons = QDialogButtonBox(self)
        self.buttons.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addRow("Select Layer", self.layer_cb)
        layout.addWidget(self.buttons)

        for layer in selectedLayers:
            self.layer_cb.addItem(layer.name(), layer)

    def layer(self) -> QgsVectorLayer:
        if self.layer_cb.currentIndex() == -1:
            return None
        return self.layer_cb.currentData(Qt.ItemDataRole.UserRole)

    def on_layer_changed(self, index: int) -> None:
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(index != -1)
