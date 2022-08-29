from typing import Optional, Union, List
import math

from qgis.core import (QgsUnitTypes, QgsApplication, QgsMemoryProviderUtils, QgsFields, QgsField,
                       QgsWkbTypes, QgsFeature, QgsProject)
from qgis.PyQt.QtWidgets import (QDialog, QHBoxLayout, QComboBox, QPushButton, QToolButton,
                                 QDoubleSpinBox, QWidget, QFormLayout, QTreeWidget,
                                 QTreeWidgetItem, QGroupBox, QCheckBox, QTextBrowser)
from qgis.PyQt.QtCore import (Qt, pyqtSignal, QVariant)

from ..constants.field_names import FieldNames


class LoSSettings(QDialog):

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.Dialog) -> None:
        super().__init__(parent, flags)

        self._distances: List[Distance] = []

        self.init_gui()

        self._calculate_object_angle_size()

    def init_gui(self) -> None:

        self.setWindowTitle("LoS without Target Sampling Settings")
        self.setMinimumWidth(600)

        layout = QFormLayout(self)
        self.setLayout(layout)

        group_box_object = QGroupBox("Object settings", self)
        layout_group_box_object = QFormLayout()
        group_box_object.setLayout(layout_group_box_object)

        self.object_size = DistanceWidget()
        self.object_size.setValue(1)
        self.object_size.valueChanged.connect(self._calculate_object_angle_size)

        self.object_distance = DistanceWidget()
        self.object_distance.setValue(1000)
        self.object_distance.valueChanged.connect(self._calculate_object_angle_size)

        self.object_angle_size = QDoubleSpinBox()
        self.object_angle_size.setDecimals(3)
        self.object_angle_size.setReadOnly(True)
        self.object_angle_size.setSuffix("°")
        self.object_angle_size.valueChanged.connect(self.fill_distances)
        self.object_angle_size.valueChanged.connect(self.description_text)

        layout_group_box_object.addRow("Object Size", self.object_size)
        layout_group_box_object.addRow("Object Distance", self.object_distance)
        layout_group_box_object.addRow("Object Angle Size", self.object_angle_size)

        self.text = QTextBrowser(self)
        self.text.setReadOnly(True)
        self.description_text()

        group_box_los = QGroupBox("LoS settings", self)
        layout_group_box_los = QFormLayout()
        group_box_los.setLayout(layout_group_box_los)

        self.default_sampling_size = DistanceWidget()
        self.default_sampling_size.setValue(1)
        self.default_sampling_size.valueChanged.connect(self.fill_distances)

        self.maximal_los_length = DistanceWidget()
        self.maximal_los_length.setValue(10, QgsUnitTypes.DistanceKilometers)
        self.maximal_los_length.valueChanged.connect(self.fill_distances)
        self.use_maximal_los_length = QCheckBox()
        self.use_maximal_los_length.stateChanged.connect(self.fill_distances)

        layout_group_box_los.addRow("Default Sampling Size", self.default_sampling_size)
        layout_group_box_los.addRow("Maximal LoS Length", self.maximal_los_length)
        layout_group_box_los.addRow("Use Maximal LoS Length", self.use_maximal_los_length)

        self.distance = DistanceWidget()
        self.distance.setValue(1, QgsUnitTypes.DistanceKilometers)

        lineLayout = QHBoxLayout()

        self.toolButton_add = QToolButton()
        self.toolButton_remove = QToolButton()
        self.toolButton_add.setIcon(QgsApplication.getThemeIcon('/symbologyAdd.svg'))
        self.toolButton_remove.setIcon(QgsApplication.getThemeIcon('/symbologyRemove.svg'))
        self.toolButton_add.clicked.connect(self.add_distance)
        self.toolButton_remove.clicked.connect(self.remove_distance)

        lineLayout.addStretch(1)
        lineLayout.addWidget(self.toolButton_add)
        lineLayout.addWidget(self.toolButton_remove)

        self.treeView = QTreeWidget(self)
        self.treeView.setHeaderLabels(["Distance", "Sampling Size"])

        self.button_add_layer = QPushButton("Add layer to project")
        self.button_add_layer.clicked.connect(self.add_layer_to_project)

        layout.addRow(group_box_object)
        layout.addRow(self.text)
        layout.addRow(group_box_los)
        layout.addRow("Distance Add", self.distance)
        layout.addRow(lineLayout)
        layout.addRow(self.treeView)
        layout.addRow(self.button_add_layer)

    def description_text(self) -> None:
        text = [
            "To detect object of size {} at distance {}, the angular sampling needs to be {}°. ".
            format(self.object_size.distance(), self.object_distance.distance(),
                   self.object_angle_size.value()),
            "With this angular sampling of lines-of-sight, it is guaranteed to hit the object at least once.\n",
            "The approach can be done, to simplify sampling on each LoS. With growing distance from observer, it is possible to sample less frequently.\n",
            "Below the calculation of sampling distances for various distances can be performed.\n",
            "Default sampling size is used for distances below the first specified distance. Then after each specified distance the calculated sampling distance is used."
        ]
        self.text.setText("".join(text))

    def _calculate_object_angle_size(self) -> None:
        distance = self.object_distance.value()
        if 0 < distance:
            self.object_angle_size.setValue(
                math.degrees(math.atan(self.object_size.value() / distance)))
        else:
            self.object_angle_size.setValue(0)

    def add_distance(self) -> None:
        distance = self.distance.distance()
        if distance not in self._distances:
            self._distances.append(distance)
            self._distances.sort(key=lambda x: x.meters())
            self.fill_distances()

    def remove_distance(self) -> None:
        if self.treeView.currentIndex().row() == 0:
            return

        index = self.treeView.currentIndex().row() + 1
        self._distances.pop(index)
        self.fill_distances()

    def fill_distances(self) -> None:
        self.treeView.clear()

        if self._distances:

            item = QTreeWidgetItem()
            item.setText(0, "Below {}".format(self._distances[0]))
            item.setText(1, str(self.default_sampling_size.distanceMeters()))

            self.treeView.addTopLevelItem(item)

        for distance in self._distances:

            item = QTreeWidgetItem()
            item.setText(0, "Over {}".format(distance))
            item.setData(0, Qt.UserRole, distance)
            size = round(
                (math.tan(math.radians(self.object_angle_size.value()))) * distance.meters(), 3)
            item.setText(1, str(size))

            self.treeView.addTopLevelItem(item)

        if self.use_maximal_los_length.isChecked() and self._distances:

            item = QTreeWidgetItem()
            item.setText(
                0, "Over {} to {}".format(self._distances[-1], self.maximal_los_length.distance()))
            item.setText(1, str(size))

            self.treeView.addTopLevelItem(item)

    def create_data_layer(self) -> QgsVectorLayer:
        size = None

        fields = QgsFields()
        fields.append(QgsField(FieldNames.SIZE_ANGLE, QVariant.Double))
        fields.append(QgsField(FieldNames.DISTANCE, QVariant.Double))
        fields.append(QgsField(FieldNames.SIZE, QVariant.Double))

        layer = QgsMemoryProviderUtils.createMemoryLayer("Sampling Table",
                                                         fields=fields,
                                                         geometryType=QgsWkbTypes.NoGeometry)

        angle = self.object_angle_size.value()

        f = QgsFeature(fields)
        f.setAttribute(f.fieldNameIndex(FieldNames.SIZE_ANGLE), angle)
        f.setAttribute(f.fieldNameIndex(FieldNames.DISTANCE), 0)
        f.setAttribute(f.fieldNameIndex(FieldNames.SIZE),
                       self.default_sampling_size.distanceMeters())
        layer.dataProvider().addFeature(f)

        for distance in self._distances:
            f = QgsFeature(fields)
            f.setAttribute(f.fieldNameIndex(FieldNames.SIZE_ANGLE), angle)
            f.setAttribute(f.fieldNameIndex(FieldNames.DISTANCE), distance.meters())
            size = math.tan(math.radians(self.object_angle_size.value())) * distance.meters()
            f.setAttribute(f.fieldNameIndex(FieldNames.SIZE), size)
            layer.dataProvider().addFeature(f)

        if size:
            f = QgsFeature(fields)
            f.setAttribute(f.fieldNameIndex(FieldNames.SIZE_ANGLE), angle)
            if self.use_maximal_los_length.isChecked():
                f.setAttribute(f.fieldNameIndex(FieldNames.DISTANCE),
                               self.maximal_los_length.distanceMeters())
            else:
                f.setAttribute(f.fieldNameIndex(FieldNames.DISTANCE), -1)
            f.setAttribute(f.fieldNameIndex(FieldNames.SIZE), size)
            layer.dataProvider().addFeature(f)

        return layer

    def add_layer_to_project(self) -> None:

        project = QgsProject.instance()
        project.addMapLayer(self.create_data_layer())

        self.close()


class Distance:

    def __init__(
            self,
            distance: float = 0,
            unit: QgsUnitTypes.DistanceUnit = QgsUnitTypes.DistanceUnit.DistanceMeters) -> None:
        self._distance: float = distance
        self._unit: QgsUnitTypes.DistanceUnit = unit

    def __str__(self) -> str:
        return "{} {}".format(self._distance, QgsUnitTypes.toString(self._unit))

    def __eq__(self, other) -> bool:
        return self._distance == other._distance and self._unit == other._unit

    def meters(self) -> float:
        conversion = QgsUnitTypes.fromUnitToUnitFactor(self._unit,
                                                       QgsUnitTypes.DistanceUnit.DistanceMeters)
        return self._distance * conversion

    def distance(self) -> float:
        return self._distance


class DistanceWidget(QWidget):

    valueChanged = pyqtSignal()

    def __init__(self,
                 parent: Optional['QWidget'] = None,
                 flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.Widget) -> None:
        super().__init__(parent, flags)

        self.init_gui()

    def init_gui(self) -> None:
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        self.distance_value = QDoubleSpinBox(self)
        self.distance_value.setMinimum(0.001)
        self.distance_value.setMaximum(999999999)
        self.distance_value.setValue(0)
        self.distance_value.valueChanged.connect(self._raiseValueChanged)

        self.units = QComboBox(self)
        self.units.addItem(QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceMeters),
                           QgsUnitTypes.DistanceUnit.DistanceMeters)
        self.units.addItem(QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceKilometers),
                           QgsUnitTypes.DistanceUnit.DistanceKilometers)
        self.units.addItem(QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceFeet),
                           QgsUnitTypes.DistanceUnit.DistanceFeet)
        self.units.addItem(QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceMiles),
                           QgsUnitTypes.DistanceUnit.DistanceMiles)
        self.units.addItem(QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceYards),
                           QgsUnitTypes.DistanceUnit.DistanceYards)
        self.units.currentIndexChanged.connect(self._raiseValueChanged)

        layout.addWidget(self.distance_value)
        layout.addWidget(self.units)

    def _raiseValueChanged(self):
        self.valueChanged.emit()

    def value(self) -> float:
        return self.distanceMeters()

    def setValue(self,
                 value: float,
                 unit: QgsUnitTypes.DistanceUnit = QgsUnitTypes.DistanceUnit.DistanceMeters):
        self.units.setCurrentText(QgsUnitTypes.toString(unit))
        self.distance_value.setValue(value)

    def distanceMeters(self) -> float:
        conversion = QgsUnitTypes.fromUnitToUnitFactor(self.units.currentData(Qt.UserRole),
                                                       QgsUnitTypes.DistanceUnit.DistanceMeters)
        return self.distance_value.value() * conversion

    def distance(self) -> Distance:
        return Distance(self.distance_value.value(), self.units.currentData(Qt.UserRole))
