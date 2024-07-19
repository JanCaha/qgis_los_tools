import typing

import pytest
from qgis.core import (
    Qgis,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsVectorLayer,
)

from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.processing.horizons.tool_extract_horizon_lines import ExtractHorizonLinesAlgorithm
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
    alg = ExtractHorizonLinesAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("LoSLayer"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("HorizonType"), parameter_type="enum")
    assert_parameter(alg.parameterDefinition("OutputLayer"), parameter_type="sink")
    assert_parameter(alg.parameterDefinition("CurvatureCorrections"), parameter_type="boolean", default_value=True)
    assert_parameter(alg.parameterDefinition("RefractionCoefficient"), parameter_type="number", default_value=0.13)


def test_alg_settings() -> None:
    alg = ExtractHorizonLinesAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_wrong_params(
    los_no_target_wrong: QgsVectorLayer, los_local: QgsVectorLayer, los_global: QgsVectorLayer
) -> None:
    alg = ExtractHorizonLinesAlgorithm()
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


@pytest.mark.parametrize(
    "los_fixture_name,horizon_type",
    [
        ("los_no_target", 0),
        ("los_no_target", 1),
    ],
)
def test_run_alg(los_fixture_name: str, horizon_type: int, request) -> None:
    alg = ExtractHorizonLinesAlgorithm()
    alg.initAlgorithm()

    los: QgsVectorLayer = request.getfixturevalue(los_fixture_name)

    horizon_result = NamesConstants.HORIZON_MAX_LOCAL
    if horizon_type == 1:
        horizon_result = NamesConstants.HORIZON_GLOBAL

    output_path = result_filename("horizon_lines.gpkg")

    params = {
        "LoSLayer": los,
        "HorizonType": horizon_type,
        "OutputLayer": output_path,
        "CurvatureCorrections": True,
        "RefractionCoefficient": 0.13,
    }

    assert_run(alg, params)

    horizon_lines_layer = QgsVectorLayer(output_path)

    assert_layer(horizon_lines_layer, geom_type=Qgis.WkbType.LineStringZM, crs=los.sourceCrs())

    assert_field_names_exist(
        [FieldNames.HORIZON_TYPE, FieldNames.ID_OBSERVER, FieldNames.OBSERVER_X, FieldNames.OBSERVER_Y],
        horizon_lines_layer,
    )
    assert (
        horizon_result
        == sorted(
            list(horizon_lines_layer.uniqueValues(horizon_lines_layer.fields().lookupField(FieldNames.HORIZON_TYPE)))
        )[0]
    )
