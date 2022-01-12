from qgis.core import (QgsVectorLayer, QgsRasterLayer, QgsFeatureRequest)
from qgis._core import QgsWkbTypes

from los_tools.create_los.tool_create_global_los import CreateGlobalLosAlgorithm
from los_tools.constants.field_names import FieldNames
from los_tools.tools.util_functions import get_diagonal_size

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase
from tests.utils_tests import (get_data_path, get_data_path_results)


class CreateGlobalLosAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        super().setUp()

        self.observers = QgsVectorLayer(get_data_path(file="points.gpkg"))
        self.observers_id = "id_point"
        self.observers_offset = "observ_offset"

        self.targets = QgsVectorLayer(get_data_path(file="single_point.gpkg"))
        self.targets_id = "id_point"
        self.targets_offset = "offset"

        self.dsm = QgsRasterLayer(get_data_path(file="dsm.tif"))

        self.output_path = get_data_path_results(file="los_global.gpkg")

        self.alg = CreateGlobalLosAlgorithm()
        self.alg.initAlgorithm()

    def test_parameters(self) -> None:

        self.assertQgsProcessingParameter(self.alg.parameterDefinition("DemRasters"),
                                          parameter_type="multilayer")
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
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("TargetOffset"),
                                          parameter_type="field",
                                          parent_parameter="TargetPoints")
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("LineDensity"),
                                          parameter_type="distance",
                                          default_value=1)
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("OutputLayer"),
                                          parameter_type="sink")

    def test_alg_settings(self) -> None:

        self.assertAlgSettings()

    def test_check_wrong_params(self) -> None:

        # multiband raster fail
        params = {
            "DemRasters": [QgsRasterLayer(get_data_path(file="raster_multiband.tif"))],
            "ObserverPoints": self.observers,
            "TargetPoints": self.targets
        }

        self.assertCheckParameterValuesRaisesMessage(parameters=params,
                                                     message="Rasters can only have one band")

        # observer layer with geographic coordinates
        params = {
            "DemRasters": [self.dsm],
            "ObserverPoints": QgsVectorLayer(get_data_path(file="single_point_wgs84.gpkg")),
            "TargetPoints": self.targets
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params, message="`Observers point layer` crs must be projected.")

        # raster crs != observers crs
        params = {
            "DemRasters": [QgsRasterLayer(get_data_path(file="dsm_epsg_5514.tif"))],
            "ObserverPoints": self.observers,
            "TargetPoints": self.targets
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message=
            "`Observers point layer` and raster layers crs must be equal. Right now they are not.")

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
            "DemRasters": [self.dsm],
            "ObserverPoints": self.observers,
            "ObserverIdField": self.observers_id,
            "ObserverOffset": self.observers_offset,
            "TargetPoints": self.targets,
            "TargetIdField": self.targets_id,
            "TargetOffset": self.targets_offset,
            "LineDensity": 1,
            "OutputLayer": self.output_path
        }

        self.assertRunAlgorithm(parameters=params)

        los_layer = QgsVectorLayer(self.output_path)

        self.assertQgsVectorLayer(los_layer,
                                  geom_type=QgsWkbTypes.LineStringZ,
                                  crs=self.observers.sourceCrs())

        self.assertFieldNamesInQgsVectorLayer([
            FieldNames.LOS_TYPE, FieldNames.ID_OBSERVER, FieldNames.ID_TARGET,
            FieldNames.OBSERVER_OFFSET, FieldNames.TARGET_OFFSET
        ], los_layer)

        self.assertEqual(self.observers.featureCount() * self.targets.featureCount(),
                         los_layer.featureCount())

        observers_ids = list(
            self.observers.uniqueValues(self.observers.fields().lookupField(self.observers_id)))
        targets_ids = list(
            self.targets.uniqueValues(self.targets.fields().lookupField(self.targets_id)))

        dsm_max_size = get_diagonal_size(self.dsm.dataProvider())
        dsm_extent = self.dsm.dataProvider().extent()

        for observer_id in observers_ids:
            for target_id in targets_ids:
                with self.subTest(observer_id=observer_id, target_id=target_id):

                    request = QgsFeatureRequest()
                    request.setFilterExpression("{} = '{}'".format(self.observers_id, observer_id))
                    observer_feature = list(self.observers.getFeatures(request))[0]

                    request = QgsFeatureRequest()
                    request.setFilterExpression("{} = '{}'".format(self.targets_id, target_id))
                    target_feature = list(self.targets.getFeatures(request))[0]

                    request = QgsFeatureRequest()
                    request.setFilterExpression("{} = '{}' AND {} = '{}'".format(
                        FieldNames.ID_OBSERVER, observer_id, FieldNames.ID_TARGET, target_id))
                    los_layer_feature = list(los_layer.getFeatures(request))[0]

                    self.assertTrue(observer_feature.geometry().distance(target_feature.geometry())
                                    < los_layer_feature.geometry().length())

                    self.assertTrue(los_layer_feature.geometry().length() < dsm_max_size)

                    vertices = los_layer_feature.geometry().asPolyline()

                    self.assertEqual(observer_feature.geometry().asPoint(), vertices[0])
                    self.assertIn(target_feature.geometry().asPoint(), vertices)

                    self.assertTrue(dsm_extent.contains(target_feature.geometry().boundingBox()))
