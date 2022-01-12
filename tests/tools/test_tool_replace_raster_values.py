import unittest

from osgeo import gdal
import numpy as np

from qgis.core import (QgsRasterLayer, QgsProcessingParameterField, QgsProcessingFeedback,
                       QgsProcessingContext)

from processing.core.Processing import Processing

from los_tools.tools.tool_replace_raster_values import ReplaceRasterValuesAlgorithm

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase
from tests.utils_tests import (print_alg_params, print_alg_outputs, get_data_path,
                               get_data_path_results)


class ReplaceRasterValuesAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        self.raster = QgsRasterLayer(get_data_path(file="dsm.tif"))
        self.polygons = f'{get_data_path(file="polys.gpkg")}|layername=polys'

        self.output_path = get_data_path_results(file="raster_new_values.tif")

        self.alg = ReplaceRasterValuesAlgorithm()
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
        param_value_field = self.alg.parameterDefinition("ValueField")
        param_output_raster = self.alg.parameterDefinition("OutputRaster")

        self.assertEqual("raster", param_raster_layer.type())
        self.assertEqual("source", param_vector_layer.type())
        self.assertEqual("number", param_raster_value.type())
        self.assertEqual("field", param_value_field.type())
        self.assertEqual("rasterDestination", param_output_raster.type())

        self.assertEqual(1, param_raster_value.defaultValue())
        self.assertEqual("VectorLayer", param_value_field.parentLayerParameterName())
        self.assertEqual(QgsProcessingParameterField.Numeric, param_value_field.dataType())

    def test_check_wrong_params(self) -> None:
        # does not apply, there are no checks for parameters
        pass

    def test_run_alg(self):

        Processing.initialize()

        params = {
            "RasterLayer": self.raster,
            "VectorLayer": self.polygons,
            "RasterValue": -100,
            "ValueField": "",
            "OutputRaster": self.output_path,
        }

        self.alg.run(params, context=self.context, feedback=self.feedback)

        ds = gdal.Open(self.output_path)
        raster_array = ds.GetRasterBand(1).ReadAsArray()

        self.assertIn(-100, np.unique(raster_array))

        ds = None

        params = {
            "RasterLayer": self.raster,
            "VectorLayer": self.polygons,
            "RasterValue": -1,
            "ValueField": "height",
            "OutputRaster": self.output_path,
        }

        self.alg.run(parameters=params, context=self.context, feedback=self.feedback)

        ds = gdal.Open(self.output_path)
        raster_array = ds.GetRasterBand(1).ReadAsArray()
        unique_values = np.unique(raster_array)

        self.assertIn(1200, unique_values)
        self.assertIn(1100, unique_values)
        self.assertIn(1050, unique_values)

        ds = None
