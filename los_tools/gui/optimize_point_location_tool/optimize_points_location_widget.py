from typing import Optional

from qgis.core import QgsMapLayerProxyModel, QgsRasterLayer, QgsUnitTypes
from qgis.gui import QgsDoubleSpinBox, QgsMapLayerComboBox
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QFormLayout, QWidget


class OptimizePointLocationInputWidget(QWidget):
    valuesChanged = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QFormLayout()
        self.setLayout(layout)

        self._layer = QgsMapLayerComboBox(self)
        self._layer.setFilters(QgsMapLayerProxyModel.Filter.RasterLayer)
        self._layer.layerChanged.connect(self.emit_values_changed)
        self._distance = QgsDoubleSpinBox(self)
        self._distance.setMinimum(0)
        self._distance.setMaximum(9999999)
        self._distance.setValue(10)
        self._distance.setClearValue(10)
        self._distance.valueChanged.connect(self.emit_values_changed)

        layout.addRow("Layer", self._layer)
        layout.addRow("Search Distance", self._distance)

    def emit_values_changed(self) -> None:
        self.valuesChanged.emit()

    def show(self) -> None:
        self.valuesChanged.emit()
        return super().show()

    def set_units(self, unit: QgsUnitTypes) -> None:
        self._distance.setSuffix(f" {QgsUnitTypes.toString(unit)}")

    @property
    def raster_layer(self) -> QgsRasterLayer:
        return self._layer.currentLayer()

    @property
    def distance(self) -> float:
        return self._distance.value()
