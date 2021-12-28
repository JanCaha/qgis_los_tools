import unittest
import os

from qgis.core import (QgsVectorLayer,
                       QgsRasterLayer,
                       QgsWkbTypes,
                       QgsProcessingFeedback,
                       QgsProcessingContext)

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase

from los_tools.create_points.tool_optimize_point_location import OptimizePointLocationAlgorithm

from tests.utils_tests import (print_alg_params,
                               print_alg_outputs,
                               get_data_path,
                               get_data_path_results)


class OptimizePointLocationAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:
        self.feedback = QgsProcessingFeedback()
        self.context = QgsProcessingContext()

        self.points = QgsVectorLayer(get_data_path(file="points.gpkg"))

        self.raster = QgsRasterLayer(get_data_path(file="dsm.tif"))

        self.alg = OptimizePointLocationAlgorithm()
        self.alg.initAlgorithm()

    @unittest.skip("printing not necessary `test_show_params()`")
    def test_show_params(self) -> None:
        print("{}".format(self.alg.name()))
        print("----------------------------------")
        print_alg_params(self.alg)
        print("----------------------------------")
        print_alg_outputs(self.alg)

    def test_parameters(self) -> None:

        param_input_raster = self.alg.parameterDefinition("InputRaster")
        param_input_points = self.alg.parameterDefinition("InputLayer")
        param_distance = self.alg.parameterDefinition("Distance")
        param_mask_raster = self.alg.parameterDefinition("MaskRaster")
        param_output_layer = self.alg.parameterDefinition("OutputLayer")

        self.assertEqual("raster", param_input_raster.type())
        self.assertEqual("source", param_input_points.type())
        self.assertEqual("distance", param_distance.type())
        self.assertEqual("raster", param_mask_raster.type())
        self.assertEqual("sink", param_output_layer.type())

        self.assertEqual(30, param_distance.defaultValue())

    def test_check_wrong_params(self) -> None:

        # multiband raster fail
        params = {
            "InputRaster": QgsRasterLayer(get_data_path(file="raster_multiband.tif"))
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertFalse(can_run)
        self.assertIn("`Location optimization raster` can only have one band.", msg)

        # observer layer with geographic coordinates
        params = {
            "InputRaster": self.raster,
            "InputLayer": QgsVectorLayer(get_data_path(file="single_point_wgs84.gpkg")),
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertFalse(can_run)
        self.assertIn("`Input point layer` crs must be projected.", msg)

        # raster crs != observers crs
        params = {
            "InputRaster": QgsRasterLayer(get_data_path(file="dsm_epsg_5514.tif")),
            "InputLayer": self.points
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertFalse(can_run)
        self.assertIn("`Input point layer` and `Location optimization raster` crs must be equal.", msg)

        # mask raster errors
        params = {
            "InputRaster": self.raster,
            "InputLayer": self.points,
            "MaskRaster": QgsRasterLayer(get_data_path(file="raster_multiband.tif"))
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertFalse(can_run)
        self.assertIn("`Mask raster` can only have one band.", msg)

        params = {
            "InputRaster": self.raster,
            "InputLayer": self.points,
            "MaskRaster": QgsRasterLayer(get_data_path(file="dsm_epsg_5514.tif"))
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertFalse(can_run)
        self.assertIn("CRS for `Mask raster` and `Location optimization raster` must be equal.", msg)

    def test_run_alg(self):

        output_path = get_data_path_results(file="points_optimized.gpkg")

        params = {
            "InputRaster": self.raster,
            "InputLayer": self.points,
            "Distance": 10,
            "OutputLayer": output_path,
        }

        self.alg.run(parameters=params, context=self.context, feedback=self.feedback)

        output_layer = QgsVectorLayer(output_path)

        self.assertQgsVectorLayer(output_layer,
                                  geom_type=self.points.wkbType(),
                                  crs=self.points.sourceCrs())

        self.assertIsInstance(output_layer, QgsVectorLayer)
        self.assertEqual(self.points.featureCount(), output_layer.featureCount())
