from typing import Optional

from qgis.gui import QgsDoubleSpinBox
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QComboBox, QFormLayout, QPushButton, QWidget

from los_tools.gui.custom_classes import Distance, DistanceWidget


class LoSInputWidget(QWidget):
    valuesChanged = pyqtSignal()
    saveToLayerClicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.form_layout)

        self._los_type = QComboBox(self)
        self._los_type.addItem("Local")
        self._los_type.addItem("Global")
        self._los_type.addItem("No Target")
        self._los_type.currentIndexChanged.connect(self.change_setting_enabled)

        self._observers_offset = QgsDoubleSpinBox(self)
        self._observers_offset.setMinimum(0.0)
        self._observers_offset.setMaximum(999999.999)
        self._observers_offset.setValue(1.6)
        self._observers_offset.setClearValue(1.6)

        self._target_offset = QgsDoubleSpinBox(self)
        self._target_offset.setMinimum(0.0)
        self._target_offset.setMaximum(999999.999)
        self._target_offset.setValue(0.0)
        self._target_offset.setClearValue(0.0)

        self._sampling_distance = DistanceWidget(self)
        self._sampling_distance.setMinimum(0.01)
        self._sampling_distance.setMaximum(999999.999)
        self._sampling_distance.setValue(1.0)
        self._sampling_distance.setClearValue(1.0)
        self._sampling_distance.setDecimals(2)

        self._angle_difference = QgsDoubleSpinBox(self)
        self._angle_difference.setMinimum(0.000)
        self._angle_difference.setMaximum(180.000)
        self._angle_difference.setValue(10.000)
        self._angle_difference.setClearValue(10.000)
        self._angle_difference.setDecimals(3)
        self._angle_difference.setEnabled(False)
        self._angle_difference.setSuffix("°")
        self._angle_difference.valueChanged.connect(self.emit_values_changed)

        self._angle_step = QgsDoubleSpinBox(self)
        self._angle_step.setMinimum(0.001)
        self._angle_step.setMaximum(90)
        self._angle_step.setValue(1)
        self._angle_step.setClearValue(1)
        self._angle_step.setDecimals(3)
        self._angle_step.setEnabled(False)
        self._angle_step.setSuffix("°")
        self._angle_step.valueChanged.connect(self.angle_step_changed)
        self._angle_step.valueChanged.connect(self.emit_values_changed)

        self._add_los_to_layer = QPushButton("Add LoS to Plugin Layer")
        self._add_los_to_layer.setEnabled(False)
        self._add_los_to_layer.clicked.connect(self.clickedAddLosToLayer)

        self.form_layout.addRow("LoS Type", self._los_type)
        self.form_layout.addRow("Observer Offset", self._observers_offset)
        self.form_layout.addRow("Target Offset", self._target_offset)
        self.form_layout.addRow("Sampling Distance", self._sampling_distance)
        self.form_layout.addRow("Angle Difference", self._angle_difference)
        self.form_layout.addRow("Angle Step", self._angle_step)
        self.form_layout.addWidget(self._add_los_to_layer)

    def change_setting_enabled(self) -> None:
        self._angle_difference.setEnabled(self.los_no_target)
        self._angle_step.setEnabled(self.los_no_target)
        if self.los_local or self.los_global:
            self._angle_difference.setEnabled(False)
            self._angle_step.setEnabled(False)
            self._sampling_distance.setEnabled(True)
            self._target_offset.setEnabled(True)
        else:
            self._angle_difference.setEnabled(True)
            self._angle_step.setEnabled(True)
            self._sampling_distance.setEnabled(False)
            self._target_offset.setEnabled(False)

    def angle_step_changed(self) -> None:
        if self._angle_step.value() > self._angle_difference.value() * 2:
            self._angle_step.setValue(self._angle_difference.value() * 2)

    @property
    def sampling_distance(self) -> Distance:
        return self._sampling_distance.distance()

    @property
    def observer_offset(self) -> float:
        return self._observers_offset.value()

    @property
    def target_offset(self) -> float:
        return self._target_offset.value()

    @property
    def angle_step(self) -> float:
        return self._angle_step.value()

    @property
    def angle_difference(self) -> float:
        return self._angle_difference.value()

    @property
    def los_type(self) -> str:
        return self._los_type.currentText()

    @property
    def los_local(self) -> bool:
        return self._los_type.currentText() == "Local"

    @property
    def los_global(self) -> bool:
        return self._los_type.currentText() == "Global"

    @property
    def los_no_target(self) -> bool:
        return self._los_type.currentText() == "No Target"

    def emit_values_changed(self) -> None:
        self.valuesChanged.emit()

    def clickedAddLosToLayer(self) -> None:
        self.saveToLayerClicked.emit()
        self.disableAddLos()

    def enableAddLos(self) -> None:
        self._add_los_to_layer.setEnabled(True)

    def disableAddLos(self) -> None:
        self._add_los_to_layer.setEnabled(False)
