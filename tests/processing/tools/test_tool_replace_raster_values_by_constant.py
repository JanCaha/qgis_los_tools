import unittest

from osgeo import gdal
import numpy as np

from qgis.core import (QgsRasterLayer, QgsProcessingFeedback, QgsProcessingContext, QgsPointXY)

from processing.core.Processing import Processing

from los_tools.processing.tools.tool_replace_raster_values_by_constant import ReplaceRasterValuesByConstantValueAlgorithm

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase
from tests.utils_tests import (print_alg_params, print_alg_outputs, get_data_path,
                               get_data_path_results)


class ReplaceRasterValuesAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        self.raster = QgsRasterLayer(get_data_path(file="dsm.tif"))
        self.polygons = f'{get_data_path(file="polys.gpkg")}|layername=polys'

        self.output_path = get_data_path_results(file="raster_new_values.tif")

        self.alg = ReplaceRasterValuesByConstantValueAlgorithm()
        self.alg.initAlgorithm()

        self.feedback = QgsProcessingFeedback()
        self.context = QgsProcessingContext()

    @unittest.skip("printing not necessary `test_show_params()`")
    def test_show_params(self) -> None:
        print("{}".format(self.alg.name()))
        print("----------------------------------")
        print_alg_params(self.alg)
        print("----------------------------------")
        print_alg_outputs(self.alg)

    def test_alg_settings(self) -> None:

        self.assertAlgSettings()

    def test_parameters(self) -> None:
        param_raster_layer = self.alg.parameterDefinition("RasterLayer")
        param_vector_layer = self.alg.parameterDefinition("VectorLayer")
        param_raster_value = self.alg.parameterDefinition("RasterValue")
        param_output_raster = self.alg.parameterDefinition("OutputRaster")

        self.assertEqual("raster", param_raster_layer.type())
        self.assertEqual("source", param_vector_layer.type())
        self.assertEqual("number", param_raster_value.type())
        self.assertEqual("rasterDestination", param_output_raster.type())

        self.assertEqual(1, param_raster_value.defaultValue())

    def test_check_wrong_params(self) -> None:
        # does not apply, there are no checks for parameters
        pass

    def test_run_alg(self):

        Processing.initialize()

        params = {
            "RasterLayer": self.raster,
            "VectorLayer": self.polygons,
            "RasterValue": -100,
            "OutputRaster": self.output_path,
        }

        self.alg.run(params, context=self.context, feedback=self.feedback)

        ds = gdal.Open(self.output_path)
        raster_array = ds.GetRasterBand(1).ReadAsArray()

        self.assertIn(-100, np.unique(raster_array))

        self.assert_same_raster_values(self.raster,
                                       QgsRasterLayer(self.output_path, "new raster", "gdal"))
        self.assert_not_same_raster_values(self.raster,
                                           QgsRasterLayer(self.output_path, "new raster", "gdal"))

        ds = None

    def assert_same_raster_values(self, raster_original: QgsRasterLayer,
                                  raster_new: QgsRasterLayer):
        points = [
            QgsPointXY(-336484.00, -1189103.24),
            QgsPointXY(-336378.35, -1189152.49),
            QgsPointXY(-336510.77, -1189168.83),
            QgsPointXY(-336391.02, -1189095.07),
            QgsPointXY(-336352.81, -1189095.48),
        ]

        for point in points:
            assert raster_original.dataProvider().sample(point,
                                                         1) == raster_new.dataProvider().sample(
                                                             point, 1)

    def assert_not_same_raster_values(self, raster_original: QgsRasterLayer,
                                      raster_new: QgsRasterLayer):
        points = [
            QgsPointXY(-336478.89, -1189048.48),
            QgsPointXY(-336421.47, -1189091.80),
            QgsPointXY(-336324.40, -1189098.54),
            QgsPointXY(-336340.34, -1189116.73),
            QgsPointXY(-336469.297, -1189033.700),
        ]

        for point in points:
            new_value = raster_new.dataProvider().sample(point, 1)
            assert raster_original.dataProvider().sample(point, 1) != new_value
            assert new_value == -100
