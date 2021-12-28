from qgis.core import (QgsVectorLayer)
from qgis._core import QgsWkbTypes

from los_tools.horizons.tool_extract_horizons import ExtractHorizonsAlgorithm
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase

from tests.utils_tests import (get_data_path,
                               get_data_path_results)


class ExtractHorizonsAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        super().setUp()

        self.los_global = QgsVectorLayer(get_data_path(file="los_global.gpkg"))

        self.los_local = QgsVectorLayer(get_data_path(file="los_local.gpkg"))

        self.alg = ExtractHorizonsAlgorithm()
        self.alg.initAlgorithm()

    def test_parameters(self) -> None:
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("LoSLayer"),
                                          parameter_type="source")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("HorizonType"),
                                          parameter_type="enum",
                                          default_value=2)
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("OutputLayer"),
                                          parameter_type="sink")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("CurvatureCorrections"),
                                          parameter_type="boolean",
                                          default_value=True)
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("RefractionCoefficient"),
                                          parameter_type="number",
                                          default_value=0.13)

    def test_check_wrong_params(self) -> None:

        # use layer that is not corrently constructed LoS layer
        params = {
            "LoSLayer": QgsVectorLayer(get_data_path(file="no_target_los_wrong.gpkg"))
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="Fields specific for LoS not found in current layer (los_type)."
        )

        # try to extract global horizon from local LoS
        params = {
            "LoSLayer": self.los_local,
            "HorizonType": 1
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="Cannot extract global horizon from local LoS."
        )

    def test_run_alg(self) -> None:

        output_path = get_data_path_results(file="horizons_local.gpkg")

        params = {
            "LoSLayer": self.los_local,
            "HorizonType": 0,
            "OutputLayer": output_path,
            "CurvatureCorrections": True,
            "RefractionCoefficient": 0.13
        }

        self.assertRunAlgorithm(parameters=params)

        horizon_layer = QgsVectorLayer(output_path)

        self.assertQgsVectorLayer(horizon_layer,
                                  geom_type=QgsWkbTypes.PointZ,
                                  crs=self.los_local.sourceCrs())

        self.assertFieldNamesInQgsVectorLayer([FieldNames.HORIZON_TYPE,
                                               FieldNames.ID_OBSERVER,
                                               FieldNames.ID_TARGET],
                                              horizon_layer)

        self.assertEqual(NamesConstants.HORIZON_LOCAL,
                         list(horizon_layer.uniqueValues(horizon_layer.fields().
                                                         lookupField(FieldNames.HORIZON_TYPE)))[0])

        output_path = get_data_path_results(file="horizons_global.gpkg")

        params = {
            "LoSLayer": self.los_global,
            "HorizonType": 1,
            "OutputLayer": output_path,
            "CurvatureCorrections": True,
            "RefractionCoefficient": 0.13
        }

        self.assertRunAlgorithm(parameters=params)

        horizon_layer = QgsVectorLayer(output_path)

        self.assertQgsVectorLayer(horizon_layer,
                                  geom_type=QgsWkbTypes.PointZ,
                                  crs=self.los_local.sourceCrs())

        self.assertFieldNamesInQgsVectorLayer([FieldNames.HORIZON_TYPE,
                                               FieldNames.ID_OBSERVER,
                                               FieldNames.ID_TARGET],
                                              horizon_layer)

        self.assertEqual(NamesConstants.HORIZON_GLOBAL,
                         list(horizon_layer.uniqueValues(horizon_layer.fields().
                                                         lookupField(FieldNames.HORIZON_TYPE)))[0])

        self.assertEqual(self.los_global.featureCount(),
                         horizon_layer.featureCount())
