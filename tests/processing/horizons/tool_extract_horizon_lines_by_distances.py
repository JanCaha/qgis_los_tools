import typing

import pytest
from qgis.core import Qgis, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.processing.horizons.tool_extract_horizon_lines_by_distances import ExtractHorizonLinesByDistanceAlgorithm
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
    alg = ExtractHorizonLinesByDistanceAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("LoSLayer"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("OutputLayer"), parameter_type="sink")
    assert_parameter(alg.parameterDefinition("CurvatureCorrections"), parameter_type="boolean", default_value=True)
    assert_parameter(alg.parameterDefinition("RefractionCoefficient"), parameter_type="number", default_value=0.13)
    assert_parameter(alg.parameterDefinition("Distances"), parameter_type="matrix")


def test_alg_settings() -> None:
    alg = ExtractHorizonLinesByDistanceAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_wrong_params(
    los_no_target_wrong: QgsVectorLayer, los_local: QgsVectorLayer, los_global: QgsVectorLayer
) -> None:
    alg = ExtractHorizonLinesByDistanceAlgorithm()
    alg.initAlgorithm()

    # use layer that is not corrently constructed LoS layer
    params = {"LoSLayer": los_no_target_wrong}

    with pytest.raises(AssertionError, match="Fields specific for LoS not found in current layer"):
        assert_check_parameter_values(alg, params)

    params = {"LoSLayer": los_local, "HorizonType": 0}

    with pytest.raises(
        AssertionError, match="LoS must be of type `without target` to extract horizon lines but type `local` found"
    ):
        assert_check_parameter_values(alg, params)

    params = {"LoSLayer": los_global, "HorizonType": 0}

    with pytest.raises(
        AssertionError, match="LoS must be of type `without target` to extract horizon lines but type `global` found"
    ):
        assert_check_parameter_values(alg, params)


def test_run_alg(los_no_target: QgsVectorLayer) -> None:
    alg = ExtractHorizonLinesByDistanceAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("horizon_lines.gpkg")

    distances = [10, 30, 50, 100, 200]
    params = {
        "LoSLayer": los_no_target,
        "Distances": distances,
        "OutputLayer": output_path,
        "CurvatureCorrections": True,
        "RefractionCoefficient": 0.13,
    }

    assert_run(alg, params)

    horizon_lines_layer = QgsVectorLayer(output_path)

    assert_layer(horizon_lines_layer, geom_type=Qgis.WkbType.LineStringZM, crs=los_no_target.sourceCrs())

    assert_field_names_exist(
        [FieldNames.HORIZON_DISTANCE, FieldNames.ID_OBSERVER, FieldNames.OBSERVER_X, FieldNames.OBSERVER_Y],
        horizon_lines_layer,
    )

    unique_ids = list(los_no_target.uniqueValues(los_no_target.fields().lookupField(FieldNames.ID_OBSERVER)))

    assert horizon_lines_layer.featureCount() == len(unique_ids) * len(distances)
