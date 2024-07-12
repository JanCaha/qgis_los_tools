import pytest
from pytest_qgis.utils import clean_qgis_layer
from qgis.core import QgsFeature, QgsRasterLayer, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from tests.utils import data_file_path


@pytest.fixture
@clean_qgis_layer
def raster_small() -> QgsRasterLayer:
    d = data_file_path("dsm.tif")
    r = QgsRasterLayer(d.as_posix(), d.stem, "gdal")
    assert r.isValid()
    return r


@pytest.fixture
@clean_qgis_layer
def raster_large() -> QgsRasterLayer:
    d = data_file_path("srtm.tif")
    r = QgsRasterLayer(d.as_posix(), d.stem, "gdal")
    assert r.isValid()
    return r


@pytest.fixture
@clean_qgis_layer
def raster_wrong_crs() -> QgsRasterLayer:
    d = data_file_path("dsm_epsg_5514.tif")
    r = QgsRasterLayer(d.as_posix(), d.stem, "gdal")
    assert r.isValid()
    return r


@pytest.fixture
@clean_qgis_layer
def raster_multi_band() -> QgsRasterLayer:
    d = data_file_path("raster_multiband.tif")
    r = QgsRasterLayer(d.as_posix(), d.stem, "gdal")
    assert r.isValid()
    return r


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


@pytest.fixture
@clean_qgis_layer
def los_global() -> QgsVectorLayer:
    p = data_file_path("los_global.gpkg")
    v = QgsVectorLayer(p.as_posix(), p.stem, "ogr")
    assert v.isValid()
    return v


@pytest.fixture
@clean_qgis_layer
def los_local() -> QgsVectorLayer:
    p = data_file_path("los_local.gpkg")
    v = QgsVectorLayer(p.as_posix(), p.stem, "ogr")
    assert v.isValid()
    return v


@pytest.fixture
@clean_qgis_layer
def los_no_target() -> QgsVectorLayer:
    p = data_file_path("no_target_los.gpkg")
    v = QgsVectorLayer(p.as_posix(), p.stem, "ogr")
    assert v.isValid()
    return v


@pytest.fixture
@clean_qgis_layer
def los_no_target_wrong() -> QgsVectorLayer:
    p = data_file_path("no_target_los_wrong.gpkg")
    v = QgsVectorLayer(p.as_posix(), p.stem, "ogr")
    assert v.isValid()
    return v


@pytest.fixture
@clean_qgis_layer
def layer_polygon() -> QgsVectorLayer:
    p = data_file_path("poly.gpkg")
    v = QgsVectorLayer(p.as_posix(), p.stem, "ogr")
    assert v.isValid()
    return v


@pytest.fixture
@clean_qgis_layer
def layer_polygon_crs_5514() -> QgsVectorLayer:
    p = data_file_path("poly_epsg_5514.gpkg")
    v = QgsVectorLayer(p.as_posix(), p.stem, "ogr")
    assert v.isValid()
    return v


@pytest.fixture
@clean_qgis_layer
def layer_polygons() -> QgsVectorLayer:
    p = data_file_path("polys.gpkg")
    v = QgsVectorLayer(p.as_posix(), p.stem, "ogr")
    assert v.isValid()
    return v
