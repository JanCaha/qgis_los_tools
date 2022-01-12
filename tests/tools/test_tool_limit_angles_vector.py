import unittest
import os

from qgis.core import (QgsVectorLayer, QgsProcessingFeedback, QgsProcessingContext)

from los_tools.tools.tool_limit_angles_vector import LimitAnglesAlgorithm
from los_tools.constants.field_names import FieldNames

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase
from tests.utils_tests import (print_alg_params, print_alg_outputs, get_data_path,
                               get_data_path_results)


class LimitAnglesAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:
        self.los_no_target = QgsVectorLayer(get_data_path(file="no_target_los.gpkg"))
        self.los_no_target_wrong = QgsVectorLayer(get_data_path(file="no_target_los_wrong.gpkg"))
        self.polygon = QgsVectorLayer(get_data_path(file="poly.gpkg"))
        self.polygons = QgsVectorLayer(get_data_path(file="polys.gpkg"))

        self.output_path = get_data_path_results(file="table.csv")

        self.alg = LimitAnglesAlgorithm()
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
        param_los_layer = self.alg.parameterDefinition("LoSLayer")
        param_object_layer = self.alg.parameterDefinition("ObjectLayer")
        param_output_table = self.alg.parameterDefinition("OutputTable")

        self.assertEqual("source", param_los_layer.type())
        self.assertEqual("source", param_object_layer.type())
        self.assertEqual("sink", param_output_table.type())

    def test_check_wrong_params(self) -> None:

        params = {
            "LoSLayer": self.los_no_target_wrong,
            "ObjectLayer": self.polygon,
            "OutputTable": self.output_path,
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertFalse(can_run)
        self.assertIn(
            "Fields specific for LoS without target not found in current layer (los_type).", msg)

    def test_run_alg(self) -> None:

        params = {
            "LoSLayer": self.los_no_target,
            "ObjectLayerID": "fid",
            "ObjectLayer": self.polygon,
            "OutputTable": self.output_path,
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)
        self.assertTrue(can_run)
        self.assertIn("", msg)

        self.alg.run(parameters=params, context=self.context, feedback=self.feedback)

        table = QgsVectorLayer(self.output_path)

        self.assertIn(FieldNames.AZIMUTH_MIN, table.fields().names())
        self.assertIn(FieldNames.AZIMUTH_MAX, table.fields().names())
        self.assertIn(FieldNames.ID_OBSERVER, table.fields().names())
        self.assertIn(FieldNames.ID_OBJECT, table.fields().names())

        unique_ids = self.los_no_target.uniqueValues(self.los_no_target.fields().lookupField(
            FieldNames.ID_OBSERVER))

        self.assertEqual(table.featureCount(), len(unique_ids))
