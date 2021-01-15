from qgis.core import (QgsVectorLayer)
from qgis._core import QgsWkbTypes

from los_tools.analyse_los.tool_analyse_los import AnalyseLosAlgorithm
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants

from los_tools.test.AlgorithmTestCase import QgsProcessingAlgorithmTestCase

from los_tools.test.utils_tests import (get_data_path,
                                        get_data_path_results)

from los_tools.test.utils_tests import get_qgis_app

QGIS_APP = get_qgis_app()


class AnalyseLosAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        super().setUp()

        self.los_global = QgsVectorLayer(get_data_path(file="los_global.gpkg"))

        self.los_local = QgsVectorLayer(get_data_path(file="los_local.gpkg"))

        self.los_no_target = QgsVectorLayer(get_data_path(file="no_target_los.gpkg"))

        self.alg = AnalyseLosAlgorithm()
        self.alg.initAlgorithm()

    def test_parameters(self) -> None:
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("LoSLayer"),
                                          parameter_type="source")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("CurvatureCorrections"),
                                          parameter_type="boolean",
                                          default_value=True)
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("RefractionCoefficient"),
                                          parameter_type="number",
                                          default_value=0.13)

    def test_check_wrong_params(self) -> None:

        # use layer that is not correctly constructed LoS layer
        params = {
            "LoSLayer": QgsVectorLayer(get_data_path(file="no_target_los_wrong.gpkg"))
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="Fields specific for LoS not found in current layer"
        )

    def test_run_alg(self) -> None:

        output_path = get_data_path_results(file="los_local_analysed.gpkg")

        params = {
            "LoSLayer": self.los_local,
            "OutputLayer": output_path
        }

        self.assertRunAlgorithm(parameters=params)

        self.assertFieldNamesInQgsVectorLayer([FieldNames.VISIBLE,
                                               FieldNames.VIEWING_ANGLE,
                                               FieldNames.ELEVATION_DIFF,
                                               FieldNames.ANGLE_DIFF_LH,
                                               FieldNames.ELEVATION_DIFF_LH,
                                               FieldNames.SLOPE_DIFFERENCE_LH,
                                               FieldNames.HORIZON_COUNT,
                                               FieldNames.DISTANCE_LH],
                                              self.los_local)

        output_path = get_data_path_results(file="los_global_analysed.gpkg")

        params = {
            "LoSLayer": self.los_global,
            "OutputLayer": output_path
        }

        self.assertRunAlgorithm(parameters=params)

        self.assertFieldNamesInQgsVectorLayer([FieldNames.VISIBLE,
                                               FieldNames.ANGLE_DIFF_GH,
                                               FieldNames.ELEVATION_DIFF_GH,
                                               FieldNames.HORIZON_COUNT_BEHIND,
                                               FieldNames.DISTANCE_GH],
                                              self.los_global)

        output_path = get_data_path_results(file="los_notarget_analysed.gpkg")

        params = {
            "LoSLayer": self.los_no_target,
            "OutputLayer": output_path
        }

        self.assertRunAlgorithm(parameters=params)

        self.assertFieldNamesInQgsVectorLayer([FieldNames.MAXIMAL_VERTICAL_ANGLE,
                                               FieldNames.DISTANCE_GH,
                                               FieldNames.DISTANCE_LH,
                                               FieldNames.VERTICAL_ANGLE_LH],
                                              self.los_no_target)
