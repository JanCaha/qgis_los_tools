import typing
from pathlib import Path

import pytest
from pytest_qgis.utils import clean_qgis_layer
from qgis.core import Qgis, QgsFeature, QgsRasterLayer, QgsVectorLayer
from qgis.gui import QgisInterface

from los_tools.constants.field_names import FieldNames
from tests.utils import data_file_path


@pytest.fixture(autouse=True, scope="function")
def _monkeypatch_iface(qgis_iface: QgisInterface, monkeypatch):
    def add_user_input_widget(widget):
        pass

    qgis_iface.addUserInputWidget = None
    monkeypatch.setattr(qgis_iface, "addUserInputWidget", add_user_input_widget)

    def push_widget(widget):
        pass

    qgis_iface.messageBar().pushWidget = None
    monkeypatch.setattr(qgis_iface.messageBar(), "pushWidget", push_widget)

    def pop_widget():
        pass

    qgis_iface.messageBar().popWidget = None
    monkeypatch.setattr(qgis_iface.messageBar(), "popWidget", pop_widget)


def _raster_layer(path: Path) -> QgsRasterLayer:
    layer = QgsRasterLayer(path.as_posix(), path.stem, "gdal")
    assert layer.isValid()
    return layer


@pytest.fixture
@clean_qgis_layer
def raster_small() -> QgsRasterLayer:
    return _raster_layer(data_file_path("dsm.tif"))


@pytest.fixture
@clean_qgis_layer
def raster_large() -> QgsRasterLayer:
    return _raster_layer(data_file_path("srtm.tif"))


@pytest.fixture
@clean_qgis_layer
def raster_wrong_crs() -> QgsRasterLayer:
    return _raster_layer(data_file_path("dsm_epsg_5514.tif"))


@pytest.fixture
@clean_qgis_layer
def raster_multi_band() -> QgsRasterLayer:
    return _raster_layer(data_file_path("raster_multiband.tif"))


@pytest.fixture
@clean_qgis_layer
def table_angle_distance_size() -> QgsVectorLayer:
    table = QgsVectorLayer(
        f"NoGeometry?"
        f"field={FieldNames.SIZE_ANGLE}:double&"
        f"field={FieldNames.DISTANCE}:double&"
        f"field={FieldNames.SIZE}:double",
        "source",
        "memory",
    )

    table_dp = table.dataProvider()

    fields = table.fields()

    field_index_angle = fields.indexFromName(FieldNames.SIZE_ANGLE)
    field_index_distance = fields.indexFromName(FieldNames.DISTANCE)
    field_index_size = fields.indexFromName(FieldNames.SIZE)

    angle_size = 0.1

    f = QgsFeature(fields)
    f.setAttribute(field_index_angle, angle_size)
    f.setAttribute(field_index_distance, 0)
    f.setAttribute(field_index_size, 0.5)

    table_dp.addFeature(f)

    f = QgsFeature(fields)
    f.setAttribute(field_index_angle, angle_size)
    f.setAttribute(field_index_distance, 500)
    f.setAttribute(field_index_size, 0.873)

    table_dp.addFeature(f)

    f = QgsFeature(fields)
    f.setAttribute(field_index_angle, angle_size)
    f.setAttribute(field_index_distance, 1000)
    f.setAttribute(field_index_size, 1.745)

    table_dp.addFeature(f)

    f = QgsFeature(fields)
    f.setAttribute(field_index_angle, angle_size)
    f.setAttribute(field_index_distance, 1500)
    f.setAttribute(field_index_size, 2.618)

    table_dp.addFeature(f)

    f = QgsFeature(fields)
    f.setAttribute(field_index_angle, angle_size)
    f.setAttribute(field_index_distance, 2000)
    f.setAttribute(field_index_size, 3.491)

    table_dp.addFeature(f)

    assert table.isValid()

    return table


def _vector_layer(path: Path) -> QgsVectorLayer:
    layer = QgsVectorLayer(path.as_posix(), path.stem, "ogr")
    assert layer.isValid()
    return layer


@pytest.fixture
@clean_qgis_layer
def los_global() -> QgsVectorLayer:
    return _vector_layer(data_file_path("los_global.gpkg"))


@pytest.fixture
@clean_qgis_layer
def los_local() -> QgsVectorLayer:
    return _vector_layer(data_file_path("los_local.gpkg"))


@pytest.fixture
@clean_qgis_layer
def los_no_target() -> QgsVectorLayer:
    return _vector_layer(data_file_path("no_target_los.gpkg"))


@pytest.fixture
@clean_qgis_layer
def los_no_target_wrong() -> QgsVectorLayer:
    return _vector_layer(data_file_path("no_target_los_wrong.gpkg"))


@pytest.fixture
@clean_qgis_layer
def layer_polygon() -> QgsVectorLayer:
    return _vector_layer(data_file_path("poly.gpkg"))


@pytest.fixture
@clean_qgis_layer
def layer_polygon_crs_5514() -> QgsVectorLayer:
    return _vector_layer(data_file_path("poly_epsg_5514.gpkg"))


@pytest.fixture
@clean_qgis_layer
def layer_polygons() -> QgsVectorLayer:
    return _vector_layer(data_file_path("polys.gpkg"))


@pytest.fixture
@clean_qgis_layer
def horizon_line_local() -> QgsVectorLayer:
    return _vector_layer(data_file_path("horizon_line_local.gpkg"))


@pytest.fixture
@clean_qgis_layer
def horizon_line_global() -> QgsVectorLayer:
    return _vector_layer(data_file_path("horizon_line_global.gpkg"))


@pytest.fixture
@clean_qgis_layer
def layer_point() -> QgsVectorLayer:
    return _vector_layer(data_file_path("single_point.gpkg"))


@pytest.fixture
@clean_qgis_layer
def layer_point_wgs84() -> QgsVectorLayer:
    return _vector_layer(data_file_path("single_point_wgs84.gpkg"))


@pytest.fixture
@clean_qgis_layer
def layer_points() -> QgsVectorLayer:
    return _vector_layer(data_file_path("points.gpkg"))


@pytest.fixture
@clean_qgis_layer
def layer_points_wgs84() -> QgsVectorLayer:
    return _vector_layer(data_file_path("points_wgs84.gpkg"))


@pytest.fixture
@clean_qgis_layer
def layer_points_epsg5514() -> QgsVectorLayer:
    return _vector_layer(data_file_path("points_epsg_5514.gpkg"))


@pytest.fixture
@clean_qgis_layer
def layer_size_distance() -> QgsVectorLayer:
    return _vector_layer(data_file_path("size_distance.xlsx"))


@pytest.fixture
@clean_qgis_layer
def layer_points_in_direction() -> QgsVectorLayer:
    return _vector_layer(data_file_path("points_in_direction.gpkg"))


@pytest.fixture
def mock_add_message_to_messagebar(qgis_iface: QgisInterface) -> typing.Callable:

    def add_message(message, level):
        qgis_iface.messageBar().pushMessage("Patched", message, level=level, duration=0)

    return add_message


@pytest.fixture(autouse=True, scope="function")
def _clear_message_bar_messages(qgis_iface: QgisInterface):
    mb = qgis_iface.messageBar()
    mb.messages[Qgis.MessageLevel.Info] = []
    mb.messages[Qgis.MessageLevel.Warning] = []
    mb.messages[Qgis.MessageLevel.Critical] = []
    mb.messages[Qgis.MessageLevel.Success] = []


@pytest.fixture(autouse=True, scope="function")
def _clean_project(qgis_iface: QgisInterface) -> None:
    qgis_iface.newProject()
