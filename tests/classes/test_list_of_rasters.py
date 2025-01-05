import pytest
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsPoint,
    QgsProject,
    QgsRasterDataProvider,
    QgsRasterLayer,
    QgsVectorLayer,
)

from los_tools.classes.list_raster import ListOfRasters


@pytest.fixture(autouse=True)
def _qgs_project(
    raster_small: QgsRasterLayer,
    raster_large: QgsRasterLayer,
    raster_wrong_crs: QgsRasterLayer,
    raster_multi_band: QgsRasterLayer,
    los_local: QgsVectorLayer,
):
    QgsProject.instance().addMapLayers([raster_small, raster_large, raster_wrong_crs, los_local, raster_multi_band])


def test_create_object(
    raster_small: QgsRasterLayer,
    raster_large: QgsRasterLayer,
    raster_wrong_crs: QgsRasterLayer,
    los_local: QgsVectorLayer,
):
    list_rasters = ListOfRasters([raster_small, raster_large])

    assert isinstance(list_rasters, ListOfRasters)
    assert isinstance(list_rasters.rasters, list)
    assert isinstance(list_rasters.rasters_dp, list)
    assert isinstance(list_rasters.rasters[0], QgsRasterLayer)
    assert isinstance(list_rasters.rasters_dp[0], QgsRasterDataProvider)

    with pytest.raises(ValueError, match="All inputs must be QgsRasterLayer"):
        ListOfRasters([raster_small, raster_large, los_local])

    with pytest.raises(ValueError, match="All CRS must be equal"):
        ListOfRasters([raster_small, raster_large, raster_wrong_crs])


def test_maximal_diagonal_size(
    raster_small: QgsRasterLayer,
    raster_large: QgsRasterLayer,
):
    list_rasters = ListOfRasters([raster_small, raster_large])

    assert list_rasters.maximal_diagonal_size() == pytest.approx(4954.494401943971)


def test_extract_interpolated_value(
    raster_small: QgsRasterLayer,
    raster_large: QgsRasterLayer,
):
    list_rasters = ListOfRasters([raster_small, raster_large])

    point_1 = QgsPoint(-336332.2, -1189104.8)
    point_2 = QgsPoint(-337045.6, -1188775.2)
    point_3 = QgsPoint(-334597.8840, -1187659.5597)

    assert list_rasters.extract_interpolated_value(point_1) == 1007.409252288644
    assert list_rasters.extract_interpolated_value(point_2) == 1076.6832007948944
    assert list_rasters.extract_interpolated_value(point_3) is None


def test_validate_crs(
    raster_small: QgsRasterLayer,
    raster_large: QgsRasterLayer,
    raster_wrong_crs: QgsRasterLayer,
):
    status, msg = ListOfRasters.validate_crs(
        [raster_small, raster_large], crs=QgsCoordinateReferenceSystem("EPSG:8353")
    )

    assert status
    assert msg == ""

    status, msg = ListOfRasters.validate_crs(
        [raster_small, raster_large], crs=QgsCoordinateReferenceSystem("EPSG:5514")
    )

    assert status is False
    assert "Provided crs template and raster layers crs must be equal" in msg

    status, msg = ListOfRasters.validate_crs(
        [raster_small, raster_large, raster_wrong_crs],
        crs=QgsCoordinateReferenceSystem("EPSG:8353"),
    )

    assert status is False
    assert "All CRS for all rasters must be equal" in msg


def test_validate_bands(
    raster_small: QgsRasterLayer,
    raster_large: QgsRasterLayer,
    raster_multi_band: QgsRasterLayer,
):
    status, msg = ListOfRasters.validate_bands([raster_small, raster_large])

    assert status
    assert msg == ""

    status, msg = ListOfRasters.validate_bands([raster_small, raster_large, raster_multi_band])

    assert status is False
    assert "Rasters can only have one band" in msg


def test_validate_ordering(
    raster_small: QgsRasterLayer,
    raster_large: QgsRasterLayer,
):
    status, msg = ListOfRasters.validate_ordering([raster_small, raster_large])

    assert status
    assert msg == ""

    status, msg = ListOfRasters.validate_ordering(
        [
            raster_small,
            raster_large,
            raster_small,
            raster_large,
        ]
    )

    assert status is False
    assert "Raster cell sizes must be unique to form complete ordering" in msg


def test_raster_remove(
    raster_small: QgsRasterLayer,
    raster_large: QgsRasterLayer,
):
    list_rasters = ListOfRasters([raster_small, raster_large])

    assert len(list_rasters.rasters) == 2

    list_rasters.remove_raster(raster_small.id())

    assert len(list_rasters.rasters) == 1
