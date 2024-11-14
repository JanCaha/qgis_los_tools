# pylint: disable=protected-access
from qgis.core import Qgis, QgsPointXY, QgsProject, QgsVectorLayer
from qgis.gui import QgisInterface, QgsMapCanvas
from qgis.PyQt.QtCore import QEvent

from los_tools.gui.los_without_target_visualization.los_without_target import LosNoTargetMapTool
from tests.utils import create_mouse_event


def test_notarget_los_tool(
    qgis_iface: QgisInterface,
    layer_points: QgsVectorLayer,
    qgis_canvas: QgsMapCanvas,
):

    # set project
    project = QgsProject.instance()
    project.addMapLayer(layer_points)

    # properly set up canvas
    qgis_canvas.setLayers([layer_points])
    qgis_canvas.setCurrentLayer(layer_points)
    qgis_canvas.zoomToFeatureExtent(layer_points.extent())

    # set snapping
    config = qgis_canvas.snappingUtils().config()
    config.setEnabled(True)
    config.setMode(Qgis.SnappingMode.AllLayers)
    config.setType(Qgis.SnappingType.Vertex)
    config.setUnits(Qgis.MapToolUnit.Pixels)
    config.setTolerance(10)
    config.addLayers([layer_points])
    project.setSnappingConfig(config)
    qgis_canvas.snappingUtils().setConfig(config)

    map_tool = LosNoTargetMapTool(qgis_iface)

    map_tool.activate()

    assert map_tool._snap_point is None

    point = QgsPointXY(-336366.19582480326062068, -1189110.65821624454110861)

    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, point, event=QEvent.Type.MouseMove))

    assert map_tool._snap_point == point
    assert map_tool._los_rubber_band.size() == 0

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point))

    assert map_tool._los_rubber_band.size() == 360

    map_tool._widget._min_angle.setValue(90)
    map_tool._widget._max_angle.setValue(270)

    point = QgsPointXY(-336408.92, -1189142.77)

    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, point, event=QEvent.Type.MouseMove))

    assert map_tool._snap_point != point
    assert map_tool._snap_point == QgsPointXY(-336366.19582480326062068, -1189110.65821624454110861)

    assert map_tool._los_rubber_band.size() == 181
