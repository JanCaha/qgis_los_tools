import unittest

import numpy as np
import math

from qgis.core import (QgsVectorLayer,
                       QgsFeatureRequest,
                       QgsProcessingFeedback,
                       QgsProcessingContext)

from los_tools.create_points.tool_points_in_direction import CreatePointsInDirectionAlgorithm
from los_tools.constants.field_names import FieldNames

from los_tools.test.utils_tests import (print_alg_params,
                                        print_alg_outputs,
                                        get_data_path,
                                        get_data_path_results)


class CreatePointsInDirectionAlgorithmTest(unittest.TestCase):

    def setUp(self) -> None:
        self.points = QgsVectorLayer(get_data_path(file="points.gpkg"))
        self.points_id_field = "id_point"
        self.single_point = QgsVectorLayer(get_data_path(file="single_point.gpkg"))

        self.alg = CreatePointsInDirectionAlgorithm()
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
        param_direction_layer = self.alg.parameterDefinition("DirectionLayer")
        param_angle_offset = self.alg.parameterDefinition("AngleOffset")
        param_angle_step = self.alg.parameterDefinition("AngleStep")
        param_distance = self.alg.parameterDefinition("Distance")
        param_output_layer = self.alg.parameterDefinition("OutputLayer")

        self.assertEqual("source", param_input_layer.type())
        self.assertEqual("field", param_id_field.type())
        self.assertEqual("source", param_direction_layer.type())
        self.assertEqual("number", param_angle_offset.type())
        self.assertEqual("number", param_angle_step.type())
        self.assertEqual("distance", param_distance.type())
        self.assertEqual("sink", param_output_layer.type())

        self.assertEqual("InputLayer", param_id_field.parentLayerParameterName())
        self.assertIn("InputLayer", param_distance.dependsOnOtherParameters())

        self.assertEqual(20, param_angle_offset.defaultValue())
        self.assertEqual(1, param_angle_step.defaultValue())
        self.assertEqual(10, param_distance.defaultValue())

    def test_check_wrong_params(self) -> None:

        output_path = get_data_path_results(file="points_direction.gpkg")

        params = {
            "InputLayer": self.points,
            "IdField": self.points_id_field,
            "DirectionLayer": self.points,
            "AngleOffset": 10,
            "AngleStep": 0.5,
            "Distance": 10,
            "OutputLayer": output_path,
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertFalse(can_run)
        self.assertIn("`Main direction point layer` should only containt one feature.",
                      msg)

    def test_run_alg(self) -> None:

        output_path = get_data_path_results(file="points_direction.gpkg")

        angle_offset = 20
        angle_step = 1
        distance = 10

        params = {
            "InputLayer": self.points,
            "IdField": self.points_id_field,
            "DirectionLayer": self.single_point,
            "AngleOffset": angle_offset,
            "AngleStep": angle_step,
            "Distance": distance,
            "OutputLayer": output_path,
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertTrue(can_run)
        self.assertIn("OK", msg)

        self.alg.run(parameters=params, context=self.context, feedback=self.feedback)

        output_layer = QgsVectorLayer(output_path)

        self.assertIn(FieldNames.ID_ORIGINAL_POINT, output_layer.fields().names())
        self.assertIn(FieldNames.ID_POINT, output_layer.fields().names())
        self.assertIn(FieldNames.AZIMUTH, output_layer.fields().names())

        unique_ids_orig = list(self.points.uniqueValues(self.points.fields().lookupField(self.points_id_field)))
        unique_ids_new = list(output_layer.uniqueValues(output_layer.fields().lookupField(FieldNames.ID_ORIGINAL_POINT)))

        self.assertListEqual(unique_ids_orig, unique_ids_new)

        angles = np.arange(0 - angle_offset,
                           0 + angle_offset + 0.1*angle_step,
                           step=angle_step).tolist()

        number_of_elements = len(angles) * len(unique_ids_orig)

        self.assertEqual(number_of_elements, output_layer.featureCount())

        for id_orig in unique_ids_orig:

            request = QgsFeatureRequest()
            request.setFilterExpression("{} = '{}'".format(FieldNames.ID_ORIGINAL_POINT, id_orig))
            order_by_clause = QgsFeatureRequest.OrderByClause(FieldNames.AZIMUTH, ascending=True)
            request.setOrderBy(QgsFeatureRequest.OrderBy([order_by_clause]))

            features = list(output_layer.getFeatures(request))

            for i in range(0, len(features)-1):
                with self.subTest(id_original_point=id_orig, point_range=i):
                    self.assertAlmostEqual(features[i].geometry().distance(features[i+1].geometry()),
                                           math.radians(angle_step)*distance,
                                           places=5)
