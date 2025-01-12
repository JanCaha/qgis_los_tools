import math
from typing import List, Optional, Union

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsMemoryProviderUtils,
    QgsProject,
    QgsUnitTypes,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QTextBrowser,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from los_tools.classes.sampling_distance_matrix import SamplingDistanceMatrix
from los_tools.constants.field_names import FieldNames
from los_tools.gui.custom_classes import Distance, DistanceWidget
from los_tools.utils import _column_type_class


class LoSSettings(QDialog):

    samplingDistanceMatrixUpdated = pyqtSignal(SamplingDistanceMatrix)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.Dialog,
    ) -> None:
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
        self.object_size.setClearValue(1)
        self.object_size.valueChanged.connect(self._calculate_object_angle_size)

        self.object_distance = DistanceWidget()
        self.object_distance.setValue(1000)
        self.object_distance.setClearValue(1000)
        self.object_distance.valueChanged.connect(self._calculate_object_angle_size)

        self.angle_size_manually = QCheckBox()
        self.angle_size_manually.stateChanged.connect(self._change_object_size_manual)
        self.angle_size_manually.stateChanged.connect(self.description_text)

        self.object_angle_size = QDoubleSpinBox()
        self.object_angle_size.setDecimals(3)
        self.object_angle_size.setReadOnly(True)
        self.object_angle_size.setSuffix("°")
        self.object_angle_size.setMinimum(0.001)
        self.object_angle_size.setSingleStep(0.01)

        self.object_angle_size.valueChanged.connect(self.fill_distances)
        self.object_angle_size.valueChanged.connect(self.description_text)

        layout_group_box_object.addRow("Object Size", self.object_size)
        layout_group_box_object.addRow("Object Distance", self.object_distance)
        layout_group_box_object.addRow("Specify Object Size Manually", self.angle_size_manually)
        layout_group_box_object.addRow("Object Angle Size", self.object_angle_size)

        self.text = QTextBrowser(self)
        self.text.setReadOnly(True)
        self.text.setMinimumHeight(200)
        self.description_text()

        group_box_los = QGroupBox("LoS settings", self)
        layout_group_box_los = QFormLayout()
        group_box_los.setLayout(layout_group_box_los)

        self.default_sampling_size = DistanceWidget()
        self.default_sampling_size.setValue(1)
        self.default_sampling_size.valueChanged.connect(self.fill_distances)

        self.maximal_los_length = DistanceWidget()
        self.maximal_los_length.setValue(100, QgsUnitTypes.DistanceKilometers)
        self.maximal_los_length.valueChanged.connect(self.fill_distances)
        self.maximal_los_length.setDisabled(True)

        self.use_maximal_los_length = QCheckBox()
        self.use_maximal_los_length.toggled.connect(self.fill_distances)

        layout_group_box_los.addRow("Default Sampling Size", self.default_sampling_size)
        layout_group_box_los.addRow("Use Maximal LoS Length", self.use_maximal_los_length)
        layout_group_box_los.addRow("Maximal LoS Length", self.maximal_los_length)

        self.distance = DistanceWidget()
        self.distance.setValue(1, QgsUnitTypes.DistanceKilometers)

        lineLayout = QHBoxLayout()

        self.toolButton_add = QToolButton()
        self.toolButton_remove = QToolButton()
        self.toolButton_add.setIcon(QgsApplication.getThemeIcon("/symbologyAdd.svg"))
        self.toolButton_remove.setIcon(QgsApplication.getThemeIcon("/symbologyRemove.svg"))
        self.toolButton_add.clicked.connect(self.add_distance)
        self.toolButton_remove.clicked.connect(self.remove_distance)

        lineLayout.addStretch(1)
        lineLayout.addWidget(self.toolButton_add)
        lineLayout.addWidget(self.toolButton_remove)

        self.treeView = QTreeWidget(self)
        self.treeView.setHeaderLabels(["Distance", "Sampling Size"])

        self.data_unit = QComboBox(self)
        self.data_unit.addItem(
            QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceMeters),
            QgsUnitTypes.DistanceUnit.DistanceMeters,
        )
        self.data_unit.addItem(
            QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceKilometers),
            QgsUnitTypes.DistanceUnit.DistanceKilometers,
        )
        self.data_unit.addItem(
            QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceFeet),
            QgsUnitTypes.DistanceUnit.DistanceFeet,
        )
        self.data_unit.addItem(
            QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceMiles),
            QgsUnitTypes.DistanceUnit.DistanceMiles,
        )
        self.data_unit.addItem(
            QgsUnitTypes.toString(QgsUnitTypes.DistanceUnit.DistanceYards),
            QgsUnitTypes.DistanceUnit.DistanceYards,
        )
        self.data_unit.currentIndexChanged.connect(self.fill_distances)

        self.button_add_layer = QPushButton("Add layer to project")
        self.button_add_layer.clicked.connect(self.add_layer_to_project)

        layout.addRow(group_box_object)
        layout.addRow(self.text)
        layout.addRow(group_box_los)
        layout.addRow("Distance Add", self.distance)
        layout.addRow(lineLayout)
        layout.addRow(self.treeView)
        layout.addRow("Layer units", self.data_unit)
        layout.addRow(self.button_add_layer)

    def description_text(self) -> None:
        if self.angle_size_manually.isChecked():
            text = [f"Angular sampling manually set to {round(self.object_angle_size.value(), 3)}°.\n\n"]
        else:
            text = [
                f" To detect an object of {self.object_size.distance()} in size "
                f"at a distance of {self.object_distance.distance()}, "
                f"an angular sampling of {round(self.object_angle_size.value(), 3)}° is required.\n\n"
                "This angular sampling of lines-of-sight ensures that the object will be intersected at least once."
                "\n\n",
            ]
        text += [
            "To simplify the calculation process, sampling frequency can be adjusted along each line-of-sight. "
            "As the distance from the observer increases, the sampling frequency can be reduced.",
            ".\n\n",
            "The calculation of sampling distances for various ranges can be performed below.\n\n",
            "The default sampling size is applied for distances shorter than the first specified distance. ",
            "Beyond each specified distance threshold, the calculated sampling distance is used.",
        ]

        self.text.setText("".join(text))

    def _calculate_object_angle_size(self) -> None:
        distance = self.object_distance.value()
        if 0 < distance:
            self.object_angle_size.setValue(math.degrees(math.atan(self.object_size.value() / distance)))
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

        index = self.treeView.currentIndex().row() - 1
        self._distances.pop(index)
        self.fill_distances()

    def fill_distances(self) -> None:
        self.maximal_los_length.setDisabled(not self.use_maximal_los_length.isChecked())

        self.treeView.clear()

        result_unit = self.data_unit.currentData(Qt.UserRole)

        if self._distances:
            item = QTreeWidgetItem()
            item.setText(0, "Below {}".format(self._distances[0]))
            item.setText(
                1,
                str(round(self.default_sampling_size.distance().inUnits(result_unit), 3)),
            )

            self.treeView.addTopLevelItem(item)

        if self.use_maximal_los_length.isChecked() and self._distances:
            self._distances = [
                x
                for x in self._distances
                if x.inUnits(result_unit) < self.maximal_los_length.distance().inUnits(result_unit)
            ]

        for distance in self._distances:
            item = QTreeWidgetItem()
            item.setText(0, f"Over {distance}")
            item.setData(0, Qt.UserRole, distance)
            size_units = self.calculate_size(self.object_angle_size.value(), distance)
            size = round(size_units.inUnits(result_unit), 3)
            item.setText(1, str(size))

            self.treeView.addTopLevelItem(item)

        if self.use_maximal_los_length.isChecked() and self._distances:
            item = QTreeWidgetItem()
            item.setText(
                0,
                f"Over {self._distances[-1]} to {self.maximal_los_length.distance()}",
            )
            item.setText(1, str(size))

            self.treeView.addTopLevelItem(item)

        layer = self.create_data_layer()
        self.samplingDistanceMatrixUpdated.emit(SamplingDistanceMatrix(layer))

    def calculate_size(self, angle: float, distance: Distance) -> Distance:
        size = math.tan(math.radians(angle)) * distance.distance()
        return Distance(size, distance.unit())

    def create_data_layer(self) -> QgsVectorLayer:
        unit = self.data_unit.currentData(Qt.UserRole)
        unit_name = QgsUnitTypes.toString(unit)

        distance_field_name = FieldNames.TEMPLATE_DISTANCE.replace("?", unit_name)
        size_field_name = FieldNames.TEMPLATE_SIZE.replace("?", unit_name)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.SIZE_ANGLE, _column_type_class().Double))
        fields.append(QgsField(distance_field_name, _column_type_class().Double))
        fields.append(QgsField(size_field_name, _column_type_class().Double))

        layer = QgsMemoryProviderUtils.createMemoryLayer(
            "Sampling Table", fields=fields, geometryType=Qgis.WkbType.NoGeometry
        )

        angle = self.object_angle_size.value()

        distance_index = fields.indexOf(distance_field_name)
        size_index = fields.indexOf(size_field_name)
        angle_index = fields.indexOf(FieldNames.SIZE_ANGLE)

        f = QgsFeature(fields)
        f.setAttribute(angle_index, angle)
        f.setAttribute(distance_index, 0)
        f.setAttribute(size_index, self.default_sampling_size.distance().inUnits(unit))
        layer.dataProvider().addFeature(f)

        size = self.default_sampling_size.distance().inUnits(unit)

        for distance in self._distances:
            f = QgsFeature(fields)
            f.setAttribute(angle_index, angle)
            f.setAttribute(distance_index, distance.inUnits(unit))
            size_units = self.calculate_size(self.object_angle_size.value(), distance)
            size = size_units.inUnits(unit)
            f.setAttribute(size_index, size)
            layer.dataProvider().addFeature(f)

        if size:
            f = QgsFeature(fields)
            f.setAttribute(angle_index, angle)
            if self.use_maximal_los_length.isChecked():
                f.setAttribute(distance_index, self.maximal_los_length.distance().inUnits(unit))
            else:
                f.setAttribute(distance_index, -1)
            f.setAttribute(size_index, size)
            layer.dataProvider().addFeature(f)

        return layer

    def add_layer_to_project(self) -> None:
        project = QgsProject.instance()
        project.addMapLayer(self.create_data_layer())

        self.close()

    def los_maximal_length(self) -> Optional[Distance]:
        if self.use_maximal_los_length.isChecked():
            return self.maximal_los_length.distance()
        else:
            return None

    def _change_object_size_manual(self):
        manual = self.angle_size_manually.isChecked()
        self.object_size.setEnabled(not manual)
        self.object_distance.setEnabled(not manual)
        self.object_angle_size.setReadOnly(not manual)
        if not manual:
            self._calculate_object_angle_size()
