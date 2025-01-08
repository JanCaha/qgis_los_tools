from typing import Optional

from qgis.core import Qgis, QgsSettings, QgsUnitTypes
from qgis.gui import QgsDoubleSpinBox
from qgis.PyQt.QtCore import QSignalBlocker
from qgis.PyQt.QtWidgets import QComboBox, QFormLayout, QLineEdit, QPushButton, QWidget

from los_tools.constants.plugin import PluginConstants
from los_tools.gui.create_los_tool.los_digitizing_tool_with_widget import LoSDigitizingToolWidget
from los_tools.gui.custom_classes import Distance, DistanceWidget


class LoSInputWidget(LoSDigitizingToolWidget):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.form_layout)

        self._rasters = QLineEdit()
        self._rasters.setReadOnly(True)

        self._los_type = QComboBox(self)
        self._los_type.addItem("Local")
        self._los_type.addItem("Global")
        self._los_type.currentIndexChanged.connect(self.save_settings)

        self._observer_offset = QgsDoubleSpinBox(self)
        self._observer_offset.setMinimum(0.0)
        self._observer_offset.setMaximum(999999.999)
        self._observer_offset.setValue(1.6)
        self._observer_offset.setClearValue(1.6)
        self._observer_offset.valueChanged.connect(self.save_settings)

        self._target_offset = QgsDoubleSpinBox(self)
        self._target_offset.setMinimum(0.0)
        self._target_offset.setMaximum(999999.999)
        self._target_offset.setValue(0.0)
        self._target_offset.setClearValue(0.0)
        self._target_offset.valueChanged.connect(self.save_settings)

        self._sampling_distance = DistanceWidget(self)
        self._sampling_distance.setMinimum(0.01)
        self._sampling_distance.setMaximum(999999.999)
        self._sampling_distance.setValue(1.0)
        self._sampling_distance.setClearValue(1.0)
        self._sampling_distance.setDecimals(2)
        self._sampling_distance.valueChanged.connect(self.save_settings)

        self._add_los_to_layer = QPushButton("Add LoS to Plugin Layer")
        self._add_los_to_layer.setEnabled(False)
        self._add_los_to_layer.clicked.connect(self.clickedAddLosToLayer)

        self.form_layout.addRow("Rasters", self._rasters)
        self.form_layout.addRow("LoS Type", self._los_type)
        self.form_layout.addRow("Observer Offset", self._observer_offset)
        self.form_layout.addRow("Target Offset", self._target_offset)
        self.form_layout.addRow("Sampling Distance", self._sampling_distance)

        self.form_layout.addWidget(self._add_los_to_layer)

    @property
    def sampling_distance(self) -> Distance:
        return self._sampling_distance.distance()

    @property
    def observer_offset(self) -> float:
        return self._observer_offset.value()

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

    def load_settings(self) -> None:
        settings = QgsSettings()
        settings_class = f"{PluginConstants.settings_group}/CreateLoSTool"

        with QSignalBlocker(self._los_type):
            self._los_type.setCurrentText(
                settings.value(f"{settings_class}/LoSType", "Local", type=str, section=QgsSettings.Section.Plugins)
            )

        with QSignalBlocker(self._observer_offset):
            self._observer_offset.setValue(
                settings.value(f"{settings_class}/ObserverOffset", 1.6, type=float, section=QgsSettings.Section.Plugins)
            )

        with QSignalBlocker(self._target_offset):

            self._target_offset.setValue(
                settings.value(f"{settings_class}/TargetOffset", 0, type=float, section=QgsSettings.Section.Plugins)
            )

        with QSignalBlocker(self._sampling_distance):
            self._sampling_distance.setValue(
                settings.value(f"{settings_class}/SamplingDistance", 1, type=float, section=QgsSettings.Section.Plugins)
            )

        unit, success = QgsUnitTypes.decodeDistanceUnit(
            settings.value(
                f"{settings_class}/SamplingDistanceUnits",
                QgsUnitTypes.toString(Qgis.DistanceUnit.Meters),
                section=QgsSettings.Section.Plugins,
            )
        )

        with QSignalBlocker(self._sampling_distance):
            if success:
                self._sampling_distance.set_units(unit)
            else:
                self._sampling_distance.set_units(Qgis.DistanceUnit.Meters)

    def save_settings(self) -> None:
        settings = QgsSettings()
        settings_class = f"{PluginConstants.settings_group}/CreateLoSTool"
        settings.setValue(f"{settings_class}/LoSType", self.los_type, section=QgsSettings.Section.Plugins)
        settings.setValue(f"{settings_class}/ObserverOffset", self.observer_offset, section=QgsSettings.Section.Plugins)
        settings.setValue(f"{settings_class}/TargetOffset", self.target_offset, section=QgsSettings.Section.Plugins)
        settings.setValue(
            f"{settings_class}/SamplingDistance", self.sampling_distance.distance(), section=QgsSettings.Section.Plugins
        )
        settings.setValue(
            f"{settings_class}/SamplingDistanceUnits",
            QgsUnitTypes.encodeUnit(self._sampling_distance.unit()),
            section=QgsSettings.Section.Plugins,
        )
