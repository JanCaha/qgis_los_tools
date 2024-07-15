import pytest
from qgis.core import (
    Qgis,
    QgsFeatureRequest,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsRasterLayer,
    QgsVectorLayer,
)

from los_tools.constants.field_names import FieldNames
from los_tools.processing.create_los.tool_create_local_los import CreateLocalLosAlgorithm
from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase
from tests.custom_assertions import (
    assert_algorithm,
    assert_check_parameter_values,
    assert_field_names_exist,
    assert_layer,
    assert_parameter,
    assert_run,
)
from tests.utils import result_filename

OBSERVERS_ID = "id_point"
OBSERVERS_OFFSET = "observ_offset"
TARGETS_ID = "id_point"
TARGETS_OFFSET = "offset"


def test_parameters() -> None:
    alg = CreateLocalLosAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("DemRasters"), parameter_type="multilayer")
    assert_parameter(alg.parameterDefinition("ObserverPoints"), parameter_type="source")
    assert_parameter(
        alg.parameterDefinition("ObserverIdField"), parameter_type="field", parent_parameter="ObserverPoints"
    )
    assert_parameter(
        alg.parameterDefinition("ObserverOffset"), parameter_type="field", parent_parameter="ObserverPoints"
    )
    assert_parameter(alg.parameterDefinition("TargetPoints"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("TargetIdField"), parameter_type="field", parent_parameter="TargetPoints")
    assert_parameter(alg.parameterDefinition("TargetOffset"), parameter_type="field", parent_parameter="TargetPoints")
    assert_parameter(alg.parameterDefinition("LineDensity"), parameter_type="distance", default_value=1)
    assert_parameter(alg.parameterDefinition("OutputLayer"), parameter_type="sink")


def test_alg_settings() -> None:
    alg = CreateLocalLosAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_wrong_params(
    raster_small: QgsRasterLayer,
    raster_multi_band: QgsRasterLayer,
    raster_wrong_crs: QgsRasterLayer,
    layer_points: QgsVectorLayer,
    layer_point: QgsVectorLayer,
    layer_point_wgs84: QgsVectorLayer,
    layer_points_epsg5514: QgsVectorLayer,
) -> None:
    alg = CreateLocalLosAlgorithm()
    alg.initAlgorithm()

    # multiband raster fail
    params = {
        "DemRasters": [raster_multi_band],
        "ObserverPoints": layer_points,
        "TargetPoints": layer_point,
    }

    with pytest.raises(AssertionError, match="Rasters can only have one band"):
        assert_check_parameter_values(alg, params)

    # observer layer with geographic coordinates
    params = {
        "DemRasters": [raster_small],
        "ObserverPoints": layer_point_wgs84,
    }

    with pytest.raises(AssertionError, match="`Observers point layer` crs must be projected."):
        assert_check_parameter_values(alg, params)

    # raster crs != observers crs
    params = {
        "DemRasters": [raster_wrong_crs],
        "ObserverPoints": layer_points,
        "TargetPoints": layer_point,
        "ObserverIdField": OBSERVERS_ID,
        "ObserverOffset": OBSERVERS_OFFSET,
        "TargetIdField": TARGETS_ID,
        "TargetOffset": TARGETS_OFFSET,
    }

    with pytest.raises(AssertionError, match="Provided crs template and raster layers crs must be equal"):
        assert_check_parameter_values(alg, params)

    # observers crs != target crs
    params = {
        "DemRasters": [raster_small],
        "ObserverPoints": layer_points,
        "TargetPoints": layer_points_epsg5514,
        "ObserverIdField": OBSERVERS_ID,
        "ObserverOffset": OBSERVERS_OFFSET,
        "TargetIdField": TARGETS_ID,
        "TargetOffset": TARGETS_OFFSET,
    }

    with pytest.raises(AssertionError, match="`Observers point layer` and `Targets point layer` crs must be equal."):
        assert_check_parameter_values(alg, params)


def test_run_alg(raster_small: QgsRasterLayer, layer_points: QgsVectorLayer, layer_point: QgsVectorLayer) -> None:

    alg = CreateLocalLosAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("los_local.gpkg")

    params = {
        "DemRasters": [raster_small],
        "ObserverPoints": layer_points,
        "ObserverIdField": OBSERVERS_ID,
        "ObserverOffset": OBSERVERS_OFFSET,
        "TargetPoints": layer_point,
        "TargetIdField": TARGETS_ID,
        "TargetOffset": TARGETS_OFFSET,
        "LineDensity": 1,
        "OutputLayer": output_path,
    }

    assert_run(alg, parameters=params)

    los_layer = QgsVectorLayer(output_path)

    assert_layer(los_layer, geom_type=Qgis.WkbType.LineStringZ, crs=layer_points.sourceCrs())

    assert_field_names_exist(
        [
            FieldNames.LOS_TYPE,
            FieldNames.ID_OBSERVER,
            FieldNames.ID_OBSERVER,
            FieldNames.ID_TARGET,
            FieldNames.OBSERVER_OFFSET,
            FieldNames.TARGET_OFFSET,
        ],
        los_layer,
    )

    assert layer_points.featureCount() * layer_point.featureCount() == los_layer.featureCount()

    observers_ids = list(layer_points.uniqueValues(layer_points.fields().lookupField(OBSERVERS_ID)))
    targets_ids = list(layer_point.uniqueValues(layer_point.fields().lookupField(TARGETS_ID)))

    for observer_id in observers_ids:
        for target_id in targets_ids:

            request = QgsFeatureRequest()
            request.setFilterExpression(f"{OBSERVERS_ID} = '{observer_id}'")
            observer_feature = list(layer_points.getFeatures(request))[0]

            request = QgsFeatureRequest()
            request.setFilterExpression(f"{TARGETS_ID} = '{target_id}'")
            target_feature = list(layer_point.getFeatures(request))[0]

            request = QgsFeatureRequest()
            request.setFilterExpression(
                f"{FieldNames.ID_OBSERVER} = '{observer_id}' AND {FieldNames.ID_TARGET} = '{target_id}'"
            )
            los_layer_feature = list(los_layer.getFeatures(request))[0]

            assert observer_feature.geometry().distance(target_feature.geometry()) == pytest.approx(
                los_layer_feature.geometry().length()
            )

            vertices = los_layer_feature.geometry().asPolyline()

            assert vertices[0] == observer_feature.geometry().asPoint()
            assert vertices[-1] == target_feature.geometry().asPoint()
