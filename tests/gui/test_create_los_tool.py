# pylint: disable=protected-access
import pytest
from pytestqt.qtbot import QtBot
from qgis.core import QgsPointXY, QgsVectorLayer
from qgis.gui import QgisInterface, QgsMapCanvas
from qgis.PyQt.QtCore import QEvent, Qt

from los_tools.classes.list_raster import ListOfRasters
from los_tools.gui.los_tool.create_los_tool import CreateLoSMapTool
from tests.utils import create_mouse_event


def test_local_los(
    qgis_iface: QgisInterface,
    qgis_canvas: QgsMapCanvas,
    list_of_rasters: ListOfRasters,
    los_layer: QgsVectorLayer,
    center_point: QgsPointXY,
):
    left_point = center_point.project(75, 90)

    map_tool = CreateLoSMapTool(qgis_iface, list_of_rasters, los_layer)

    map_tool.activate()

    assert map_tool._start_point is None
    assert map_tool._end_point is None
    assert map_tool._direction_point is None
    assert map_tool._los_rubber_band.size() == 0

    # set observer point
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, center_point))

    assert map_tool._start_point is not None
    assert map_tool._start_point.isEmpty() is False
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 0

    # move mouse - start creating LoS
    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, left_point, event=QEvent.Type.MouseMove))

    assert map_tool._start_point is not None
    assert map_tool._direction_point is not None
    assert map_tool._direction_point.isEmpty() is False
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 1
    assert map_tool._los_rubber_band.asGeometry().length() == 75

    # set second point create local LoS
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, left_point))

    assert map_tool._start_point is not None
    assert map_tool._direction_point is not None
    assert map_tool._direction_point.isEmpty() is False
    assert map_tool._end_point is not None
    assert map_tool._los_rubber_band.size() == 1

    assert map_tool._los_rubber_band.asGeometry().length() == 75
    assert map_tool._los_rubber_band.asGeometry().asWkt(0) == "LineString (-336420 -1189120, -336345 -1189120)"

    map_tool.deactivate()


def test_global_los(
    qgis_iface: QgisInterface,
    qgis_canvas: QgsMapCanvas,
    los_layer: QgsVectorLayer,
    list_of_rasters: ListOfRasters,
    center_point: QgsPointXY,
):
    left_point = center_point.project(75, 90)

    map_tool = CreateLoSMapTool(qgis_iface, list_of_rasters, los_layer)

    map_tool.activate()

    assert map_tool._start_point is None
    assert map_tool._direction_point is None
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 0

    # set observer point
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, center_point))

    assert map_tool._start_point is not None
    assert map_tool._start_point.isEmpty() is False
    assert map_tool._direction_point is None
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 0
    assert map_tool._widget._add_los_to_layer.isEnabled() is False

    # set global LoS
    map_tool._widget._los_type.setCurrentIndex(1)

    # move mouse - start creating LoS
    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, left_point, event=QEvent.Type.MouseMove))

    assert map_tool._start_point is not None
    assert map_tool._direction_point is not None
    assert map_tool._direction_point.isEmpty() is False
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 1
    assert map_tool._los_rubber_band.asGeometry().length() == pytest.approx(1822.1, rel=0.1)
    assert map_tool._widget._add_los_to_layer.isEnabled() is False

    # create global LoS
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, left_point))

    assert map_tool._start_point is not None
    assert map_tool._direction_point is not None
    assert map_tool._direction_point.isEmpty() is False
    assert map_tool._end_point is not None
    assert map_tool._los_rubber_band.size() == 1

    assert map_tool._los_rubber_band.asGeometry().length() == pytest.approx(1822.1, rel=0.1)
    assert (
        map_tool._los_rubber_band.asGeometry().asWkt(0)
        == "LineString (-336420 -1189120, -336345 -1189120, -334598 -1189120)"
    )
    assert map_tool._widget._add_los_to_layer.isEnabled()

    map_tool.deactivate()


def test_right_click_when_creating(
    qgis_iface: QgisInterface,
    qgis_canvas: QgsMapCanvas,
    los_layer: QgsVectorLayer,
    list_of_rasters: ListOfRasters,
    center_point: QgsPointXY,
):

    left_point = center_point.project(75, 90)

    map_tool = CreateLoSMapTool(qgis_iface, list_of_rasters, los_layer)

    map_tool.activate()

    # set local LoS
    map_tool._widget._los_type.setCurrentIndex(0)

    assert map_tool._start_point is None
    assert map_tool._direction_point is None
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 0

    # set observer point
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, center_point))

    assert map_tool._start_point is not None
    assert map_tool._start_point.isEmpty() is False
    assert map_tool._direction_point is None
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 0

    # move mouse - start creating LoS
    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, left_point, event=QEvent.Type.MouseMove))

    assert map_tool._start_point is not None
    assert map_tool._direction_point is not None
    assert map_tool._direction_point.isEmpty() is False
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 1
    assert map_tool._los_rubber_band.asGeometry().length() == 75

    # mouse right click
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, left_point, mouse_button=Qt.MouseButton.RightButton))

    assert map_tool._start_point is None
    assert map_tool._direction_point is None
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 0


def test_global_los_add_to_plugin_layer(
    qgis_iface: QgisInterface,
    qgis_canvas: QgsMapCanvas,
    los_layer: QgsVectorLayer,
    list_of_rasters: ListOfRasters,
    center_point: QgsPointXY,
    qtbot: QtBot,
):

    left_point = center_point.project(75, 90)

    map_tool = CreateLoSMapTool(qgis_iface, list_of_rasters, los_layer)

    map_tool.activate()

    assert map_tool._start_point is None
    assert map_tool._direction_point is None
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 0

    # set observer point
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, center_point))

    assert map_tool._start_point is not None
    assert map_tool._start_point.isEmpty() is False
    assert map_tool._direction_point is None
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 0
    assert map_tool._widget._add_los_to_layer.isEnabled() is False

    # set global LoS
    map_tool._widget._los_type.setCurrentIndex(1)

    # move mouse - start creating LoS
    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, left_point, event=QEvent.Type.MouseMove))

    assert map_tool._start_point is not None
    assert map_tool._direction_point is not None
    assert map_tool._direction_point.isEmpty() is False
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 1
    assert map_tool._los_rubber_band.asGeometry().length() == pytest.approx(1822.1, rel=0.1)
    assert map_tool._widget._add_los_to_layer.isEnabled() is False

    # create global LoS
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, left_point))

    assert map_tool._start_point is not None
    assert map_tool._direction_point is not None
    assert map_tool._direction_point.isEmpty() is False
    assert map_tool._end_point is not None
    assert map_tool._los_rubber_band.size() == 1

    assert map_tool._los_rubber_band.asGeometry().length() == pytest.approx(1822.1, rel=0.1)
    assert (
        map_tool._los_rubber_band.asGeometry().asWkt(0)
        == "LineString (-336420 -1189120, -336345 -1189120, -334598 -1189120)"
    )
    assert map_tool._widget._add_los_to_layer.isEnabled()

    assert los_layer.dataProvider().featureCount() == 0

    # wait for signal - nothing happing just need to wait for it
    with qtbot.waitSignal(map_tool.featuresAdded, timeout=None, raising=True):
        # click button to add LoS to layer
        map_tool._widget._add_los_to_layer.click()

    assert los_layer.dataProvider().featureCount() == 1

    assert map_tool._start_point is None
    assert map_tool._direction_point is None
    assert map_tool._end_point is None
    assert map_tool._los_rubber_band.size() == 0

    map_tool.deactivate()
