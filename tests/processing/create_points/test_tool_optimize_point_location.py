import pytest
from qgis.core import Qgis, QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsVectorLayer

from los_tools.processing.create_points.tool_optimize_point_location import OptimizePointLocationAlgorithm
from tests.custom_assertions import (
    assert_algorithm,
    assert_check_parameter_values,
    assert_field_names_exist,
    assert_layer,
    assert_parameter,
    assert_run,
)
from tests.utils import result_filename


def test_parameters() -> None:
    alg = OptimizePointLocationAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("InputRaster"), parameter_type="raster")
    assert_parameter(alg.parameterDefinition("InputLayer"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("Distance"), parameter_type="distance")
    assert_parameter(alg.parameterDefinition("MaskRaster"), parameter_type="raster")
    assert_parameter(alg.parameterDefinition("OutputLayer"), parameter_type="sink")


def test_alg_settings() -> None:
    alg = OptimizePointLocationAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_wrong_params(
    raster_multi_band: QgsRasterLayer,
    raster_small: QgsRasterLayer,
    layer_point_wgs84: QgsVectorLayer,
    raster_wrong_crs: QgsRasterLayer,
    layer_points: QgsVectorLayer,
) -> None:
    alg = OptimizePointLocationAlgorithm()
    alg.initAlgorithm()

    # multiband raster fail
    params = {"InputRaster": raster_multi_band}

    with pytest.raises(AssertionError, match="`Location optimization raster` can only have one band."):
        assert_check_parameter_values(alg, parameters=params)

    # observer layer with geographic coordinates
    params = {
        "InputRaster": raster_small,
        "InputLayer": layer_point_wgs84,
    }

    with pytest.raises(AssertionError, match="`Input point layer` crs must be projected."):
        assert_check_parameter_values(alg, parameters=params)
    # raster crs != observers crs
    params = {"InputRaster": raster_wrong_crs, "InputLayer": layer_points}

    with pytest.raises(
        AssertionError, match="`Input point layer` and `Location optimization raster` crs must be equal."
    ):
        assert_check_parameter_values(alg, parameters=params)

    # mask raster errors
    params = {
        "InputRaster": raster_small,
        "InputLayer": layer_points,
        "MaskRaster": raster_multi_band,
    }

    with pytest.raises(AssertionError, match="`Mask raster` can only have one band."):
        assert_check_parameter_values(alg, parameters=params)

    params = {
        "InputRaster": raster_small,
        "InputLayer": layer_points,
        "MaskRaster": raster_wrong_crs,
    }

    with pytest.raises(AssertionError, match="CRS for `Mask raster` and `Location optimization raster` must be equal."):
        assert_check_parameter_values(alg, parameters=params)


def test_run_alg(raster_small: QgsRasterLayer, layer_points: QgsVectorLayer) -> None:
    alg = OptimizePointLocationAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("points_optimized.gpkg")

    params = {
        "InputRaster": raster_small,
        "InputLayer": layer_points,
        "Distance": 10,
        "OutputLayer": output_path,
    }

    assert_run(alg, params)

    output_layer = QgsVectorLayer(output_path)

    assert_layer(output_layer, geom_type=Qgis.WkbType.Point, crs=layer_points.sourceCrs())

    assert layer_points.featureCount() == output_layer.featureCount()
