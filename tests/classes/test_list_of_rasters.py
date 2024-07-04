import pytest
from qgis.core import QgsCoordinateReferenceSystem, QgsPoint, QgsRasterDataProvider, QgsRasterLayer

from los_tools.classes.list_raster import ListOfRasters
from tests.conftest import TestData


def test_create_object(test_data_class: TestData):
    list_rasters = ListOfRasters([test_data_class.RASTER_SMALL, test_data_class.RASTER_LARGE])

    assert isinstance(list_rasters, ListOfRasters)
    assert isinstance(list_rasters.rasters, list)
    assert isinstance(list_rasters.rasters_dp, list)
    assert isinstance(list_rasters.rasters[0], QgsRasterLayer)
    assert isinstance(list_rasters.rasters_dp[0], QgsRasterDataProvider)

    with pytest.raises(ValueError, match="All inputs must be QgsRasterLayer"):
        ListOfRasters([test_data_class.RASTER_SMALL, test_data_class.RASTER_LARGE, test_data_class.VECTOR_LOS_LOCAL])

    with pytest.raises(ValueError, match="All CRS must be equal"):
        ListOfRasters([test_data_class.RASTER_SMALL, test_data_class.RASTER_LARGE, test_data_class.RASTER_WRONG_CRS])


def test_maximal_diagonal_size(test_data_class: TestData):
    list_rasters = ListOfRasters([test_data_class.RASTER_SMALL, test_data_class.RASTER_LARGE])

    assert list_rasters.maximal_diagonal_size() == pytest.approx(4954.494401943971)


def test_extract_interpolated_value(test_data_class: TestData):
    list_rasters = ListOfRasters([test_data_class.RASTER_SMALL, test_data_class.RASTER_LARGE])

    point_1 = QgsPoint(-336332.2, -1189104.8)
    point_2 = QgsPoint(-337045.6, -1188775.2)
    point_3 = QgsPoint(-334597.8840, -1187659.5597)

    assert list_rasters.extract_interpolated_value(point_1) == 1007.409252288644
    assert list_rasters.extract_interpolated_value(point_2) == 1076.6832007948944
    assert list_rasters.extract_interpolated_value(point_3) is None


def test_validate_crs(test_data_class: TestData):
    status, msg = ListOfRasters.validate_crs(
        [test_data_class.RASTER_SMALL, test_data_class.RASTER_LARGE], crs=QgsCoordinateReferenceSystem("EPSG:8353")
    )

    assert status
    assert msg == ""

    status, msg = ListOfRasters.validate_crs(
        [test_data_class.RASTER_SMALL, test_data_class.RASTER_LARGE], crs=QgsCoordinateReferenceSystem("EPSG:5514")
    )

    assert status is False
    assert "Provided crs template and raster layers crs must be equal" in msg

    status, msg = ListOfRasters.validate_crs(
        [test_data_class.RASTER_SMALL, test_data_class.RASTER_LARGE, test_data_class.RASTER_WRONG_CRS],
        crs=QgsCoordinateReferenceSystem("EPSG:8353"),
    )

    assert status is False
    assert "All CRS for all rasters must be equal" in msg


def test_validate_bands(test_data_class: TestData):
    status, msg = ListOfRasters.validate_bands([test_data_class.RASTER_SMALL, test_data_class.RASTER_LARGE])

    assert status
    assert msg == ""

    status, msg = ListOfRasters.validate_bands(
        [test_data_class.RASTER_SMALL, test_data_class.RASTER_LARGE, test_data_class.RASTER_MULTI_BAND]
    )

    assert status is False
    assert "Rasters can only have one band" in msg


def test_validate_ordering(test_data_class: TestData):
    status, msg = ListOfRasters.validate_ordering([test_data_class.RASTER_SMALL, test_data_class.RASTER_LARGE])

    assert status
    assert msg == ""

    status, msg = ListOfRasters.validate_ordering(
        [
            test_data_class.RASTER_SMALL,
            test_data_class.RASTER_LARGE,
            test_data_class.RASTER_SMALL,
            test_data_class.RASTER_LARGE,
        ]
    )

    assert status is False
    assert "Raster cell sizes must be unique to form complete ordering" in msg
