from typing import List, Optional

from qgis.core import Qgis, QgsSettings, QgsUnitTypes
from qgis.gui import QgsDoubleSpinBox
from qgis.PyQt.QtCore import QSignalBlocker, Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QCheckBox, QFormLayout, QWidget

from los_tools.constants.plugin import PluginConstants
from los_tools.gui.custom_classes import DistancesWidget, DistanceWidget


class LoSNoTargetInputWidget(QWidget):

    valuesChanged = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._min_angle = QgsDoubleSpinBox(self)
        self._min_angle.setMinimum(-359.999)
        self._min_angle.setMaximum(359.999)
        self._min_angle.setValue(0)
        self._min_angle.setClearValue(0)
        self._min_angle.setDecimals(3)
        self._min_angle.valueChanged.connect(self._on_minimum_changed)
        self._min_angle.valueChanged.connect(self.emit_values_changed)
        self._min_angle.valueChanged.connect(self.save_settings)

        self._max_angle = QgsDoubleSpinBox(self)
        self._max_angle.setMinimum(-359.999)
        self._max_angle.setMaximum(359.999)
        self._max_angle.setValue(359.999)
        self._max_angle.setClearValue(359.999)
        self._max_angle.setDecimals(3)
        self._max_angle.valueChanged.connect(self._on_maximum_changed)
        self._max_angle.valueChanged.connect(self.emit_values_changed)
        self._max_angle.valueChanged.connect(self.save_settings)

        self._angle_step = QgsDoubleSpinBox(self)
        self._angle_step.setMinimum(0.001)
        self._angle_step.setMaximum(90)
        self._angle_step.setValue(1)
        self._angle_step.setClearValue(1)
        self._angle_step.setDecimals(3)
        self._angle_step.valueChanged.connect(self.emit_values_changed)
        self._angle_step.valueChanged.connect(self.save_settings)

        self._length = DistanceWidget(self)
        self._length.setMinimum(1)
        self._length.setMaximum(999999999)
        self._length.setValue(100)
        self._length.setClearValue(100)
        self._length.setDecimals(2)
        self._length.valueChanged.connect(self.emit_values_changed)
        self._length.valueChanged.connect(self.save_settings)

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

        layout.addRow("Minimum Azimuth", self._min_angle)
        layout.addRow("Maximal Azimuth", self._max_angle)
        layout.addRow("Angle Step", self._angle_step)
        layout.addRow("LoS Length", self._length)
        layout.addRow("Show Distance Limits", self._show_distances)
        layout.addRow("Distance Limits", self._distances)

        self._unit = QgsUnitTypes.DistanceUnit.DistanceMeters

    def _on_minimum_changed(self) -> None:
        if self._max_angle.value() < self._min_angle.value():
            self._max_angle.setValue(self._min_angle.value())

    def _on_maximum_changed(self) -> None:
        if self._min_angle.value() > self._max_angle.value():
            self._min_angle.setValue(self._max_angle.value())

    def emit_values_changed(self) -> None:
        self.valuesChanged.emit()

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
    def length(self) -> float:
        return self._length.distance().inUnits(self._unit)

    @property
    def show_distance_limits(self) -> bool:
        return self._show_distances.isChecked()

    @property
    def distance_limits(self) -> List[float]:
        return self._distances.distances_in_units(self._unit)

    def save_settings(self) -> None:
        settings = QgsSettings()
        settings_class = f"{PluginConstants.settings_group}/LoSNoTarget"

        settings.setValue(f"{settings_class}/MinAngle", self.min_angle, section=QgsSettings.Section.Plugins)
        settings.setValue(f"{settings_class}/MaxAngle", self.max_angle, section=QgsSettings.Section.Plugins)
        settings.setValue(f"{settings_class}/AngleStep", self.angle_step, section=QgsSettings.Section.Plugins)
        settings.setValue(f"{settings_class}/Length", self.length, section=QgsSettings.Section.Plugins)
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

    def load_settings(self) -> None:
        settings = QgsSettings()
        settings_class = f"{PluginConstants.settings_group}/LoSNoTarget"

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

        with QSignalBlocker(self._length):
            self._length.setValue(
                settings.value(f"{settings_class}/Length", 100, type=float, section=QgsSettings.Section.Plugins)
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
