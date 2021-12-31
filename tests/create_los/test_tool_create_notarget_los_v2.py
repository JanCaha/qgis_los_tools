from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsVectorLayer, QgsRasterLayer)
from qgis._core import QgsWkbTypes

from los_tools.create_los.tool_create_notarget_los_v2 import CreateNoTargetLosAlgorithmV2
from los_tools.tools.tools_distances_for_sizes import ObjectDistancesAlgorithm
from los_tools.constants.field_names import FieldNames

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase

from tests.utils_tests import (get_data_path, get_data_path_results)


class CreateNoTargetLosAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        super().setUp()

        self.observers = QgsVectorLayer(get_data_path(file="points.gpkg"))
        self.observers_id = "id_point"
        self.observers_offset = "observ_offset"

        self.targets = QgsVectorLayer(get_data_path(file="points_in_direction.gpkg"))
        self.targets_id = "id_point"
        self.targets_origin_id = FieldNames.ID_ORIGINAL_POINT

        self.dsm = QgsRasterLayer(get_data_path(file="dsm.tif"))

        self.table = QgsVectorLayer(get_data_path(file="size_distance.xlsx"))

        self.output_path = get_data_path_results(file="los_no_target_v2.gpkg")

        self.alg = CreateNoTargetLosAlgorithmV2()
        self.alg.initAlgorithm()

    def test_parameters(self) -> None:

        self.assertQgsProcessingParameter(self.alg.parameterDefinition("DemRasters"),
                                          parameter_type="multilayer")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("LineSettingsTable"),
                                          parameter_type="source")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("ObserverPoints"),
                                          parameter_type="source")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("ObserverIdField"),
                                          parameter_type="field",
                                          parent_parameter="ObserverPoints")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("ObserverOffset"),
                                          parameter_type="field",
                                          parent_parameter="ObserverPoints")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("TargetPoints"),
                                          parameter_type="source")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("TargetIdField"),
                                          parameter_type="field",
                                          parent_parameter="TargetPoints")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("TargetDefinitionIdField"),
                                          parameter_type="field",
                                          parent_parameter="TargetPoints")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("OutputLayer"),
                                          parameter_type="sink")

    def test_check_wrong_params(self) -> None:

        # multiband raster fail
        params = {
            "DemRasters": [get_data_path(file="raster_multiband.tif")],
            'ObserverPoints': self.observers,
            'TargetPoints': self.targets
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params, message="`raster_multiband` can only have one band.")

        # observer layer with geographic coordinates
        params = {
            "DemRasters": [self.dsm],
            "ObserverPoints": QgsVectorLayer(get_data_path(file="single_point_wgs84.gpkg")),
            'TargetPoints': self.targets
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params, message="`Observers point layer` crs must be projected.")

        # raster crs != observers crs
        params = {
            "DemRasters": [get_data_path(file="dsm_epsg_5514.tif")],
            "ObserverPoints": self.observers,
            'TargetPoints': self.targets
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="`Observers point layer` and `dsm_epsg_5514` crs must be equal.")

        # observers crs != target crs
        params = {
            "DemRasters": [self.dsm],
            "ObserverPoints": self.observers,
            "TargetPoints": QgsVectorLayer(get_data_path(file="points_epsg_5514.gpkg"))
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="`Observers point layer` and `Targets point layer` crs must be equal.")

    def test_run_alg(self) -> None:

        params = {
            'DemRasters': [self.dsm],
            'LineSettingsTable': self.table,
            'ObserverPoints': self.observers,
            'ObserverIdField': self.observers_id,
            'ObserverOffset': self.observers_offset,
            'TargetPoints': self.targets,
            'TargetIdField': self.targets_id,
            'TargetDefinitionIdField': self.targets_origin_id,
            'OutputLayer': self.output_path
        }

        self.assertRunAlgorithm(parameters=params)

        los_layer = QgsVectorLayer(self.output_path)

        self.assertQgsVectorLayer(los_layer,
                                  geom_type=QgsWkbTypes.LineStringZ,
                                  crs=self.observers.sourceCrs())

        self.assertFieldNamesInQgsVectorLayer([
            FieldNames.LOS_TYPE, FieldNames.ID_OBSERVER, FieldNames.ID_TARGET,
            FieldNames.OBSERVER_OFFSET, FieldNames.AZIMUTH, FieldNames.OBSERVER_X,
            FieldNames.OBSERVER_Y
        ], los_layer)

        self.assertEqual(self.targets.featureCount(), los_layer.featureCount())
