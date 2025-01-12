from enum import Enum
from typing import List, Optional

from qgis.core import Qgis, QgsSettings, QgsUnitTypes
from qgis.gui import QgsDoubleSpinBox
from qgis.PyQt.QtCore import QSignalBlocker, Qt
from qgis.PyQt.QtWidgets import QCheckBox, QFormLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QTabWidget, QWidget

from los_tools.constants.plugin import PluginConstants
from los_tools.gui.custom_classes import DistancesWidget
from los_tools.gui.tools.los_digitizing_tool_with_widget import LoSDigitizingToolWidget


class LoSNoTargetDefinitionType(Enum):
    AZIMUTHS = 0
    DIRECTION_ANGLE_WIDTH = 1


class LoSNoTargetInputWidget(LoSDigitizingToolWidget):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._rasters = QLineEdit()
        self._rasters.setReadOnly(True)

        self._observer_offset = QgsDoubleSpinBox(self)
        self._observer_offset.setMinimum(0.0)
        self._observer_offset.setMaximum(999999.999)
        self._observer_offset.setValue(1.6)
        self._observer_offset.setClearValue(1.6)
        self._observer_offset.valueChanged.connect(self.save_settings)

        self._min_angle = QgsDoubleSpinBox(self)
        self._min_angle.setMinimum(-359.999)
        self._min_angle.setMaximum(359.999)
        self._min_angle.setValue(0)
        self._min_angle.setClearValue(0)
        self._min_angle.setDecimals(3)
        self._min_angle.valueChanged.connect(self._on_minimum_changed)
        self._min_angle.valueChanged.connect(self.valuesChanged.emit)
        self._min_angle.valueChanged.connect(self.save_settings)

        self._max_angle = QgsDoubleSpinBox(self)
        self._max_angle.setMinimum(-359.999)
        self._max_angle.setMaximum(359.999)
        self._max_angle.setValue(359.999)
        self._max_angle.setClearValue(359.999)
        self._max_angle.setDecimals(3)
        self._max_angle.valueChanged.connect(self._on_maximum_changed)
        self._max_angle.valueChanged.connect(self.valuesChanged.emit)
        self._max_angle.valueChanged.connect(self.save_settings)

        self._angle_difference = QgsDoubleSpinBox(self)
        self._angle_difference.setMinimum(0.000)
        self._angle_difference.setMaximum(180.000)
        self._angle_difference.setValue(10.000)
        self._angle_difference.setClearValue(10.000)
        self._angle_difference.setDecimals(3)
        self._angle_difference.setSuffix("°")
        self._angle_difference.valueChanged.connect(self.valuesChanged.emit)
        self._angle_difference.valueChanged.connect(self.save_settings)

        page_1 = QWidget(self)
        page_1_layout = QFormLayout()
        page_1.setLayout(page_1_layout)

        page_1_layout.addRow("Minimum Azimuth", self._min_angle)
        page_1_layout.addRow("Maximal Azimuth", self._max_angle)

        page_2 = QWidget(self)
        page_2_layout = QFormLayout()
        page_2.setLayout(page_2_layout)

        page_2_layout.addRow("Angle Difference", self._angle_difference)

        self._tabs = QTabWidget(self)
        self._tabs.addTab(page_1, "Definition by Azimuth")
        self._tabs.addTab(page_2, "Definition by Angle Width")

        self._tabs.currentChanged.connect(self.valuesChanged.emit)
        self._tabs.currentChanged.connect(self.save_settings)

        self._angle_step = QgsDoubleSpinBox(self)
        self._angle_step.setMinimum(0.001)
        self._angle_step.setMaximum(90)
        self._angle_step.setValue(1)
        self._angle_step.setClearValue(1)
        self._angle_step.setDecimals(3)
        self._angle_step.setSuffix("°")
        self._angle_step.valueChanged.connect(self._angle_step_changed)
        self._angle_step.valueChanged.connect(self.valuesChanged.emit)
        self._angle_step.valueChanged.connect(self.save_settings)

        self._show_distances = QCheckBox(self)
        self._show_distances.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._show_distances.setChecked(False)
        self._show_distances.stateChanged.connect(self.valuesChanged.emit)
        self._show_distances.stateChanged.connect(self.save_settings)

        self._distances = DistancesWidget(self)
        self._distances.setEnabled(False)
        self._show_distances.stateChanged.connect(self._distances.setEnabled)
        self._distances.valueChanged.connect(self.valuesChanged.emit)
        self._distances.valueChanged.connect(self.save_settings)

        self._add_los_to_layer = QPushButton("Add LoS to Plugin Layer")
        self._add_los_to_layer.setEnabled(False)
        self._add_los_to_layer.clicked.connect(self.clickedAddLosToLayer)

        layout.addWidget(QLabel("Rasters"), 0, 0)
        layout.addWidget(self._rasters, 0, 1)

        layout.addWidget(QLabel("Observer Offset"), 1, 0)
        layout.addWidget(self._observer_offset, 1, 1)

        layout.addWidget(self._tabs, 2, 0, 1, 2)
        layout.addWidget(QLabel("Angle Step"), 3, 0)
        layout.addWidget(self._angle_step, 3, 1)
        layout.addWidget(QLabel("Show Distance Limits"), 4, 0)
        layout.addWidget(self._show_distances, 4, 1)
        layout.addWidget(QLabel("Distance Limits"), 5, 0)
        layout.addWidget(self._distances, 5, 1)
        layout.addWidget(self._add_los_to_layer, 6, 1, 1, 2)

        self._unit = QgsUnitTypes.DistanceUnit.DistanceMeters

    def _on_minimum_changed(self) -> None:
        if self._max_angle.value() < self._min_angle.value():
            self._max_angle.setValue(self._min_angle.value())

    def _on_maximum_changed(self) -> None:
        if self._min_angle.value() > self._max_angle.value():
            self._min_angle.setValue(self._max_angle.value())

    def _angle_step_changed(self) -> None:
        if self._angle_step.value() > self._angle_difference.value() * 2:
            self._angle_step.setValue(self._angle_difference.value() * 2)

    @property
    def los_type_definition(self) -> LoSNoTargetDefinitionType:
        if self._tabs.currentIndex() == 0:
            return LoSNoTargetDefinitionType.AZIMUTHS
        elif self._tabs.currentIndex() == 1:
            return LoSNoTargetDefinitionType.DIRECTION_ANGLE_WIDTH

        return LoSNoTargetDefinitionType.AZIMUTHS

    @property
    def min_angle(self) -> float:
        return self._min_angle.value()

    @property
    def max_angle(self) -> float:
        return self._max_angle.value()

    @property
    def angle_step(self) -> float:
        if self._angle_step.value() == 0:
            return 0.01
        return self._angle_step.value()

    def setUnit(self, unit: QgsUnitTypes.DistanceUnit.DistanceMeters) -> None:
        self._unit = unit

    @property
    def angle_difference(self) -> float:
        return self._angle_difference.value()

    @property
    def show_distance_limits(self) -> bool:
        return self._show_distances.isChecked()

    @property
    def distance_limits(self) -> List[float]:
        return self._distances.distances_in_units(self._unit)

    @property
    def observer_offset(self) -> float:
        return self._observer_offset.value()

    def save_settings(self) -> None:
        settings = QgsSettings()
        settings_class = f"{PluginConstants.settings_group}/LoSNoTarget"

        settings.setValue(f"{settings_class}/ObserverOffset", self.observer_offset, section=QgsSettings.Section.Plugins)
        settings.setValue(f"{settings_class}/MinAngle", self.min_angle, section=QgsSettings.Section.Plugins)
        settings.setValue(f"{settings_class}/MaxAngle", self.max_angle, section=QgsSettings.Section.Plugins)
        settings.setValue(f"{settings_class}/AngleStep", self.angle_step, section=QgsSettings.Section.Plugins)
        settings.setValue(
            f"{settings_class}/ShowDistanceLimits", self.show_distance_limits, section=QgsSettings.Section.Plugins
        )
        settings.setValue(
            f"{settings_class}/DistanceLimits",
            ";".join([str(x) for x in self.distance_limits]),
            section=QgsSettings.Section.Plugins,
        )
        settings.setValue(
            f"{settings_class}/DistanceLimitsUnits",
            QgsUnitTypes.encodeUnit(self._distances.units()),
            section=QgsSettings.Section.Plugins,
        )
        settings.setValue(
            f"{settings_class}/AngleDifference", self._angle_difference.value(), section=QgsSettings.Section.Plugins
        )
        settings.setValue(
            f"{settings_class}/LoSType", self.los_type_definition.value, section=QgsSettings.Section.Plugins
        )

    def load_settings(self) -> None:
        settings = QgsSettings()
        settings_class = f"{PluginConstants.settings_group}/LoSNoTarget"

        with QSignalBlocker(self._observer_offset):
            self._observer_offset.setValue(
                settings.value(f"{settings_class}/ObserverOffset", 1.6, type=float, section=QgsSettings.Section.Plugins)
            )

        with QSignalBlocker(self._min_angle):
            self._min_angle.setValue(
                settings.value(f"{settings_class}/MinAngle", 0, type=float, section=QgsSettings.Section.Plugins)
            )

        with QSignalBlocker(self._max_angle):
            self._max_angle.setValue(
                settings.value(f"{settings_class}/MaxAngle", 359.999, type=float, section=QgsSettings.Section.Plugins)
            )

        with QSignalBlocker(self._angle_step):
            self._angle_step.setValue(
                settings.value(f"{settings_class}/AngleStep", 1, type=float, section=QgsSettings.Section.Plugins)
            )

        with QSignalBlocker(self._show_distances):
            self._show_distances.setChecked(
                settings.value(
                    f"{settings_class}/ShowDistanceLimits", False, type=bool, section=QgsSettings.Section.Plugins
                )
            )
            if self._show_distances.isChecked():
                self._distances.setEnabled(True)

        with QSignalBlocker(self._distances):
            distances = settings.value(
                f"{settings_class}/DistanceLimits", "", type=str, section=QgsSettings.Section.Plugins
            )
            if distances:
                distances = [float(x) for x in distances.split(";")]
                self._distances.set_distances(distances)

        unit, success = QgsUnitTypes.decodeDistanceUnit(
            settings.value(
                f"{settings_class}/DistanceLimitsUnits",
                QgsUnitTypes.toString(Qgis.DistanceUnit.Meters),
                section=QgsSettings.Section.Plugins,
            )
        )
        if not success:
            unit = Qgis.DistanceUnit.Meters

        with QSignalBlocker(self._distances):
            self._distances.set_units(unit)

        with QSignalBlocker(self._angle_difference):
            self._angle_difference.setValue(
                settings.value(f"{settings_class}/AngleDifference", 10, type=float, section=QgsSettings.Section.Plugins)
            )

        tab_index = settings.value(f"{settings_class}/LoSType", 0, type=int, section=QgsSettings.Section.Plugins)
        self._tabs.setCurrentIndex(tab_index)
