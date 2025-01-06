from functools import partial
from typing import List, Optional, Union

from qgis.core import Qgis, QgsApplication, QgsUnitTypes
from qgis.gui import QgsDoubleSpinBox
from qgis.PyQt.QtCore import QAbstractItemModel, QModelIndex, Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QStyledItemDelegate,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


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


class DistancesLineEdit(QLineEdit):

    clicked = pyqtSignal()

    def mouseReleaseEvent(self, a0):
        self.clicked.emit()
        return super().mouseReleaseEvent(a0)


class NumericTreeItem(QTreeWidgetItem):
    def __lt__(self, other):
        column = self.treeWidget().sortColumn()

        try:
            value1 = self.data(column, Qt.ItemDataRole.EditRole)
            value2 = other.data(column, Qt.ItemDataRole.EditRole)

            if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                return value1 < value2
        except:
            pass

        return super().__lt__(other)


class DistancesDialog(QDialog):

    distancesChanged = pyqtSignal()

    def __init__(
        self,
        distance_units: Qgis.DistanceUnit = Qgis.DistanceUnit.Meters,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowType.Window,
    ):
        super().__init__(parent, flags)

        self._distance_units = distance_units
        self.init_gui()

    def init_gui(self) -> None:
        self.setModal(True)
        self.setWindowTitle("Distances")
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        label = QLabel(f"Distances in {QgsUnitTypes.toString(self._distance_units)}")

        line_layout = QHBoxLayout()

        self._tool_button_add = QToolButton()
        self._tool_button_remove = QToolButton()
        line_layout.addStretch(1)
        line_layout.addWidget(self._tool_button_add)
        line_layout.addWidget(self._tool_button_remove)

        self._tool_button_add.setIcon(QgsApplication.getThemeIcon("/symbologyAdd.svg"))
        self._tool_button_remove.setIcon(QgsApplication.getThemeIcon("/symbologyRemove.svg"))

        self._tool_button_add.clicked.connect(self.add_distance)
        self._tool_button_remove.clicked.connect(self.remove_distance)

        self._distances_tree_widget = QTreeWidget(self)
        self._distances_tree_widget.setColumnCount(1)
        self._distances_tree_widget.setHeaderLabels(["Distance"])
        self._distances_tree_widget.setItemDelegateForColumn(0, DistanceSpinBoxDelegate(self._distances_tree_widget))
        self._distances_tree_widget.setSortingEnabled(True)
        self._distances_tree_widget.header().setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        self._distances_tree_widget.itemChanged.connect(self.distancesChanged.emit)
        self._distances_tree_widget.currentItemChanged.connect(self.activate_deletion)

        layout.addWidget(label)
        layout.addLayout(line_layout)
        layout.addWidget(self._distances_tree_widget)

    def distances(self) -> List[float]:
        distances = []

        for i in range(self._distances_tree_widget.topLevelItemCount()):
            item = self._distances_tree_widget.topLevelItem(i)
            distances.append(float(item.data(0, Qt.ItemDataRole.EditRole)))

        return distances

    def add_distance(self):
        item = NumericTreeItem([str(0)])
        item.setData(0, Qt.ItemDataRole.EditRole, 0)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
        self._distances_tree_widget.addTopLevelItem(item)

        self.distancesChanged.emit()

    def remove_distance(self):
        self._distances_tree_widget.takeTopLevelItem(self._distances_tree_widget.currentIndex().row())

        self.distancesChanged.emit()

    def activate_deletion(self) -> None:
        if self._distances_tree_widget.currentIndex().row() == -1:
            self._tool_button_remove.setEnabled(False)
        else:
            self._tool_button_remove.setEnabled(True)


class DistancesWidget(QWidget):
    valueChanged = pyqtSignal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.Widget,
    ) -> None:
        super().__init__(parent, flags)

        self.distances: List[float] = []

        self.init_gui()

    def setEnabled(self, a0: bool) -> None:
        self._distance_values.setEnabled(a0)
        self._units.setEnabled(a0)
        return super().setEnabled(a0)

    def blockSignals(self, a0: bool) -> None:
        self._distance_values.blockSignals(a0)
        self._units.blockSignals(a0)
        return super().blockSignals(a0)

    def init_gui(self) -> None:
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        self._distance_values = DistancesLineEdit(self)
        self._distance_values.setReadOnly(True)
        self._distance_values.clicked.connect(self.open_distances_dialog)
        self._distance_values.textChanged.connect(self.valueChanged.emit)

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
        self._units.currentIndexChanged.connect(self.valueChanged.emit)

        layout.addWidget(self._distance_values)
        layout.addWidget(self._units)

    def open_distances_dialog(self):
        dialog = DistancesDialog()
        dialog.distancesChanged.connect(partial(self.setup_distances, dialog))
        dialog.exec()

    def setup_distances(self, dialog: DistancesDialog) -> None:
        self.distances = dialog.distances()
        self.distances.sort()
        self._distance_values.setText(", ".join(str(d) for d in self.distances))

    def set_distances(self, distances: List[float]):
        self.distances = distances
        self.distances.sort()
        self._distance_values.setText(", ".join(str(d) for d in self.distances))

    def units(self) -> QgsUnitTypes.DistanceUnit:
        return self._units.currentData()

    def set_units(self, unit: QgsUnitTypes.DistanceUnit):
        self._units.setCurrentText(QgsUnitTypes.toString(unit))

    def distances_in_units(self, unit: QgsUnitTypes.DistanceUnit) -> List[float]:
        distances = []
        for d in self.distances:
            distances.append(Distance(d, self._units.currentData()).inUnits(unit))

        return distances

    def distances_original_units(self) -> List[float]:
        return self.distances


class DistanceSpinBoxDelegate(QStyledItemDelegate):

    def createEditor(self, parent: QWidget, option, index):

        editor = QDoubleSpinBox(parent)
        editor.setMinimum(0)
        editor.setMaximum(999999999.99)
        editor.setDecimals(2)
        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        if isinstance(editor, QDoubleSpinBox):
            value = float(index.model().data(index, Qt.ItemDataRole.EditRole) or 0)
            editor.setValue(value)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if isinstance(editor, QDoubleSpinBox):
            model.setData(index, editor.value(), Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)
