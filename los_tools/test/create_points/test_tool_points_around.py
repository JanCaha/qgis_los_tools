import unittest
import os

from qgis.core import (QgsVectorLayer,
                       QgsProcessingFeedback,
                       QgsProcessingContext)

from los_tools.create_points.tool_points_around import CreatePointsAroundAlgorithm

from los_tools.test.utils_tests import (print_alg_params,
                                        print_alg_outputs,
                                        get_data_path,
                                        get_data_path_results)


class CreatePointsAroundAlgorithmTest(unittest.TestCase):

    def setUp(self) -> None:
        self.feedback = QgsProcessingFeedback()
        self.context = QgsProcessingContext()

        self.points = QgsVectorLayer(get_data_path(file="points.gpkg"))

        self.alg = CreatePointsAroundAlgorithm()
        self.alg.initAlgorithm()

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
        param_angle_start = self.alg.parameterDefinition("AngleStart")
        param_angle_end = self.alg.parameterDefinition("AngleEnd")
        param_angle_step = self.alg.parameterDefinition("AngleStep")
        param_distance = self.alg.parameterDefinition("Distance")
        param_output_layer = self.alg.parameterDefinition("OutputLayer")

        self.assertEqual("source", param_input_layer.type())
        self.assertEqual("field", param_id_field.type())
        self.assertEqual("number", param_angle_start.type())
        self.assertEqual("number", param_angle_end.type())
        self.assertEqual("number", param_angle_step.type())
        self.assertEqual("distance", param_distance.type())
        self.assertEqual("sink", param_output_layer.type())

        self.assertIn("InputLayer", param_distance.dependsOnOtherParameters())

        self.assertEqual(0, param_angle_start.defaultValue())
        self.assertEqual(359, param_angle_end.defaultValue())
        self.assertEqual(1, param_angle_step.defaultValue())
        self.assertEqual(10, param_distance.defaultValue())

    def test_check_wrong_params(self) -> None:
        # does not apply, there are no checks for parameters
        pass

    def test_run_alg(self):

        output_path = get_data_path_results(file="points_around.gpkg")

        params = {
            "InputLayer": self.points,
            "IdField": "id_point",
            "AngleStart": 0,
            "AngleEnd": 359,
            "AngleStep": 1,
            "Distance": 5,
            "OutputLayer": output_path,
        }

        self.alg.run(parameters=params, context=self.context, feedback=self.feedback)

        output_layer = QgsVectorLayer(output_path)

        self.assertIsInstance(output_layer, QgsVectorLayer)
        self.assertEqual(2160, output_layer.featureCount())
