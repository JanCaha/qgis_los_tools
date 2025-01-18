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
    layer_polygons: QgsVectorLayer,
    qtbot: QtBot,
):

    setup_project_with_snapping(qgis_canvas, layer_polygons)

    map_tool = PointCaptureMapTool(qgis_canvas)

    point = QgsPointXY(-336433.464, -1189082.192)

    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, point, event_type=QEvent.Type.MouseMove))

    assert map_tool.get_point() == QgsPointXY(-336430.54888639913406223, -1189081.19254285283386707)

    with qtbot.waitSignal(map_tool.canvasClicked, timeout=None, raising=True):
        map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point))

    assert map_tool.is_point_snapped()
    assert map_tool.snap_layer() == layer_polygons.name()
    assert map_tool.get_point() == QgsPointXY(-336430.54888639913406223, -1189081.19254285283386707)
