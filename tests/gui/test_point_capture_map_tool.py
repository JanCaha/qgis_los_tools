# pylint: disable=protected-access
from pytestqt.qtbot import QtBot
from qgis.core import QgsPointXY, QgsVectorLayer
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtCore import QEvent

from los_tools.gui.tools.point_capture_map_tool import PointCaptureMapTool
from tests.utils import create_mouse_event, setup_project_with_snapping, setup_project_without_snapping


def test_point_capture_map_tool_no_snap(
    qgis_canvas: QgsMapCanvas,
    layer_polygons: QgsVectorLayer,
    qtbot: QtBot,
):

    setup_project_without_snapping(qgis_canvas, layer_polygons)

    map_tool = PointCaptureMapTool(qgis_canvas)

    point = QgsPointXY(-336433.464, -1189082.192)

    with qtbot.waitSignal(map_tool.canvasClicked, timeout=None, raising=True):
        map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, point, event_type=QEvent.Type.MouseMove))
        map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point))

    assert map_tool.get_point() == point
    assert map_tool.is_point_snapped() is False
    assert map_tool.snap_layer() == ""


def test_point_capture_map_tool_with_snap(
    qgis_canvas: QgsMapCanvas,
    layer_points: QgsVectorLayer,
    qtbot: QtBot,
):

    setup_project_with_snapping(qgis_canvas, layer_points, 15)

    map_tool = PointCaptureMapTool(qgis_canvas)

    layer_point = layer_points.getFeature(1).geometry().asPoint()
    assert layer_point

    offset_by = 5
    point = QgsPointXY(layer_point.x() - offset_by, layer_point.y() + offset_by)

    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, point, event_type=QEvent.Type.MouseMove))

    assert map_tool.get_point() == layer_point
    assert map_tool.get_point() != point

    with qtbot.waitSignal(map_tool.canvasClicked, timeout=None, raising=True):
        map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point))

    assert map_tool.is_point_snapped()
    assert map_tool.snap_layer() == layer_points.name()
    assert map_tool.get_point() == layer_point
