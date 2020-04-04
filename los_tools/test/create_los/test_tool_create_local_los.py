import unittest

from qgis.core import (QgsVectorLayer,
                       QgsRasterLayer,
                       QgsFeatureRequest,
                       QgsProcessingFeedback,
                       QgsProcessingContext)
from qgis._core import QgsWkbTypes

from los_tools.create_los.tool_create_local_los import CreateLocalLosAlgorithm
from los_tools.constants.field_names import FieldNames

from los_tools.test.utils_tests import (print_alg_params,
                                        print_alg_outputs,
                                        get_data_path,
                                        get_data_path_results,
                                        get_qgis_app)


class CreateLocalLosAlgorithmTest(unittest.TestCase):

    def setUp(self) -> None:
        self.observers = QgsVectorLayer(get_data_path(file="points.gpkg"))
        self.observers_id = "id_point"
        self.observers_offset = "observ_offset"

        self.targets = QgsVectorLayer(get_data_path(file="single_point.gpkg"))
        self.targets_id = "id_point"
        self.targets_offset = "offset"

        self.dsm = QgsRasterLayer(get_data_path(file="dsm.tif"))

        self.output_path = get_data_path_results(file="los_local.gpkg")

        self.alg = CreateLocalLosAlgorithm()
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

    def test_parameters(self) -> None:
        param_dem_raster = self.alg.parameterDefinition("DemRaster")
        param_observers = self.alg.parameterDefinition("ObserverPoints")
        param_observers_id_field = self.alg.parameterDefinition("ObserverIdField")
        param_observers_offset_field = self.alg.parameterDefinition("ObserverOffset")
        param_targets = self.alg.parameterDefinition("TargetPoints")
        param_targets_id_field = self.alg.parameterDefinition("TargetIdField")
        param_targets_offset_field = self.alg.parameterDefinition("TargetOffset")
        param_line_density = self.alg.parameterDefinition("LineDensity")
        param_output_layer = self.alg.parameterDefinition("OutputLayer")

        self.assertEqual("raster", param_dem_raster.type())
        self.assertEqual("source", param_observers.type())
        self.assertEqual("field", param_observers_id_field.type())
        self.assertEqual("field", param_observers_offset_field.type())
        self.assertEqual("source", param_targets.type())
        self.assertEqual("field", param_targets_id_field.type())
        self.assertEqual("field", param_targets_offset_field.type())
        self.assertEqual("number", param_line_density.type())
        self.assertEqual("sink", param_output_layer.type())

        self.assertEqual("ObserverPoints", param_observers_id_field.parentLayerParameterName())
        self.assertEqual("ObserverPoints", param_observers_offset_field.parentLayerParameterName())
        self.assertEqual("TargetPoints", param_targets_id_field.parentLayerParameterName())
        self.assertEqual("TargetPoints", param_targets_offset_field.parentLayerParameterName())

        self.assertEqual(1, param_line_density.defaultValue())

    def test_check_wrong_params(self) -> None:

        # multiband raster fail
        params = {
            "DemRaster": QgsRasterLayer(get_data_path(file="raster_multiband.tif"))
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertFalse(can_run)
        self.assertIn("`Raster Layer DEM` can only have one band.", msg)

        # observer layer with geographic coordinates
        params = {
            "DemRaster": self.dsm,
            "ObserverPoints": QgsVectorLayer(get_data_path(file="single_point_wgs84.gpkg")),
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertFalse(can_run)
        self.assertIn("`Observers point layer` crs must be projected.", msg)

        # raster crs != observers crs
        params = {
            "DemRaster": QgsRasterLayer(get_data_path(file="dsm_epsg_5514.tif")),
            "ObserverPoints": self.observers
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertFalse(can_run)
        self.assertIn("`Observers point layer` and `Raster Layer DEM` crs must be equal.", msg)

        # observers crs != target crs
        params = {
            "DemRaster": self.dsm,
            "ObserverPoints": self.observers,
            "TargetPoints": QgsVectorLayer(get_data_path(file="points_epsg_5514.gpkg"))
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertFalse(can_run)
        self.assertIn("`Observers point layer` and `Targets point layer` crs must be equal.", msg)

    def test_run_alg(self) -> None:

        output_path = get_data_path_results(file="los_local.gpkg")

        params = {
            "DemRaster": self.dsm,
            "ObserverPoints": self.observers,
            "ObserverIdField": self.observers_id,
            "ObserverOffset": self.observers_offset,
            "TargetPoints": self.targets,
            "TargetIdField": self.targets_id,
            "TargetOffset": self.targets_offset,
            "LineDensity": 1,
            "OutputLayer": output_path
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)

        self.assertTrue(can_run)
        self.assertIn("OK", msg)

        self.alg.run(parameters=params, context=self.context, feedback=self.feedback)

        los_layer = QgsVectorLayer(output_path)

        self.assertEqual(QgsWkbTypes.LineStringZ, los_layer.wkbType())

        self.assertIn(FieldNames.LOS_TYPE, los_layer.fields().names())
        self.assertIn(FieldNames.ID_OBSERVER, los_layer.fields().names())
        self.assertIn(FieldNames.ID_TARGET, los_layer.fields().names())
        self.assertIn(FieldNames.OBSERVER_OFFSET, los_layer.fields().names())
        self.assertIn(FieldNames.TARGET_OFFSET, los_layer.fields().names())

        self.assertEqual(self.observers.featureCount() * self.targets.featureCount(),
                         los_layer.featureCount())

        observers_ids = list(self.observers.uniqueValues(self.observers.fields().lookupField(self.observers_id)))
        targets_ids = list(self.targets.uniqueValues(self.targets.fields().lookupField(self.targets_id)))

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
                    request.setFilterExpression("{} = '{}' AND {} = '{}'".
                                                format(FieldNames.ID_OBSERVER, observer_id,
                                                       FieldNames.ID_TARGET, target_id))
                    los_layer_feature = list(los_layer.getFeatures(request))[0]

                    self.assertAlmostEqual(observer_feature.geometry().distance(target_feature.geometry()),
                                           los_layer_feature.geometry().length(),
                                           places=9)

                    vertices = los_layer_feature.geometry().asPolyline()

                    self.assertEqual(vertices[0], observer_feature.geometry().asPoint())
                    self.assertEqual(vertices[-1], target_feature.geometry().asPoint())
