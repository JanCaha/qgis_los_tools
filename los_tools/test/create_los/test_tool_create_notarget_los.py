from qgis.core import (QgsVectorLayer,
                       QgsRasterLayer,
                       QgsFeatureRequest)
from qgis._core import QgsWkbTypes

from los_tools.create_los.tool_create_notarget_los import CreateNoTargetLosAlgorithm
from los_tools.constants.field_names import FieldNames

from los_tools.test.AlgorithmTestCase import QgsProcessingAlgorithmTestCase

from los_tools.test.utils_tests import (get_data_path,
                                        get_data_path_results)


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

        self.output_path = get_data_path_results(file="los_no_target.gpkg")

        self.alg = CreateNoTargetLosAlgorithm()
        self.alg.initAlgorithm()

    def test_parameters(self) -> None:
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("DemRaster"),
                                          parameter_type="raster")
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
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("LineDensity"),
                                          parameter_type="distance",
                                          default_value=1)
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("MaxLoSLength"),
                                          parameter_type="distance",
                                          default_value=0)
        self.assertQgsProcessingParameter(self.alg.parameterDefinition("OutputLayer"),
                                          parameter_type="sink")

    def test_check_wrong_params(self) -> None:

        # multiband raster fail
        params = {
            "DemRaster": QgsRasterLayer(get_data_path(file="raster_multiband.tif"))
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="`Raster Layer DEM` can only have one band."
        )

        # observer layer with geographic coordinates
        params = {
            "DemRaster": self.dsm,
            "ObserverPoints": QgsVectorLayer(get_data_path(file="single_point_wgs84.gpkg")),
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="`Observers point layer` crs must be projected."
        )

        # raster crs != observers crs
        params = {
            "DemRaster": QgsRasterLayer(get_data_path(file="dsm_epsg_5514.tif")),
            "ObserverPoints": self.observers
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="`Observers point layer` and `Raster Layer DEM` crs must be equal."
        )

        # observers crs != target crs
        params = {
            "DemRaster": self.dsm,
            "ObserverPoints": self.observers,
            "TargetPoints": QgsVectorLayer(get_data_path(file="points_epsg_5514.gpkg"))
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="`Observers point layer` and `Targets point layer` crs must be equal."
        )

    def test_run_alg(self) -> None:

        params = {
            "DemRaster": self.dsm,
            "ObserverPoints": self.observers,
            "ObserverIdField": self.observers_id,
            "ObserverOffset": self.observers_offset,
            "TargetPoints": self.targets,
            "TargetIdField": self.targets_id,
            "TargetDefinitionIdField": self.targets_origin_id,
            "LineDensity": 1,
            "MaxLoSLength": 0,
            "OutputLayer": self.output_path,
        }

        self.assertRunAlgorithm(parameters=params)

        los_layer = QgsVectorLayer(self.output_path)

        self.assertQgsVectorLayer(los_layer,
                                  geom_type=QgsWkbTypes.LineStringZ,
                                  crs=self.observers.sourceCrs())

        self.assertFieldNamesInQgsVectorLayer([FieldNames.LOS_TYPE,
                                               FieldNames.ID_OBSERVER,
                                               FieldNames.ID_TARGET,
                                               FieldNames.OBSERVER_OFFSET,
                                               FieldNames.AZIMUTH,
                                               FieldNames.OBSERVER_X,
                                               FieldNames.OBSERVER_Y],
                                              los_layer)

        self.assertEqual(self.targets.featureCount(),
                         los_layer.featureCount())
