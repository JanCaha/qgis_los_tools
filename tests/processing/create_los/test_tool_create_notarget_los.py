import pytest
from qgis.core import Qgis, QgsRasterLayer, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.processing.create_los.tool_create_notarget_los import CreateNoTargetLosAlgorithm
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
ORIGINAL_POINT_ID = "id_original_point"


def test_parameters() -> None:
    alg = CreateNoTargetLosAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("DemRasters"), parameter_type="multilayer")
    assert_parameter(alg.parameterDefinition("LineSettingsTable"), parameter_type="vector")
    assert_parameter(alg.parameterDefinition("ObserverPoints"), parameter_type="source")
    assert_parameter(
        alg.parameterDefinition("ObserverIdField"), parameter_type="field", parent_parameter="ObserverPoints"
    )
    assert_parameter(
        alg.parameterDefinition("ObserverOffset"), parameter_type="field", parent_parameter="ObserverPoints"
    )
    assert_parameter(alg.parameterDefinition("TargetPoints"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("TargetIdField"), parameter_type="field", parent_parameter="TargetPoints")
    assert_parameter(
        alg.parameterDefinition("TargetDefinitionIdField"), parameter_type="field", parent_parameter="TargetPoints"
    )
    assert_parameter(alg.parameterDefinition("OutputLayer"), parameter_type="sink")


def test_alg_settings() -> None:
    alg = CreateNoTargetLosAlgorithm()
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
    alg = CreateNoTargetLosAlgorithm()
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
        "TargetPoints": layer_point,
    }

    with pytest.raises(AssertionError, match="`Observers point layer` crs must be projected."):
        assert_check_parameter_values(alg, params)

    # raster crs != observers crs
    params = {
        "DemRasters": [raster_wrong_crs],
        "ObserverPoints": layer_points,
        "TargetPoints": layer_point,
    }

    with pytest.raises(AssertionError, match="Provided crs template and raster layers crs must be equal"):
        assert_check_parameter_values(alg, params)

    # observers crs != target crs
    params = {
        "DemRasters": [raster_small],
        "ObserverPoints": layer_points,
        "TargetPoints": layer_points_epsg5514,
    }

    with pytest.raises(AssertionError, match="`Observers point layer` and `Targets point layer` crs must be equal."):
        assert_check_parameter_values(alg, params)


def test_run_alg(
    raster_small: QgsRasterLayer,
    layer_size_distance: QgsVectorLayer,
    layer_points: QgsVectorLayer,
    layer_points_in_direction: QgsVectorLayer,
) -> None:
    alg = CreateNoTargetLosAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("los_no_target.gpkg")

    params = {
        "DemRasters": [raster_small],
        "LineSettingsTable": layer_size_distance,
        "ObserverPoints": layer_points,
        "ObserverIdField": OBSERVERS_ID,
        "ObserverOffset": OBSERVERS_OFFSET,
        "TargetPoints": layer_points_in_direction,
        "TargetIdField": TARGETS_ID,
        "TargetDefinitionIdField": ORIGINAL_POINT_ID,
        "OutputLayer": output_path,
    }

    assert_run(alg, params)

    los_layer = QgsVectorLayer(output_path)

    assert_layer(los_layer, geom_type=Qgis.WkbType.LineStringZ, crs=layer_points.sourceCrs())

    assert_field_names_exist(
        [
            FieldNames.LOS_TYPE,
            FieldNames.ID_OBSERVER,
            FieldNames.ID_TARGET,
            FieldNames.OBSERVER_OFFSET,
            FieldNames.AZIMUTH,
            FieldNames.OBSERVER_X,
            FieldNames.OBSERVER_Y,
        ],
        los_layer,
    )

    assert layer_points_in_direction.featureCount() == los_layer.featureCount()
