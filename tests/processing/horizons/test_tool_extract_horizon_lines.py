from qgis.core import (QgsVectorLayer, QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum, QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterBoolean, QgsProcessingParameterNumber)

from qgis._core import QgsWkbTypes

from los_tools.processing.horizons.tool_extract_horizon_lines import ExtractHorizonLinesAlgorithm
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase

from tests.utils_tests import (get_data_path, get_data_path_results)


class ExtractHorizonLinesAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        super().setUp()

        self.los_no_target = QgsVectorLayer(get_data_path(file="no_target_los.gpkg"))

        self.alg = ExtractHorizonLinesAlgorithm()
        self.alg.initAlgorithm()

    def test_parameters(self) -> None:

        self.assertIsInstance(self.alg.parameterDefinition("LoSLayer"),
                              QgsProcessingParameterFeatureSource)
        self.assertIsInstance(self.alg.parameterDefinition("HorizonType"),
                              QgsProcessingParameterEnum)
        self.assertIsInstance(self.alg.parameterDefinition("OutputLayer"),
                              QgsProcessingParameterFeatureSink)
        self.assertIsInstance(self.alg.parameterDefinition("CurvatureCorrections"),
                              QgsProcessingParameterBoolean)
        self.assertIsInstance(self.alg.parameterDefinition("RefractionCoefficient"),
                              QgsProcessingParameterNumber)

        self.assertTrue(self.alg.parameterDefinition("CurvatureCorrections").defaultValue())
        self.assertEqual(
            self.alg.parameterDefinition("RefractionCoefficient").defaultValue(), 0.13)

    def test_alg_settings(self) -> None:

        self.assertAlgSettings()

    def test_check_wrong_params(self) -> None:

        # use layer that is not corrently constructed LoS layer
        params = {"LoSLayer": QgsVectorLayer(get_data_path(file="no_target_los_wrong.gpkg"))}

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="Fields specific for LoS not found in current layer (los_type).")

        # try to extract horizon lines from local or global LoS
        params = {
            "LoSLayer": QgsVectorLayer(get_data_path(file="los_local.gpkg")),
            "HorizonType": 0
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message=
            "LoS must be of type `without target` to extract horizon lines but type `local` found."
        )

        params = {
            "LoSLayer": QgsVectorLayer(get_data_path(file="los_global.gpkg")),
            "HorizonType": 0
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message=
            "LoS must be of type `without target` to extract horizon lines but type `global` found."
        )

    def test_run_alg(self) -> None:

        output_path = get_data_path_results(file="horizons_lines_global.gpkg")

        params = {
            "LoSLayer": self.los_no_target,
            "HorizonType": 1,
            "OutputLayer": output_path,
            "CurvatureCorrections": True,
            "RefractionCoefficient": 0.13
        }

        self.assertRunAlgorithm(parameters=params)

        horizon_lines_layer = QgsVectorLayer(output_path)

        self.assertQgsVectorLayer(horizon_lines_layer,
                                  geom_type=QgsWkbTypes.LineStringZM,
                                  crs=self.los_no_target.sourceCrs())

        self.assertFieldNamesInQgsVectorLayer([
            FieldNames.HORIZON_TYPE, FieldNames.ID_OBSERVER, FieldNames.OBSERVER_X,
            FieldNames.OBSERVER_Y
        ], horizon_lines_layer)

        self.assertEqual(
            NamesConstants.HORIZON_GLOBAL,
            list(
                horizon_lines_layer.uniqueValues(horizon_lines_layer.fields().lookupField(
                    FieldNames.HORIZON_TYPE)))[0])

        output_path = get_data_path_results(file="horizon_lines_local.gpkg")

        params = {
            "LoSLayer": self.los_no_target,
            "HorizonType": 0,
            "OutputLayer": output_path,
            "CurvatureCorrections": True,
            "RefractionCoefficient": 0.13
        }

        self.assertRunAlgorithm(parameters=params)

        horizon_lines_layer = QgsVectorLayer(output_path)

        self.assertQgsVectorLayer(horizon_lines_layer,
                                  geom_type=QgsWkbTypes.LineStringZM,
                                  crs=self.los_no_target.sourceCrs())

        self.assertFieldNamesInQgsVectorLayer([
            FieldNames.HORIZON_TYPE, FieldNames.ID_OBSERVER, FieldNames.OBSERVER_X,
            FieldNames.OBSERVER_Y
        ], horizon_lines_layer)

        self.assertEqual(
            NamesConstants.HORIZON_MAX_LOCAL,
            list(
                horizon_lines_layer.uniqueValues(horizon_lines_layer.fields().lookupField(
                    FieldNames.HORIZON_TYPE)))[0])

        self.assertEqual(
            len(
                self.los_no_target.uniqueValues(self.los_no_target.fields().lookupField(
                    FieldNames.ID_OBSERVER))),
            len((horizon_lines_layer.uniqueValues(horizon_lines_layer.fields().lookupField(
                FieldNames.ID_OBSERVER)))))
