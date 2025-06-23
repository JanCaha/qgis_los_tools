import typing
from typing import Optional

from qgis.core import (
    Qgis,
    QgsCircle,
    QgsGeometry,
    QgsPoint,
    QgsPointLocator,
    QgsPointXY,
    QgsRasterLayer,
    QgsRectangle,
    QgsSnappingConfig,
    QgsUnitTypes,
    QgsVectorDataProvider,
    QgsWkbTypes,
)
from qgis.gui import QgisInterface, QgsMapCanvas, QgsMapMouseEvent, QgsMapToolEdit, QgsRubberBand, QgsSnapIndicator
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QWidget

from los_tools.gui.optimize_point_location_tool.optimize_points_location_widget import OptimizePointLocationInputWidget
from los_tools.processing.create_points.tool_optimize_point_location import OptimizePointLocationAlgorithm


class OptimizePointsLocationTool(QgsMapToolEdit):
    def __init__(self, canvas: QgsMapCanvas, iface: QgisInterface) -> None:
        super().__init__(canvas)
        self._canvas = canvas
        self._iface = iface

        self.snap_marker = QgsSnapIndicator(self._canvas)

        self.circle_rubber = QgsRubberBand(self._canvas, Qgis.GeometryType.Polygon)
        self.circle_rubber.setColor(QColor.fromRgb(255, 64, 64))
        self.circle_rubber.setWidth(2)
        self.circle_rubber.setOpacity(0.3)

        self.point_rubber = QgsRubberBand(self._canvas, Qgis.GeometryType.Point)
        self.point_rubber.setColor(QColor.fromRgb(64, 64, 255))
        self.point_rubber.setWidth(2)
        self.point_rubber.setOpacity(0.75)
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

        self._widget: QWidget = None

    def create_widget(self):
        self.delete_widget()

        self._widget = OptimizePointLocationInputWidget()
        self._iface.addUserInputWidget(self._widget)
        self._widget.setFocus(Qt.FocusReason.TabFocusReason)

        self._widget.valuesChanged.connect(self.set_values_from_widget)
        self.set_values_from_widget()

    def delete_widget(self):
        if self._widget:
            self._widget.releaseKeyboard()
            self._widget.deleteLater()
            self._widget = None

    def set_values_from_widget(self) -> None:
        self._circle_radius = self._widget.distance
        if self._widget.raster_layer:
            self._raster = self._widget.raster_layer.dataProvider()
            self._raster_extent = self._raster.extent()
            self._cell_size = self._raster_extent.width() / self._raster.xSize()
            self._distance_cells = int(self._circle_radius / self._cell_size)
            self._no_data_value = self._raster.sourceNoDataValue(1)

    def activate(self) -> None:
        super(OptimizePointsLocationTool, self).activate()
        self.create_widget()
        self.messageDiscarded.emit()
        if self.currentVectorLayer() is None:
            self.messageEmitted.emit(
                "Tool only works with vector layers. Current layer is not vector layer.",
                Qgis.MessageLevel.Critical,
            )
            self._canvas.unsetMapTool(self)
            return
        if self.currentVectorLayer().crs().isGeographic():
            self.messageEmitted.emit(
                "Tool only works for layers with projected CRS. Current layer has geographic crs.",
                Qgis.MessageLevel.Critical,
            )
            self._canvas.unsetMapTool(self)
            return
        if self.currentVectorLayer().dataProvider().capabilities() & QgsVectorDataProvider.Capability.ChangeFeatures:
            self.messageEmitted.emit(
                "Tool only works for layers where features can be edited. Current layer features cannot be edited.",
                Qgis.MessageLevel.Critical,
            )
            self._canvas.unsetMapTool(self)
            return
        if self.currentVectorLayer().wkbType() not in [
            Qgis.WkbType.Point,
            Qgis.WkbType.Point25D,
            Qgis.WkbType.PointM,
            Qgis.WkbType.PointZ,
            Qgis.WkbType.PointZM,
        ]:
            self.messageEmitted.emit(
                "Tool only works for point layers. Current layer is "
                f"{QgsWkbTypes.geometryDisplayString(self.currentVectorLayer().geometryType())}.",
                Qgis.MessageLevel.Critical,
            )
            self._canvas.unsetMapTool(self)
            return
        if not self.currentVectorLayer().isEditable():
            self.messageEmitted.emit("Layer must be in editing mode.", Qgis.MessageLevel.Critical)
            self._canvas.unsetMapTool(self)
            return
        self._distance_unit = self.currentVectorLayer().crs().mapUnits()
        self._widget.set_units(self._distance_unit)

    def clean(self) -> None:
        self._point = None
        self._pointId = None
        self._candidate_point = None
        self.snap_marker.setVisible(False)
        self.point_rubber.hide()
        self.point_rubber.reset()
        self.circle_rubber.hide()
        self.circle_rubber.reset()
        return super().clean()

    def deactivate(self) -> None:
        self.clean()
        self.delete_widget()
        super(OptimizePointsLocationTool, self).deactivate()

    def get_candidate_point(self, point: typing.Optional[QgsPointXY] = None) -> None:
        if point:
            self._candidate_point = OptimizePointLocationAlgorithm.optimized_point(
                point,
                self._raster,
                self._raster_extent,
                self._cell_size,
                self._no_data_value,
                self._distance_cells,
            )
        else:
            self._candidate_point = None

    def draw_rubber_bands(self, point: typing.Optional[QgsPointXY] = None) -> None:
        if point:
            circle = QgsCircle(QgsPoint(point.x(), point.y()), self._circle_radius)
            self.circle_rubber.setToGeometry(
                QgsGeometry(circle.toPolygon(segments=36 * 2)),
                self.currentVectorLayer(),
            )
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
        config.setMode(Qgis.SnappingMode.AdvancedConfiguration)
        config.setIntersectionSnapping(False)
        config.clearIndividualLayerSettings()

        layerSettings = QgsSnappingConfig.IndividualLayerSettings()
        layerSettings.setEnabled(True)
        layerSettings.setTypeFlag(Qgis.SnappingTypes(Qgis.SnappingType.Vertex))
        layerSettings.setTolerance(20)
        layerSettings.setUnits(Qgis.MapToolUnit.Pixels)

        config.setIndividualLayerSettings(self.currentVectorLayer(), layerSettings)
        utils.setConfig(config)

        match = utils.snapToMap(point)
        utils.setConfig(oldConfig)

        self.snap_marker.setMatch(match)

        if match.isValid():
            return match
        else:
            return None

    def canvasMoveEvent(self, e: typing.Optional[QgsMapMouseEvent]) -> None:
        match = self._snap(e.mapPoint())
        if match:
            self._point = match.point()
            self._pointId = match.featureId()
            self.get_candidate_point(self._point)
            self.draw_rubber_bands(self._point)
        else:
            self.clean()
        return super().canvasMoveEvent(e)

    def canvasReleaseEvent(self, e: typing.Optional[QgsMapMouseEvent]) -> None:
        if e.button() == Qt.MouseButton.RightButton:
            self.deactivate()
        if self._point and self._pointId and self._candidate_point:
            self.currentVectorLayer().beginEditCommand("Optimize Point Location")
            self.currentVectorLayer().changeGeometry(self._pointId, QgsGeometry.fromPointXY(self._candidate_point))
            self.currentVectorLayer().endEditCommand()
            self.currentVectorLayer().triggerRepaint()
            self.clean()
        return super().canvasReleaseEvent(e)
