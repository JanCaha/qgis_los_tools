from typing import Optional

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QWidget, QFormLayout
from qgis.gui import QgsDoubleSpinBox
from qgis.core import QgsUnitTypes
from los_tools.gui import DistanceWidget


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

        self._max_angle = QgsDoubleSpinBox(self)
        self._max_angle.setMinimum(-359.999)
        self._max_angle.setMaximum(359.999)
        self._max_angle.setValue(359.999)
        self._max_angle.setClearValue(359)
        self._max_angle.setDecimals(3)
        self._max_angle.valueChanged.connect(self._on_maximum_changed)
        self._max_angle.valueChanged.connect(self.emit_values_changed)

        self._angle_step = QgsDoubleSpinBox(self)
        self._angle_step.setMinimum(0.001)
        self._angle_step.setMaximum(90)
        self._angle_step.setValue(1)
        self._angle_step.setClearValue(1)
        self._angle_step.setDecimals(3)
        self._angle_step.valueChanged.connect(self.emit_values_changed)

        self._length = DistanceWidget(self)
        self._length.setMinimum(1)
        self._length.setMaximum(999999999)
        self._length.setValue(100)
        self._length.setClearValue(100)
        self._length.setDecimals(2)
        self._length.valueChanged.connect(self.emit_values_changed)

        layout.addRow("Minimum Azimuth", self._min_angle)
        layout.addRow("Maximal Azimuth", self._max_angle)
        layout.addRow("Angle Step", self._angle_step)
        layout.addRow("LoS Length", self._length)

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
