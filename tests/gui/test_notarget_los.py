# pylint: disable=protected-access
from pytestqt.qtbot import QtBot
from qgis.core import QgsPointXY, QgsVectorLayer
from qgis.gui import QgisInterface, QgsMapCanvas
from qgis.PyQt.QtCore import QEvent

from los_tools.classes.list_raster import ListOfRasters
from los_tools.classes.sampling_distance_matrix import SamplingDistanceMatrix
from los_tools.gui.los_without_target_visualization.los_without_target import LosNoTargetMapTool
from tests.utils import create_mouse_event, setup_project_with_snapping


def test_notarget_los_tool_point_definition(
    qgis_iface: QgisInterface,
    los_layer: QgsVectorLayer,
    list_of_rasters: ListOfRasters,
    sampling_distance_matrix: SamplingDistanceMatrix,
    layer_points: QgsVectorLayer,
    qgis_canvas: QgsMapCanvas,
):

    setup_project_with_snapping(qgis_canvas, layer_points)

    map_tool = LosNoTargetMapTool(qgis_iface, list_of_rasters, sampling_distance_matrix, los_layer)
    # set angle setup
    map_tool._widget._tabs.setCurrentIndex(0)

    map_tool.activate()

    assert map_tool._snap_point is None

    point = QgsPointXY(-336366.19582480326062068, -1189110.65821624454110861)

    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, point, event_type=QEvent.Type.MouseMove))

    assert map_tool._snap_point == point
    assert map_tool._los_rubber_band.size() == 0

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point))

    assert map_tool._start_point
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    assert map_tool._los_rubber_band.size() == 360

    map_tool._widget._min_angle.setValue(90)
    map_tool._widget._max_angle.setValue(270)

    point = QgsPointXY(-336408.92, -1189142.77)

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point, event_type=QEvent.Type.MouseMove))

    assert map_tool._start_point
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    assert map_tool._snap_point != point
    assert map_tool._snap_point == QgsPointXY(-336366.19582480326062068, -1189110.65821624454110861)

    assert map_tool._los_rubber_band.size() == 181


def test_notarget_los_tool_direction_defition(
    qgis_iface: QgisInterface,
    los_layer: QgsVectorLayer,
    list_of_rasters: ListOfRasters,
    sampling_distance_matrix: SamplingDistanceMatrix,
    layer_points: QgsVectorLayer,
    qgis_canvas: QgsMapCanvas,
):

    setup_project_with_snapping(qgis_canvas, layer_points)

    map_tool = LosNoTargetMapTool(qgis_iface, list_of_rasters, sampling_distance_matrix, los_layer)

    # set angle setup
    map_tool.clean()
    map_tool._widget._tabs.setCurrentIndex(1)
    map_tool._widget._angle_step.setValue(1)
    map_tool._widget._angle_width.setValue(20)

    map_tool.activate()

    assert map_tool._snap_point is None

    point = QgsPointXY(-336366.19582480326062068, -1189110.65821624454110861)

    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, point, event_type=QEvent.Type.MouseMove))

    assert map_tool._snap_point == point
    assert map_tool._los_rubber_band.size() == 0
    assert map_tool._distance_limits_rubber_band.size() == 0

    assert map_tool._start_point is None
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point))

    assert map_tool._start_point
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point.project(10, 90)))

    assert map_tool._start_point
    assert map_tool._end_point
    assert map_tool._direction_point is None

    assert map_tool._los_rubber_band.size() == 21
    assert map_tool._distance_limits_rubber_band.size() == 0

    # set widget
    map_tool.clean()
    map_tool._widget._tabs.setCurrentIndex(1)
    map_tool._widget._angle_width.setValue(90)

    point = QgsPointXY(-336408.92, -1189142.77)

    assert map_tool._start_point is None
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point, event_type=QEvent.Type.MouseMove))

    assert map_tool._start_point
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point.project(10, 90)))

    assert map_tool._start_point
    assert map_tool._end_point
    assert map_tool._direction_point is None

    assert map_tool._los_rubber_band.size() == 91
    assert map_tool._distance_limits_rubber_band.size() == 0

    # set widget
    map_tool.clean()
    map_tool._widget._tabs.setCurrentIndex(1)
    map_tool._widget._angle_step.setValue(2)
    map_tool._widget._angle_width.setValue(90)

    point = QgsPointXY(-336408.92, -1189142.77)

    assert map_tool._start_point is None
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point, event_type=QEvent.Type.MouseMove))

    assert map_tool._start_point
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point.project(10, 180)))

    assert map_tool._start_point
    assert map_tool._end_point
    assert map_tool._direction_point is None

    assert map_tool._los_rubber_band.size() == 46
    assert map_tool._distance_limits_rubber_band.size() == 0


def test_notarget_los_tool_direction_defition_with_limits(
    qgis_iface: QgisInterface,
    los_layer: QgsVectorLayer,
    list_of_rasters: ListOfRasters,
    sampling_distance_matrix: SamplingDistanceMatrix,
    layer_points: QgsVectorLayer,
    qgis_canvas: QgsMapCanvas,
):

    setup_project_with_snapping(qgis_canvas, layer_points)

    map_tool = LosNoTargetMapTool(qgis_iface, list_of_rasters, sampling_distance_matrix, los_layer)

    # set angle setup
    map_tool.clean()
    map_tool._widget._tabs.setCurrentIndex(1)
    map_tool._widget._angle_step.setValue(1)
    map_tool._widget._angle_width.setValue(20)
    map_tool._widget._show_distances.setChecked(True)
    map_tool._widget._distances.set_distances([1, 5, 10, 50])

    map_tool.activate()

    assert map_tool._snap_point is None

    point = QgsPointXY(-336366.19582480326062068, -1189110.65821624454110861)

    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, point, event_type=QEvent.Type.MouseMove))

    assert map_tool._snap_point == point
    assert map_tool._los_rubber_band.size() == 0
    assert map_tool._distance_limits_rubber_band.size() == 0

    assert map_tool._start_point is None
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point))

    assert map_tool._start_point
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point.project(10, 90)))

    assert map_tool._start_point
    assert map_tool._end_point
    assert map_tool._direction_point is None

    assert map_tool._los_rubber_band.size() == 21
    assert map_tool._distance_limits_rubber_band.size() == 4


def test_notarget_los_tool_add_los_to_layer(
    qgis_iface: QgisInterface,
    los_layer: QgsVectorLayer,
    list_of_rasters: ListOfRasters,
    sampling_distance_matrix: SamplingDistanceMatrix,
    layer_points: QgsVectorLayer,
    qgis_canvas: QgsMapCanvas,
    qtbot: QtBot,
):

    setup_project_with_snapping(qgis_canvas, layer_points)

    map_tool = LosNoTargetMapTool(qgis_iface, list_of_rasters, sampling_distance_matrix, los_layer)

    # set angle setup
    map_tool.clean()
    map_tool._widget._tabs.setCurrentIndex(1)
    map_tool._widget._angle_step.setValue(1)
    map_tool._widget._angle_width.setValue(20)
    map_tool._widget._show_distances.setChecked(False)

    map_tool.activate()

    assert map_tool._snap_point is None

    point = QgsPointXY(-336366.19582480326062068, -1189110.65821624454110861)

    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, point, event_type=QEvent.Type.MouseMove))

    assert map_tool._snap_point == point
    assert map_tool._los_rubber_band.size() == 0
    assert map_tool._distance_limits_rubber_band.size() == 0

    assert map_tool._start_point is None
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point))

    assert map_tool._start_point
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point.project(10, 90)))

    assert map_tool._start_point
    assert map_tool._end_point
    assert map_tool._direction_point is None

    assert map_tool._los_rubber_band.size() == 21
    assert map_tool._distance_limits_rubber_band.size() == 0

    assert los_layer.featureCount() == 0

    # wait for signal - nothing happing just need to wait for it
    with qtbot.waitSignal(map_tool.featuresAdded, timeout=None, raising=True):
        # click button to add LoS to layer
        map_tool._widget._add_los_to_layer.click()

    assert map_tool._start_point is None
    assert map_tool._end_point is None
    assert map_tool._direction_point is None

    assert los_layer.featureCount() == 21
