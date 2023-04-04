import unittest
import math

from qgis.core import (QgsRasterLayer, QgsPointXY, QgsPoint, QgsVectorLayer, QgsLineString,
                       QgsGeometry)

from osgeo import gdal, osr
import numpy as np

from los_tools.processing.tools.util_functions import (bilinear_interpolated_value,
                                                       get_diagonal_size, calculate_distance,
                                                       segmentize_los_line, segmentize_line,
                                                       wkt_to_array_points,
                                                       line_geometry_to_coords)

from tests.utils_tests import get_qgis_app
from tests.utils_tests import (get_data_path)

QGIS_APP = get_qgis_app()


class UtilsTest(unittest.TestCase):

    def setUp(self) -> None:
        self.raster = QgsRasterLayer(get_data_path(file="dsm.tif"))
        self.raster_dp = self.raster.dataProvider()
        self.points = QgsVectorLayer(get_data_path(file="points.gpkg"))

        self.points_count = 10_000
        p = []
        for i in range(self.points_count):
            p.append(QgsPoint(i, i, i))

        self.line_geometry = QgsGeometry.fromPolyline(p)

        small_raster_file = "/vsimem/small.tif"
        array = np.array([[1, 2], [3, 4]])

        self.create_small_raster(small_raster_file, (0, 2), 1, -1, array)

        self.small_raster = QgsRasterLayer(small_raster_file, "test_raster", "gdal")
        self.small_raster_dp = self.small_raster.dataProvider()

    def create_small_raster(self, newRasterfn, rasterOrigin, pixelWidth, pixelHeight, array):

        array = array[::-1]

        cols = array.shape[1]
        rows = array.shape[0]
        originX = rasterOrigin[0]
        originY = rasterOrigin[1]

        driver = gdal.GetDriverByName('GTiff')
        outRaster: gdal.Dataset = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Float32)
        outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
        outband: gdal.Band = outRaster.GetRasterBand(1)
        outband.WriteArray(array)
        outband.SetNoDataValue(-9999)
        outRasterSRS = osr.SpatialReference()
        outRasterSRS.ImportFromEPSG(5514)
        outRaster.SetProjection(outRasterSRS.ExportToWkt())
        outband.FlushCache()

    def test_bilinear_interpolated_value_small_raster(self):

        bilinear_value = bilinear_interpolated_value(self.small_raster_dp, QgsPointXY(1, 1))
        self.assertAlmostEqual(2.5, bilinear_value, places=8)

        bilinear_value = bilinear_interpolated_value(self.small_raster_dp,
                                                     QgsPointXY(0.500000001, 1))
        self.assertAlmostEqual(2, bilinear_value, places=8)

        bilinear_value = bilinear_interpolated_value(self.small_raster_dp,
                                                     QgsPointXY(1, 1.499999999))
        self.assertAlmostEqual(3.5, bilinear_value, places=8)

        bilinear_value = bilinear_interpolated_value(self.small_raster_dp,
                                                     QgsPointXY(1.499999999, 1))
        self.assertAlmostEqual(3, bilinear_value, places=8)

        bilinear_value = bilinear_interpolated_value(self.small_raster_dp,
                                                     QgsPointXY(1, 0.500000001))
        self.assertAlmostEqual(1.5, bilinear_value, places=8)

    def test_bilinear_interpolated_value(self):

        base_x = -336429.64
        base_y = -1189102.12
        p1 = QgsPointXY(base_x, base_y)
        p2 = QgsPointXY(base_x - 0.5, base_y)
        p3 = QgsPointXY(base_x - 0.5, base_y + 0.5)
        p4 = QgsPointXY(base_x, base_y + 0.5)
        value = (self.raster_dp.sample(p1, 1)[0] + self.raster_dp.sample(p2, 1)[0] +
                 self.raster_dp.sample(p3, 1)[0] + self.raster_dp.sample(p4, 1)[0]) / 4
        bilinear_value = bilinear_interpolated_value(self.raster_dp, QgsPointXY(base_x, base_y))
        self.assertAlmostEqual(value, bilinear_value, places=2)

        base_x = -336429.143
        base_y = -1189102.621
        p = QgsPointXY(base_x, base_y)
        value = self.raster_dp.sample(p1, 1)[0]
        bilinear_value = bilinear_interpolated_value(self.raster_dp, p)
        self.assertAlmostEqual(value, bilinear_value, places=2)

    def test_get_diagonal_size(self):
        extent = self.raster_dp.extent()
        self.assertEqual(math.sqrt(math.pow(extent.width(), 2) + math.pow(extent.height(), 2)),
                         get_diagonal_size(self.raster_dp))

    def test_calculate_distance(self):
        self.assertEqual(math.sqrt(2), calculate_distance(0, 0, 1, 1))
        self.assertEqual(5, calculate_distance(0, 0, 0, 5))
        self.assertEqual(math.sqrt(200), calculate_distance(0, 0, 10, 10))

    def test_segmentize_line(self):

        line = QgsGeometry.fromPolyline(
            [QgsPoint(0, 0), QgsPoint(1, 0),
             QgsPoint(1, 1), QgsPoint(2, 2)])

        line_seg = segmentize_line(line, 0.1)

        self.assertIsInstance(line_seg, QgsLineString)

        self.assertEqual(len(line_seg.points()), 36)
        self.assertEqual(line_seg.points()[0], QgsPoint(0, 0))
        self.assertEqual(line_seg.points()[10], QgsPoint(1, 0))
        self.assertEqual(line_seg.points()[20], QgsPoint(1, 1))
        self.assertEqual(line_seg.points()[-1], QgsPoint(2, 2))

    def test_segmentize_los_line(self):

        line = QgsGeometry.fromPolyline(
            [QgsPoint(0, 0), QgsPoint(1, 0),
             QgsPoint(1, 1), QgsPoint(2, 2)])

        with self.assertRaisesRegex(ValueError,
                                    "Should only segmentize lines with at most 3 vertices"):
            segmentize_los_line(line, 1)

        polygon = QgsGeometry.fromPolygonXY(
            [[QgsPointXY(0, 0), QgsPointXY(1, 0),
              QgsPointXY(0.5, 1)]])

        with self.assertRaisesRegex(TypeError, "Can only properly segmentize Lines"):
            segmentize_los_line(polygon, 1)

        geom = QgsLineString()

        with self.assertRaisesRegex(TypeError, "`line` should be `QgsGeometry`"):
            segmentize_los_line(geom, 1)

    def test_wkt_to_array(self):

        wkt = self.line_geometry.asWkt()
        points = wkt_to_array_points(wkt)

        assert len(points) == self.points_count

        for i in range(len(points)):
            assert isinstance(points[i], list)
            assert len(points[i]) == 3

            for j in range(len(points[i])):
                assert isinstance(points[i][j], float)

    def test_geom_to_wkt(self):

        points = line_geometry_to_coords(self.line_geometry)

        assert len(points) == self.points_count

        for i in range(len(points)):
            assert isinstance(points[i], list)
            assert len(points[i]) == 3

            for j in range(len(points[i])):
                assert isinstance(points[i][j], float)
