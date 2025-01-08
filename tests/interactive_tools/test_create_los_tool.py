# pylint: disable=protected-access
import pytest
from pytestqt.qtbot import QtBot
from qgis.core import QgsMemoryProviderUtils, QgsPointXY, QgsProject, QgsRasterLayer, QgsWkbTypes
from qgis.gui import QgisInterface, QgsMapCanvas
from qgis.PyQt.QtCore import QEvent, Qt
from qgis.PyQt.QtWidgets import QWidget

from los_tools.classes.list_raster import ListOfRasters
from los_tools.constants.fields import Fields
from los_tools.gui.create_los_tool.create_los_tool import CreateLoSMapTool
from los_tools.gui.dialog_los_settings import LoSSettings
from tests.utils import create_mouse_event


def test_local_los(
    qgis_parent: QWidget,
    qgis_iface: QgisInterface,
    qgis_canvas: QgsMapCanvas,
    list_of_rasters: ListOfRasters,
    center_point: QgsPointXY,
):
    left_point = center_point.project(75, 90)

    los_settings = LoSSettings(qgis_parent)

    map_tool = CreateLoSMapTool(qgis_iface, list_of_rasters, los_settings)

    map_tool.activate()

    assert map_tool._start_point is None
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0

    # set observer point
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, center_point))

    assert map_tool._start_point is not None
    assert map_tool._start_point.isEmpty() is False
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0

    # move mouse - start creating LoS
    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, left_point, event=QEvent.Type.MouseMove))

    assert map_tool._start_point is not None
    assert map_tool._last_towards_point is not None
    assert map_tool._last_towards_point.isEmpty() is False
    assert map_tool._los_rubber_band.size() == 1
    assert map_tool._los_rubber_band.asGeometry().length() == 75

    # set second point create local LoS
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, left_point))

    assert map_tool._start_point is None
    assert map_tool._last_towards_point is not None
    assert map_tool._last_towards_point.isEmpty() is False
    assert map_tool._los_rubber_band.size() == 1

    assert map_tool._los_rubber_band.asGeometry().length() == 75
    assert map_tool._los_rubber_band.asGeometry().asWkt(0) == "LineString (-336420 -1189120, -336345 -1189120)"

    map_tool.deactivate()


def test_global_los(
    qgis_parent: QWidget,
    qgis_iface: QgisInterface,
    qgis_canvas: QgsMapCanvas,
    list_of_rasters: ListOfRasters,
    center_point: QgsPointXY,
):
    left_point = center_point.project(75, 90)

    los_settings = LoSSettings(qgis_parent)

    map_tool = CreateLoSMapTool(qgis_iface, list_of_rasters, los_settings)

    map_tool.activate()

    assert map_tool._start_point is None
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0

    # set observer point
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, center_point))

    assert map_tool._start_point is not None
    assert map_tool._start_point.isEmpty() is False
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0
    assert map_tool._widget._add_los_to_layer.isEnabled() is False

    # set global LoS
    map_tool._widget._los_type.setCurrentIndex(1)

    # move mouse - start creating LoS
    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, left_point, event=QEvent.Type.MouseMove))

    assert map_tool._start_point is not None
    assert map_tool._last_towards_point is not None
    assert map_tool._last_towards_point.isEmpty() is False
    assert map_tool._los_rubber_band.size() == 1
    assert map_tool._los_rubber_band.asGeometry().length() == pytest.approx(1822.1, rel=0.1)
    assert map_tool._widget._add_los_to_layer.isEnabled() is False

    # create global LoS
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, left_point))

    assert map_tool._start_point is None
    assert map_tool._last_towards_point is not None
    assert map_tool._last_towards_point.isEmpty() is False
    assert map_tool._los_rubber_band.size() == 1

    assert map_tool._los_rubber_band.asGeometry().length() == pytest.approx(1822.1, rel=0.1)
    assert (
        map_tool._los_rubber_band.asGeometry().asWkt(0)
        == "LineString (-336420 -1189120, -336345 -1189120, -334598 -1189120)"
    )
    assert map_tool._widget._add_los_to_layer.isEnabled()

    map_tool.deactivate()


def test_no_target_los(
    qgis_parent: QWidget,
    qgis_iface: QgisInterface,
    qgis_canvas: QgsMapCanvas,
    list_of_rasters: ListOfRasters,
    center_point: QgsPointXY,
):
    left_point = center_point.project(75, 90)

    los_settings = LoSSettings(qgis_parent)

    map_tool = CreateLoSMapTool(qgis_iface, list_of_rasters, los_settings)

    map_tool.activate()

    assert map_tool._start_point is None
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0

    # set observer point
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, center_point))

    assert map_tool._start_point is not None
    assert map_tool._start_point.isEmpty() is False
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0

    # prior to setting no target LoS these should be disabled
    assert map_tool._widget._angle_difference.isEnabled() is False
    assert map_tool._widget._angle_step.isEnabled() is False

    # set notarget LoS
    map_tool._widget._los_type.setCurrentIndex(2)
    assert map_tool._widget._angle_difference.isEnabled()
    assert map_tool._widget._angle_step.isEnabled()
    angle_diff = 20
    angle_step = 1
    map_tool._widget._angle_difference.setValue(angle_diff)
    map_tool._widget._angle_step.setValue(angle_step)

    # move mouse - start creating LoS
    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, left_point, event=QEvent.Type.MouseMove))

    assert map_tool._start_point is not None
    assert map_tool._last_towards_point is not None
    assert map_tool._last_towards_point.isEmpty() is False
    assert map_tool._los_rubber_band.size() == ((2 * angle_diff) / angle_step) + 1
    geom = map_tool._los_rubber_band.asGeometry()
    assert geom.get().parts().next().length() == pytest.approx(1939.0, rel=0.1)

    # create global LoS
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, left_point))

    assert map_tool._start_point is None
    assert map_tool._last_towards_point is not None
    assert map_tool._last_towards_point.isEmpty() is False
    assert map_tool._los_rubber_band.size() == ((2 * angle_diff) / angle_step) + 1
    geom = map_tool._los_rubber_band.asGeometry()
    assert geom.get().parts().next().length() == pytest.approx(1939.0, rel=0.1)

    map_tool.deactivate()


def test_right_click_when_creating(
    qgis_parent: QWidget,
    qgis_iface: QgisInterface,
    qgis_canvas: QgsMapCanvas,
    list_of_rasters: ListOfRasters,
    center_point: QgsPointXY,
):

    left_point = center_point.project(75, 90)

    los_settings = LoSSettings(qgis_parent)

    map_tool = CreateLoSMapTool(qgis_iface, list_of_rasters, los_settings)

    map_tool.activate()

    # set local LoS
    map_tool._widget._los_type.setCurrentIndex(0)

    assert map_tool._start_point is None
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0

    # set observer point
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, center_point))

    assert map_tool._start_point is not None
    assert map_tool._start_point.isEmpty() is False
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0

    # move mouse - start creating LoS
    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, left_point, event=QEvent.Type.MouseMove))

    assert map_tool._start_point is not None
    assert map_tool._last_towards_point is not None
    assert map_tool._last_towards_point.isEmpty() is False
    assert map_tool._los_rubber_band.size() == 1
    assert map_tool._los_rubber_band.asGeometry().length() == 75

    # mouse right click
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, left_point, mouse_button=Qt.MouseButton.RightButton))

    assert map_tool._start_point is None
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0


def test_global_los_add_to_plugin_layer(
    qgis_parent: QWidget,
    qgis_iface: QgisInterface,
    qgis_canvas: QgsMapCanvas,
    list_of_rasters: ListOfRasters,
    center_point: QgsPointXY,
    qtbot: QtBot,
):

    crs = qgis_canvas.mapSettings().destinationCrs()
    los_layer = QgsMemoryProviderUtils.createMemoryLayer(
        "Manually Created LoS",
        Fields.los_plugin_layer_fields,
        QgsWkbTypes.LineString25D,
        crs,
    )

    left_point = center_point.project(75, 90)

    los_settings = LoSSettings(qgis_parent)

    map_tool = CreateLoSMapTool(qgis_iface, list_of_rasters, los_settings, los_layer=los_layer)

    map_tool.activate()

    assert map_tool._start_point is None
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0

    # set observer point
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, center_point))

    assert map_tool._start_point is not None
    assert map_tool._start_point.isEmpty() is False
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0
    assert map_tool._widget._add_los_to_layer.isEnabled() is False

    # set global LoS
    map_tool._widget._los_type.setCurrentIndex(1)

    # move mouse - start creating LoS
    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, left_point, event=QEvent.Type.MouseMove))

    assert map_tool._start_point is not None
    assert map_tool._last_towards_point is not None
    assert map_tool._last_towards_point.isEmpty() is False
    assert map_tool._los_rubber_band.size() == 1
    assert map_tool._los_rubber_band.asGeometry().length() == pytest.approx(1822.1, rel=0.1)
    assert map_tool._widget._add_los_to_layer.isEnabled() is False

    # create global LoS
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, left_point))

    assert map_tool._start_point is None
    assert map_tool._last_towards_point is not None
    assert map_tool._last_towards_point.isEmpty() is False
    assert map_tool._los_rubber_band.size() == 1

    assert map_tool._los_rubber_band.asGeometry().length() == pytest.approx(1822.1, rel=0.1)
    assert (
        map_tool._los_rubber_band.asGeometry().asWkt(0)
        == "LineString (-336420 -1189120, -336345 -1189120, -334598 -1189120)"
    )
    assert map_tool._widget._add_los_to_layer.isEnabled()

    assert los_layer.dataProvider().featureCount() == 0

    # click button to add LoS to layer
    map_tool._widget._add_los_to_layer.click()

    # wait for signal - nothing happing just need to wait for it
    with qtbot.waitSignal(map_tool.featuresAdded, timeout=None, raising=True):
        pass

    assert los_layer.dataProvider().featureCount() == 1

    map_tool.deactivate()


def test_no_target_los_add_to_plugin_layer(
    qgis_parent: QWidget,
    qgis_iface: QgisInterface,
    qgis_canvas: QgsMapCanvas,
    list_of_rasters: ListOfRasters,
    center_point: QgsPointXY,
    qtbot: QtBot,
):
    crs = qgis_canvas.mapSettings().destinationCrs()
    los_layer = QgsMemoryProviderUtils.createMemoryLayer(
        "Manually Created LoS",
        Fields.los_plugin_layer_fields,
        QgsWkbTypes.LineString25D,
        crs,
    )

    left_point = center_point.project(75, 90)

    los_settings = LoSSettings(qgis_parent)

    map_tool = CreateLoSMapTool(qgis_iface, list_of_rasters, los_settings, los_layer=los_layer)

    map_tool.activate()

    assert map_tool._start_point is None
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0

    # set observer point
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, center_point))

    assert map_tool._start_point is not None
    assert map_tool._start_point.isEmpty() is False
    assert map_tool._last_towards_point is None
    assert map_tool._los_rubber_band.size() == 0

    # prior to setting no target LoS these should be disabled
    assert map_tool._widget._angle_difference.isEnabled() is False
    assert map_tool._widget._angle_step.isEnabled() is False

    # set notarget LoS
    map_tool._widget._los_type.setCurrentIndex(2)
    assert map_tool._widget._angle_difference.isEnabled()
    assert map_tool._widget._angle_step.isEnabled()
    angle_diff = 20
    angle_step = 1
    map_tool._widget._angle_difference.setValue(angle_diff)
    map_tool._widget._angle_step.setValue(angle_step)

    # move mouse - start creating LoS
    map_tool.canvasMoveEvent(create_mouse_event(qgis_canvas, left_point, event=QEvent.Type.MouseMove))

    assert map_tool._start_point is not None
    assert map_tool._last_towards_point is not None
    assert map_tool._last_towards_point.isEmpty() is False
    assert map_tool._los_rubber_band.size() == ((2 * angle_diff) / angle_step) + 1
    geom = map_tool._los_rubber_band.asGeometry()
    assert geom.get().parts().next().length() == pytest.approx(1939.0, rel=0.1)

    # create global LoS
    map_tool.canvasReleaseEvent(create_mouse_event(qgis_canvas, left_point))

    assert map_tool._start_point is None
    assert map_tool._last_towards_point is not None
    assert map_tool._last_towards_point.isEmpty() is False
    assert map_tool._los_rubber_band.size() == ((2 * angle_diff) / angle_step) + 1
    geom = map_tool._los_rubber_band.asGeometry()
    assert geom.get().parts().next().length() == pytest.approx(1939.0, rel=0.1)

    assert map_tool._widget._add_los_to_layer.isEnabled()

    assert los_layer.dataProvider().featureCount() == 0

    # click button to add LoS to layer
    map_tool._widget._add_los_to_layer.click()

    # wait for signal - nothing happing just need to wait for it
    with qtbot.waitSignal(map_tool.featuresAdded, timeout=None, raising=True):
        pass

    assert los_layer.dataProvider().featureCount() == 41

    map_tool.deactivate()
