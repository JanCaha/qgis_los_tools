from qgis.core import (QgsVectorLayer)
from qgis._core import QgsWkbTypes

from los_tools.tools.tool_extract_points_los import ExtractPointsLoSAlgorithm
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants

from los_tools.test.AlgorithmTestCase import QgsProcessingAlgorithmTestCase

from los_tools.test.utils_tests import (get_data_path,
                                        get_data_path_results)


class ExtractPointsLoSAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        super().setUp()

        self.los_global = QgsVectorLayer(get_data_path(file="los_global.gpkg"))

        self.los_local = QgsVectorLayer(get_data_path(file="los_local.gpkg"))

        self.los_no_target = QgsVectorLayer(get_data_path(file="no_target_los.gpkg"))

        self.alg = ExtractPointsLoSAlgorithm()
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
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("OnlyVisiblePoints"),
                                          parameter_type="boolean",
                                          default_value=False)

    def test_check_wrong_params(self) -> None:

        # use layer that is not correctly constructed LoS layer
        params = {
            "LoSLayer": QgsVectorLayer(get_data_path(file="no_target_los_wrong.gpkg"))
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="Fields specific for LoS not found in current layer (los_type)."
        )

    def test_run_alg(self) -> None:

        output_path = get_data_path_results(file="points_los_local_all.gpkg")

        params = {
            "LoSLayer": self.los_local,
            "OutputLayer": output_path,
            "CurvatureCorrections": True,
            "RefractionCoefficient": 0.13,
            "OnlyVisiblePoints": False
        }

        self.assertRunAlgorithm(parameters=params)

        local_los_all_points = QgsVectorLayer(output_path)

        self.assertQgsVectorLayer(local_los_all_points,
                                  geom_type=QgsWkbTypes.PointZ,
                                  crs=self.los_local.sourceCrs())

        self.assertFieldNamesInQgsVectorLayer([FieldNames.ID_OBSERVER,
                                               FieldNames.ID_TARGET,
                                               FieldNames.VISIBLE],
                                              local_los_all_points)

        output_path = get_data_path_results(file="points_los_local_visible.gpkg")

        params = {
            "LoSLayer": self.los_local,
            "OutputLayer": output_path,
            "CurvatureCorrections": True,
            "RefractionCoefficient": 0.13,
            "OnlyVisiblePoints": True
        }

        self.assertRunAlgorithm(parameters=params)

        local_los_visible_points = QgsVectorLayer(output_path)

        self.assertTrue(local_los_visible_points.featureCount() < local_los_all_points.featureCount())
