import unittest
import os
import math

from qgis.core import (QgsRasterLayer, QgsPointXY, QgsVectorLayer)

from los_tools.tools.util_functions import bilinear_interpolated_value, get_diagonal_size, calculate_distance

from los_tools.test.utils_tests import get_qgis_app

QGIS_APP = get_qgis_app()

data_path = os.path.join(os.path.dirname(__file__), "test_data")
data_path_results = os.path.join(data_path, "results")


class UtilsTest(unittest.TestCase):

    def setUp(self) -> None:
        self.raster = QgsRasterLayer(os.path.join(data_path, "dsm.tif"))
        self.raster_dp = self.raster.dataProvider()
        self.points = QgsVectorLayer(os.path.join(data_path, "points.gpkg"))

    def test_bilinear_interpolated_value(self):

        base_x = -336429.64
        base_y = -1189102.12
        p1 = QgsPointXY(base_x, base_y)
        p2 = QgsPointXY(base_x-0.5, base_y)
        p3 = QgsPointXY(base_x-0.5, base_y+0.5)
        p4 = QgsPointXY(base_x, base_y+0.5)
        value = (self.raster_dp.sample(p1, 1)[0] + self.raster_dp.sample(p2, 1)[0] +
                 self.raster_dp.sample(p3, 1)[0] + self.raster_dp.sample(p4, 1)[0])/4
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
