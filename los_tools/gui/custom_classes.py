from typing import Optional, Union

from qgis.core import QgsUnitTypes
from qgis.gui import QgsDoubleSpinBox
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QComboBox, QHBoxLayout, QWidget


class Distance:
    def __init__(
        self,
        distance: float = 0,
        unit: QgsUnitTypes.DistanceUnit = QgsUnitTypes.DistanceUnit.DistanceMeters,
    ) -> None:
        self._distance: float = distance
        self._unit: QgsUnitTypes.DistanceUnit = unit

    def __str__(self) -> str:
        return "{} {}".format(self._distance, QgsUnitTypes.toString(self._unit))

    def __eq__(self, other) -> bool:
        return self._distance == other._distance and self._unit == other._unit

    def meters(self) -> float:
        return self.inUnits(QgsUnitTypes.DistanceUnit.DistanceMeters)

    def distance(self) -> float:
        return self._distance

    def unit(self) -> QgsUnitTypes.DistanceUnit:
        return self._unit

    def inUnits(self, unit: QgsUnitTypes.DistanceUnit) -> float:
        conversion = QgsUnitTypes.fromUnitToUnitFactor(self._unit, unit)
        return self._distance * conversion


class DistanceWidget(QWidget):
    valueChanged = pyqtSignal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.Widget,
    ) -> None:
        super().__init__(parent, flags)

        self.init_gui()

    def init_gui(self) -> None:
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        self._distance_value = QgsDoubleSpinBox(self)
        self._distance_value.setMinimum(0.001)
        self._distance_value.setMaximum(999999999)
        self._distance_value.setValue(0)
        self._distance_value.valueChanged.connect(self._raiseValueChanged)

        self._units = QComboBox(self)
        self._units.addItem(
            QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceMeters),
            QgsUnitTypes.DistanceUnit.DistanceMeters,
        )
        self._units.addItem(
            QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceKilometers),
            QgsUnitTypes.DistanceUnit.DistanceKilometers,
        )
        self._units.addItem(
            QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceFeet),
            QgsUnitTypes.DistanceUnit.DistanceFeet,
        )
        self._units.addItem(
            QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceMiles),
            QgsUnitTypes.DistanceUnit.DistanceMiles,
        )
        self._units.addItem(
            QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceYards),
            QgsUnitTypes.DistanceUnit.DistanceYards,
        )
        self._units.currentIndexChanged.connect(self._raiseValueChanged)

        layout.addWidget(self._distance_value)
        layout.addWidget(self._units)

    def _raiseValueChanged(self):
        self.valueChanged.emit()

    def setValue(
        self,
        value: float,
        unit: QgsUnitTypes.DistanceUnit = QgsUnitTypes.DistanceUnit.DistanceMeters,
    ):
        self._units.setCurrentText(QgsUnitTypes.toString(unit))
        self._distance_value.setValue(value)

    def value(self) -> float:
        return self.distance().inUnits(QgsUnitTypes.DistanceUnit.DistanceMeters)

    def distance(self) -> Distance:
        return Distance(self._distance_value.value(), self._units.currentData(Qt.UserRole))

    def setMinimum(self, value: float) -> None:
        self._distance_value.setMinimum(value)

    def setMaximum(self, value: float) -> None:
        self._distance_value.setMaximum(value)

    def setDecimals(self, prec: int) -> None:
        self._distance_value.setDecimals(prec)

    def setClearValue(self, customValue: float) -> None:
        self._distance_value.setClearValue(customValue)

    def setEnabled(self, value: bool) -> None:
        self._distance_value.setEnabled(value)
        self._units.setEnabled(value)

    def unit(self) -> QgsUnitTypes.DistanceUnit:
        return self._units.currentData()

    def set_units(self, unit: QgsUnitTypes.DistanceUnit) -> None:
        self._units.setCurrentText(QgsUnitTypes.toString(unit))


