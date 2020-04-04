import unittest

from qgis.core import (QgsVectorLayer,
                       QgsRasterLayer,
                       QgsProcessingFeedback,
                       QgsProcessingContext)
from qgis._core import QgsWkbTypes

from processing.core.Processing import Processing
import processing

from los_tools.create_points.tool_points_in_area import CreatePointsInAreaAlgorithm

from los_tools.test.utils_tests import (print_alg_params,
                                        print_alg_outputs,
                                        get_data_path,
                                        get_data_path_results,
                                        get_qgis_app)

QGIS = get_qgis_app()


class CreatePointsInAreaAlgorithmTest(unittest.TestCase):

    def setUp(self) -> None:
        self.raster = QgsRasterLayer(get_data_path(file="dsm.tif"))
        self.polygons = QgsVectorLayer(get_data_path(file="polys.gpkg"))
        self.polygons_id_field = "id_poly"

        self.alg = CreatePointsInAreaAlgorithm()
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

    def test_parameters(self) -> None:
        param_input_layer = self.alg.parameterDefinition("InputLayer")
        param_id_field = self.alg.parameterDefinition("IdField")
        param_input_raster = self.alg.parameterDefinition("InputRaster")
        param_output_layer = self.alg.parameterDefinition("OutputLayer")

        self.assertEqual("source", param_input_layer.type())
        self.assertEqual("field", param_id_field.type())
        self.assertEqual("raster", param_input_raster.type())
        self.assertEqual("sink", param_output_layer.type())

        self.assertEqual("InputLayer", param_id_field.parentLayerParameterName())

    def test_check_wrong_params(self) -> None:
        # does not apply, there are no checks for parameters
        pass

    def test_run_alg(self):

        Processing.initialize()

        output_path = get_data_path_results(file="points_in_polygons.gpkg")

        params = {
            "InputLayer": self.polygons,
            "IdField": self.polygons_id_field,
            "InputRaster": self.raster,
            "OutputLayer": output_path,
        }

        self.alg.run(parameters=params, context=self.context, feedback=self.feedback)

        point_layer = QgsVectorLayer(output_path)

        self.assertIn(self.polygons_id_field, point_layer.fields().names())

        self.assertEqual(2003, point_layer.featureCount())

        self.assertTrue(self.polygons.extent().contains(point_layer.extent()))

        self.assertEqual(QgsWkbTypes.Point, point_layer.wkbType())
