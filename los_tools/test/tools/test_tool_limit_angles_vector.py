import unittest
import os

from qgis.core import (QgsVectorLayer,
                       QgsProcessingFeedback,
                       QgsProcessingContext)

from los_tools.tools.tool_limit_angles_vector import LimitAnglesAlgorithm
from los_tools.constants.field_names import FieldNames

from los_tools.test.utils_tests import (print_alg_params,
                                        print_alg_outputs,
                                        get_data_path,
                                        get_data_path_results)


class LimitAnglesAlgorithmTest(unittest.TestCase):

    def setUp(self) -> None:
        self.los_no_target = QgsVectorLayer(get_data_path(file="no_target_los.gpkg"))
        self.los_no_target_wrong = QgsVectorLayer(get_data_path(file="no_target_los_wrong.gpkg"))
        self.polygon = QgsVectorLayer(get_data_path(file="poly.gpkg"))
        self.polygons = QgsVectorLayer(get_data_path(file="polys.gpkg"))
        self.alg = LimitAnglesAlgorithm()
        self.alg.initAlgorithm()

    @unittest.skip("printing not necessary `test_show_params()`")
    def test_show_params(self) -> None:
        print("{}".format(self.alg.name()))
        print("----------------------------------")
        print_alg_params(self.alg)
        print("----------------------------------")
        print_alg_outputs(self.alg)

    def test_parameters(self) -> None:
        param_los_layer = self.alg.parameterDefinition("LoSLayer")
        param_object_layer = self.alg.parameterDefinition("ObjectLayer")
        param_output_table = self.alg.parameterDefinition("OutputTable")

        self.assertEqual("source", param_los_layer.type())
        self.assertEqual("source", param_object_layer.type())
        self.assertEqual("sink", param_output_table.type())

    def test_check_wrong_params(self) -> None:
        context = QgsProcessingContext()

        output_path = get_data_path_results(file="table.csv")

        params = {
            "LoSLayer": self.los_no_target_wrong,
            "ObjectLayer": self.polygon,
            "OutputTable": output_path,
        }

        can_run, msg = self.alg.checkParameterValues(params, context=context)

        self.assertFalse(can_run)
        self.assertIn("Fields specific for LoS without target not found in current layer (los_type).",
                      msg)

        params = {
            "LoSLayer": self.los_no_target,
            "ObjectLayer": self.polygons,
            "OutputTable": output_path,
        }

        can_run, msg = self.alg.checkParameterValues(params, context=context)

        self.assertFalse(can_run)
        self.assertIn("Object layer must have only one feature.",
                      msg)

    def test_run_alg(self) -> None:
        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()

        output_path = get_data_path_results(file="table.csv")

        params = {
            "LoSLayer": self.los_no_target,
            "ObjectLayer": self.polygon,
            "OutputTable": output_path,
        }

        can_run, msg = self.alg.checkParameterValues(params, context=context)

        self.assertTrue(can_run)
        self.assertIn("OK", msg)

        self.alg.run(parameters=params, context=context, feedback=feedback)

        table = QgsVectorLayer(output_path)

        self.assertIn(FieldNames.AZIMUTH_MIN, table.fields().names())
        self.assertIn(FieldNames.AZIMUTH_MAX, table.fields().names())

        unique_ids = self.los_no_target.uniqueValues(self.los_no_target.fields().lookupField(FieldNames.ID_OBSERVER))

        self.assertEqual(table.featureCount(), len(unique_ids))
