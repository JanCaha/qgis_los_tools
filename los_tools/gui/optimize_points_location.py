from typing import Optional

from qgis.PyQt.QtWidgets import (QWidget, QFormLayout)
from qgis.PyQt.QtCore import (Qt, pyqtSignal)
from qgis.PyQt.QtGui import (QColor)
from qgis.core import (QgsPointXY, QgsWkbTypes, QgsGeometry, QgsPoint, QgsPointLocator, Qgis,
                       QgsVectorDataProvider, QgsSnappingConfig, QgsTolerance, QgsCircle,
                       QgsRasterLayer, QgsMapLayerProxyModel, QgsUnitTypes, QgsRectangle)
from qgis.gui import (QgisInterface, QgsMapToolEdit, QgsDoubleSpinBox, QgsRubberBand,
                      QgsMapMouseEvent, QgsMapCanvas, QgsMapLayerComboBox, QgsSnapIndicator)

from .utils import prepare_user_input_widget
from ..create_points.tool_optimize_point_location import OptimizePointLocationAlgorithm


class OptimizePointsLocationTool(QgsMapToolEdit):

    def __init__(self, canvas: QgsMapCanvas, iface: QgisInterface) -> None:
        super().__init__(canvas)
        self._canvas = canvas

        self.snap_marker = QgsSnapIndicator(self._canvas)

        self.circle_rubber = QgsRubberBand(self._canvas, QgsWkbTypes.PolygonGeometry)
        self.circle_rubber.setColor(QColor.fromRgb(255, 64, 64))
        self.circle_rubber.setWidth(2)
        self.circle_rubber.setOpacity(0.5)

        self.point_rubber = QgsRubberBand(self._canvas, QgsWkbTypes.PointGeometry)
        self.point_rubber.setColor(QColor.fromRgb(64, 64, 255))
        self.point_rubber.setWidth(2)
        self.point_rubber.setOpacity(0.5)
        self.point_rubber.setIconSize(10)

        self._circle_radius = 10.0
        self._raster: QgsRasterLayer = None
        self._distance_unit: QgsUnitTypes = None
        self._raster_extent: QgsRectangle = None
        self._cell_size: float = None
        self._distance_cells: int = None
        self._no_data_value: float = None

        self._point: QgsPointXY = None
        self._pointId: int = None
        self._candidate_point: QgsPointXY = None

        self.floating_widget = OptimizePointLocationInputWidget()
        self.floating_widget.hide()
        self.floating_widget.valuesChanged.connect(self.set_values_from_widget)

        self.user_input_widget = prepare_user_input_widget(self._canvas, self.floating_widget)

    def set_values_from_widget(self) -> None:
        self._circle_radius = self.floating_widget.distance
        if self.floating_widget.raster_layer:
            self._raster = self.floating_widget.raster_layer.dataProvider()
            self._raster_extent = self._raster.extent()
            self._cell_size = self._raster_extent.width() / self._raster.xSize()
            self._distance_cells = int(self._circle_radius / self._cell_size)
            self._no_data_value = self._raster.sourceNoDataValue(1)

    def activate(self) -> None:
        self.floating_widget.show()
        self.user_input_widget.show()
        self.messageDiscarded.emit()
        if self.currentVectorLayer() is None:
            self.messageEmitted.emit(
                "Tool only works with vector layers. Current layer is not vector layer.",
                Qgis.Critical)
            self._canvas.unsetMapTool(self)
            return
        if self.currentVectorLayer().crs().isGeographic():
            self.messageEmitted.emit(
                "Tool only works for layers with projected CRS. Current layer has geographic crs",
                Qgis.Critical)
            self._canvas.unsetMapTool(self)
            return
        if self.currentVectorLayer().dataProvider().capabilities(
        ) & QgsVectorDataProvider.ChangeFeatures:
            self.messageEmitted.emit(
                "Tool only works for layers where features can be edited. Current layer features cannot be edited.",
                Qgis.Critical)
            self._canvas.unsetMapTool(self)
            return
        if self.currentVectorLayer().geometryType() not in [
                QgsWkbTypes.Point, QgsWkbTypes.Point25D, QgsWkbTypes.PointM, QgsWkbTypes.PointZ,
                QgsWkbTypes.PointZM, QgsWkbTypes.PointGeometry
        ]:
            self.messageEmitted.emit(
                "Tool only works for point layers. Current layer is {}.".format(
                    QgsWkbTypes.geometryDisplayString(self.currentVectorLayer().geometryType())),
                Qgis.Critical)
            self._canvas.unsetMapTool(self)
            return
        if not self.currentVectorLayer().isEditable():
            self.messageEmitted.emit("Layer must be in editing mode.", Qgis.Critical)
            self._canvas.unsetMapTool(self)
            return
        self._distance_unit = self.currentVectorLayer().crs().mapUnits()
        self.floating_widget.set_units(self._distance_unit)
        return super().activate()

    def clean(self) -> None:
        self.circle_rubber.hide()
        self.point_rubber.hide()
        self._point = None
        self._pointId = None
        self._candidate_point = None
        self.snap_marker.setVisible(False)
        return super().clean()

    def deactivate(self) -> None:
        self.clean()
        self.floating_widget.hide()
        self.user_input_widget.hide()
        return super().deactivate()

    def draw_rubber_bands(self, point: QgsPointXY = None) -> None:
        if point:
            circle = QgsCircle(QgsPoint(point.x(), point.y()), self._circle_radius)
            self.circle_rubber.setToGeometry(QgsGeometry(circle.toPolygon(segments=36 * 2)),
                                             self.currentVectorLayer())
            self._candidate_point = OptimizePointLocationAlgorithm.optimized_point(
                point, self._raster, self._raster_extent, self._cell_size, self._no_data_value,
                self._distance_cells)
            self.point_rubber.setToGeometry(QgsGeometry.fromPointXY(self._candidate_point))
            self.circle_rubber.show()
            self.point_rubber.show()
        else:
            self.circle_rubber.hide()
            self.point_rubber.hide()
            self._candidate_point = None

    def _snap(self, point: QgsPointXY) -> Optional[QgsPointLocator.Match]:

        utils = self._canvas.snappingUtils()
        oldConfig = utils.config()

        config = QgsSnappingConfig(oldConfig)
        config.setEnabled(True)
        config.setMode(QgsSnappingConfig.AdvancedConfiguration)
        config.setIntersectionSnapping(False)
        config.clearIndividualLayerSettings()

        layerSettings = QgsSnappingConfig.IndividualLayerSettings()
        layerSettings.setEnabled(True)
        layerSettings.setTypeFlag(Qgis.SnappingTypes(Qgis.SnappingType.Vertex))
        layerSettings.setTolerance(20)
        layerSettings.setUnits(QgsTolerance.Pixels)

        config.setIndividualLayerSettings(self.currentVectorLayer(), layerSettings)
        utils.setConfig(config)

        match = utils.snapToMap(point)
        utils.setConfig(oldConfig)

        self.snap_marker.setMatch(match)

        if match.isValid():
            return match
        else:
            return None

    def canvasMoveEvent(self, e: QgsMapMouseEvent) -> None:
        match = self._snap(e.mapPoint())
        if match:
            self._point = match.point()
            self._pointId = match.featureId()
            self.draw_rubber_bands(self._point)
        else:
            self.clean()
        return super().canvasMoveEvent(e)

    def canvasReleaseEvent(self, e: QgsMapMouseEvent) -> None:
        if e.button() == Qt.RightButton:
            self.deactivate()
        if self._point and self._pointId and self._candidate_point:
            self.currentVectorLayer().beginEditCommand("Optimize Point Location")
            self.currentVectorLayer().changeGeometry(
                self._pointId, QgsGeometry.fromPointXY(self._candidate_point))
            self.currentVectorLayer().endEditCommand()
            self.currentVectorLayer().triggerRepaint()
            # self.currentVectorLayer().reload()
            self.clean()
        return super().canvasReleaseEvent(e)


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
        self._distance.setSuffix(" {}".format(QgsUnitTypes.toString(unit)))

    @property
    def raster_layer(self) -> QgsRasterLayer:
        return self._layer.currentLayer()

    @property
    def distance(self) -> float:
        return self._distance.value()
