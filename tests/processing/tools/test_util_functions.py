import math
import unittest

import numpy as np
import pytest
from osgeo import gdal, osr
from qgis.core import QgsGeometry, QgsLineString, QgsPoint, QgsPointXY, QgsRasterLayer, QgsVectorLayer

from los_tools.processing.tools.util_functions import (
    bilinear_interpolated_value,
    calculate_distance,
    get_diagonal_size,
    line_geometry_to_coords,
    segmentize_line,
    segmentize_los_line,
    wkt_to_array_points,
)


def create_small_raster(newRasterfn, rasterOrigin, pixelWidth, pixelHeight, array):
    array = array[::-1]
    cols = array.shape[1]
    rows = array.shape[0]
    originX = rasterOrigin[0]
    originY = rasterOrigin[1]

    driver = gdal.GetDriverByName("GTiff")
    outRaster: gdal.Dataset = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Float32)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband: gdal.Band = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outband.SetNoDataValue(-9999)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(5514)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


@pytest.fixture
def small_raster_example() -> QgsRasterLayer:
    small_raster_file = "/vsimem/small.tif"
    array = np.array([[1, 2], [3, 4]])

    create_small_raster(small_raster_file, (0, 2), 1, -1, array)

    small_raster = QgsRasterLayer(small_raster_file, "test_raster", "gdal")

    return small_raster


def test_bilinear_interpolated_value_small_raster(small_raster_example: QgsRasterLayer):
    small_raster_dp = small_raster_example.dataProvider()

    bilinear_value = bilinear_interpolated_value(small_raster_dp, QgsPointXY(1, 1))
    assert bilinear_value == pytest.approx(2.5)

    bilinear_value = bilinear_interpolated_value(small_raster_dp, QgsPointXY(0.500000001, 1))
    assert bilinear_value == pytest.approx(2)

    bilinear_value = bilinear_interpolated_value(small_raster_dp, QgsPointXY(1, 1.499999999))
    assert bilinear_value == pytest.approx(3.5)

    bilinear_value = bilinear_interpolated_value(small_raster_dp, QgsPointXY(1.499999999, 1))
    assert bilinear_value == pytest.approx(3)

    bilinear_value = bilinear_interpolated_value(small_raster_dp, QgsPointXY(1, 0.500000001))
    assert bilinear_value == pytest.approx(1.5)


def test_bilinear_interpolated_value(raster_small: QgsRasterLayer):
    raster_dp = raster_small.dataProvider()

    base_x = -336429.64
    base_y = -1189102.12
    p1 = QgsPointXY(base_x, base_y)
    p2 = QgsPointXY(base_x - 0.5, base_y)
    p3 = QgsPointXY(base_x - 0.5, base_y + 0.5)
    p4 = QgsPointXY(base_x, base_y + 0.5)
    value = (
        raster_dp.sample(p1, 1)[0]
        + raster_dp.sample(p2, 1)[0]
        + raster_dp.sample(p3, 1)[0]
        + raster_dp.sample(p4, 1)[0]
    ) / 4
    bilinear_value = bilinear_interpolated_value(raster_dp, QgsPointXY(base_x, base_y))
    assert bilinear_value == pytest.approx(value, abs=0.005)

    base_x = -336429.143
    base_y = -1189102.621
    p = QgsPointXY(base_x, base_y)
    value = raster_dp.sample(p1, 1)[0]
    bilinear_value = bilinear_interpolated_value(raster_dp, p)
    assert bilinear_value == pytest.approx(value, abs=0.005)


def test_get_diagonal_size(raster_small: QgsRasterLayer):
    raster_dp = raster_small.dataProvider()

    extent = raster_dp.extent()

    math.sqrt(math.pow(extent.width(), 2) + math.pow(extent.height(), 2)) == get_diagonal_size(raster_dp)


def test_calculate_distance():
    assert math.sqrt(2) == calculate_distance(0, 0, 1, 1)
    assert 5 == calculate_distance(0, 0, 0, 5)
    assert math.sqrt(200) == calculate_distance(0, 0, 10, 10)


def test_segmentize_line():
    line = QgsGeometry.fromPolyline([QgsPoint(0, 0), QgsPoint(1, 0), QgsPoint(1, 1), QgsPoint(2, 2)])

    line_seg = segmentize_line(line, 0.1)

    assert isinstance(line_seg, QgsLineString)

    assert len(line_seg.points()) == 36
    assert line_seg.points()[0] == QgsPoint(0, 0)
    assert line_seg.points()[10] == QgsPoint(1, 0)
    assert line_seg.points()[20] == QgsPoint(1, 1)
    assert line_seg.points()[-1] == QgsPoint(2, 2)


def test_segmentize_los_line():
    line = QgsGeometry.fromPolyline([QgsPoint(0, 0), QgsPoint(1, 0), QgsPoint(1, 1), QgsPoint(2, 2)])

    with pytest.raises(ValueError, match="Should only segmentize lines with at most 3 vertices"):
        segmentize_los_line(line, 1)

    polygon = QgsGeometry.fromPolygonXY([[QgsPointXY(0, 0), QgsPointXY(1, 0), QgsPointXY(0.5, 1)]])

    with pytest.raises(TypeError, match="Can only properly segmentize Lines"):
        segmentize_los_line(polygon, 1)

    geom = QgsLineString()

    with pytest.raises(TypeError, match="`line` should be `QgsGeometry`"):
        segmentize_los_line(geom, 1)


def test_wkt_to_array():
    points_count = 10
    p = []
    for i in range(points_count):
        p.append(QgsPoint(i, i, i))

    line_geometry = QgsGeometry.fromPolyline(p)
    wkt = line_geometry.asWkt()
    points = wkt_to_array_points(wkt)

    assert len(points) == points_count

    for i, p in enumerate(points):
        assert isinstance(p, list)
        assert len(p) == 3

        for j in range(len(points[i])):
            assert isinstance(points[i][j], float)


def test_geom_to_wkt():
    points_count = 10
    p = []
    for i in range(points_count):
        p.append(QgsPoint(i, i, i))

    line_geometry = QgsGeometry.fromPolyline(p)

    points = line_geometry_to_coords(line_geometry)

    assert len(points) == points_count

    for i, p in enumerate(points):
        assert isinstance(p, list)
        assert len(p) == 3

        for j in range(len(points[i])):
            assert isinstance(points[i][j], float)
