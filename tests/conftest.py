import pytest
from qgis.core import QgsFeature, QgsRasterLayer, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from tests.utils import data_file_path


class TestData:
    d = data_file_path("dsm.tif")
    RASTER_SMALL = QgsRasterLayer(d.as_posix(), d.stem, "gdal")

    d = data_file_path("srtm.tif")
    RASTER_LARGE = QgsRasterLayer(d.as_posix(), d.stem, "gdal")

    d = data_file_path("dsm_epsg_5514.tif")
    RASTER_WRONG_CRS = QgsRasterLayer(d.as_posix(), d.stem, "gdal")

    d = data_file_path("raster_multiband.tif")
    RASTER_MULTI_BAND = QgsRasterLayer(d.as_posix(), d.stem, "gdal")

    d = data_file_path("los_local.gpkg")
    VECTOR_LOS_LOCAL = QgsVectorLayer(d.as_posix(), d.stem, "gdal")


@pytest.fixture
def test_data_class() -> TestData:
    return TestData()


@pytest.fixture
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

    return table
