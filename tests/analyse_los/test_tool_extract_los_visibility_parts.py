from qgis.core import (QgsVectorLayer, QgsWkbTypes)

from los_tools.analyse_los.tool_extract_los_visibility_parts import ExtractLoSVisibilityPartsAlgorithm
from los_tools.constants.field_names import FieldNames

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase

from tests.utils_tests import (get_data_path, get_data_path_results)


class ExtractPointsLoSAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        super().setUp()

        self.los_global = QgsVectorLayer(get_data_path(file="los_global.gpkg"))

        self.los_local = QgsVectorLayer(get_data_path(file="los_local.gpkg"))

        self.los_no_target = QgsVectorLayer(get_data_path(file="no_target_los.gpkg"))

        self.alg = ExtractLoSVisibilityPartsAlgorithm()
        self.alg.initAlgorithm()

    def test_parameters(self) -> None:

        self.assertQgsProcessingParameter(self.alg.parameterDefinition("LoSLayer"),
                                          parameter_type="source")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("OutputLayer"),
                                          parameter_type="sink")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("CurvatureCorrections"),
                                          parameter_type="boolean",
                                          default_value=True)
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("RefractionCoefficient"),
                                          parameter_type="number",
                                          default_value=0.13)

    def test_alg_settings(self) -> None:

        self.assertAlgSettings()

    def test_check_wrong_params(self) -> None:

        # use layer that is not correctly constructed LoS layer
        params = {"LoSLayer": QgsVectorLayer(get_data_path(file="no_target_los_wrong.gpkg"))}

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="Fields specific for LoS not found in current layer (los_type).")

    def test_run_alg(self) -> None:

        output_path = get_data_path_results(file="los_parts.gpkg")

        params = {
            "LoSLayer": self.los_local,
            "OutputLayer": output_path,
            "CurvatureCorrections": True,
            "RefractionCoefficient": 0.13
        }

        self.assertRunAlgorithm(parameters=params)

        los_parts = QgsVectorLayer(output_path)

        self.assertQgsVectorLayer(los_parts,
                                  geom_type=QgsWkbTypes.MultiLineStringZ,
                                  crs=self.los_local.sourceCrs())

        self.assertFieldNamesInQgsVectorLayer(
            [FieldNames.ID_OBSERVER, FieldNames.ID_TARGET, FieldNames.VISIBLE], los_parts)

        self.assertEqual(los_parts.featureCount(), self.los_local.featureCount() * 2)

        output_path = get_data_path_results(file="los_parts.gpkg")

        params = {
            "LoSLayer": self.los_global,
            "OutputLayer": output_path,
            "CurvatureCorrections": True,
            "RefractionCoefficient": 0.13
        }

        self.assertRunAlgorithm(parameters=params)

        los_parts = QgsVectorLayer(output_path)

        self.assertQgsVectorLayer(los_parts,
                                  geom_type=QgsWkbTypes.MultiLineStringZ,
                                  crs=self.los_local.sourceCrs())

        self.assertFieldNamesInQgsVectorLayer(
            [FieldNames.ID_OBSERVER, FieldNames.ID_TARGET, FieldNames.VISIBLE], los_parts)

        self.assertEqual(los_parts.featureCount(), self.los_global.featureCount() * 2)

        output_path = get_data_path_results(file="los_parts.gpkg")

        params = {
            "LoSLayer": self.los_no_target,
            "OutputLayer": output_path,
            "CurvatureCorrections": True,
            "RefractionCoefficient": 0.13
        }

        self.assertRunAlgorithm(parameters=params)

        los_parts = QgsVectorLayer(output_path)

        self.assertQgsVectorLayer(los_parts,
                                  geom_type=QgsWkbTypes.MultiLineStringZ,
                                  crs=self.los_local.sourceCrs())

        self.assertFieldNamesInQgsVectorLayer(
            [FieldNames.ID_OBSERVER, FieldNames.ID_TARGET, FieldNames.VISIBLE], los_parts)

        self.assertEqual(los_parts.featureCount(), self.los_no_target.featureCount() * 2)
