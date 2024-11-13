# pylint: disable=protected-access
import typing

from qgis.core import Qgis, QgsPointXY, QgsProject, QgsRasterLayer, QgsVectorLayer
from qgis.gui import QgisInterface, QgsMapCanvas

from los_tools.gui.optimize_point_location_tool.optimize_points_location_tool import OptimizePointsLocationTool
from tests.utils import create_mouse_event


def test_tool_activation_errors(
    qgis_iface: QgisInterface,
    raster_small: QgsRasterLayer,
    qgis_canvas: QgsMapCanvas,
    layer_points: QgsVectorLayer,
    layer_points_wgs84: QgsVectorLayer,
    horizon_line_global: QgsVectorLayer,
    mock_add_message_to_messagebar: typing.Callable,
):
    project = QgsProject.instance()
    project.addMapLayer(raster_small)
    project.addMapLayer(layer_points)

    qgis_canvas.setLayers([raster_small, layer_points, layer_points_wgs84])

    map_tool = OptimizePointsLocationTool(qgis_canvas, qgis_iface)
    # add mocked function to pass messages to message bar
    map_tool.messageEmitted.connect(mock_add_message_to_messagebar)

    # no layer activated
    map_tool.activate()
    messages = qgis_iface.messageBar().get_messages(Qgis.MessageLevel.Critical)
    assert len(messages) == 1
    assert "Tool only works with vector layers. Current layer is not vector layer." in messages[0]

    # set active layer to vector in geographic coordinates
    qgis_canvas.setCurrentLayer(layer_points_wgs84)
    map_tool.activate()
    messages = qgis_iface.messageBar().get_messages(Qgis.MessageLevel.Critical)
    assert len(messages) == 2
    assert "Tool only works for layers with projected CRS. Current layer has geographic crs." in messages[1]

    # set active layer to raster
    qgis_canvas.setCurrentLayer(raster_small)
    map_tool.activate()
    messages = qgis_iface.messageBar().get_messages(Qgis.MessageLevel.Critical)
    assert len(messages) == 3
    assert "Tool only works with vector layers. Current layer is not vector layer." in messages[2]

    # set active layer to vector
    qgis_canvas.setCurrentLayer(layer_points)
    map_tool.activate()
    messages = qgis_iface.messageBar().get_messages(Qgis.MessageLevel.Critical)
    assert len(messages) == 4
    assert "Layer must be in editing mode." in messages[3]

    # set active layer to vector with lines
    qgis_canvas.setCurrentLayer(horizon_line_global)
    map_tool.activate()
    messages = qgis_iface.messageBar().get_messages(Qgis.MessageLevel.Critical)
    assert len(messages) == 5
    assert "Tool only works for point layers." in messages[4]


def test_tool_activation(
    qgis_iface: QgisInterface,
    raster_small: QgsRasterLayer,
    qgis_canvas: QgsMapCanvas,
    layer_points: QgsVectorLayer,
    mock_add_message_to_messagebar: typing.Callable,
):
    project = QgsProject.instance()
    project.addMapLayer(raster_small)
    project.addMapLayer(layer_points)

    qgis_canvas.setLayers([raster_small, layer_points])
    qgis_canvas.setCurrentLayer(layer_points)
    qgis_canvas.mapSettings().setDestinationCrs(layer_points.crs())
    qgis_canvas.setExtent(raster_small.extent())

    layer_points.startEditing()

    map_tool = OptimizePointsLocationTool(qgis_canvas, qgis_iface)
    # add mocked function to pass messages to message bar
    map_tool.messageEmitted.connect(mock_add_message_to_messagebar)

    map_tool.activate()

    point_existing = QgsPointXY(-336475.126, -1189064.361)
    point_not_existing = QgsPointXY(-336734.28, -1189265.50)

    assert map_tool._raster is not None

    messages = qgis_iface.messageBar().get_messages(Qgis.MessageLevel.Critical)
    assert len(messages) == 0

    assert map_tool.circle_rubber.size() == 0
    assert map_tool.point_rubber.size() == 0
    assert map_tool._point is None
    assert map_tool._pointId is None
    assert map_tool._candidate_point is None

    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, point_existing))

    assert map_tool.circle_rubber.size() == 1
    assert map_tool.point_rubber.size() == 1
    assert map_tool._point is not None
    assert map_tool._pointId is not None
    assert map_tool._candidate_point is not None
    assert map_tool._candidate_point == QgsPointXY(-336473.14529999997466803, -1189072.61889999988488853)

    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, point_not_existing))

    assert map_tool.circle_rubber.size() == 0
    assert map_tool.point_rubber.size() == 0
    assert map_tool._point is None
    assert map_tool._pointId is None
    assert map_tool._candidate_point is None

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point_existing))

    layer_points.rollBack()
