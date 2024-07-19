import typing

import pytest
from qgis.core import Qgis, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.processing.horizons.tool_extract_horizons import ExtractHorizonsAlgorithm
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
    alg = ExtractHorizonsAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("LoSLayer"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("HorizonType"), parameter_type="enum")
    assert_parameter(alg.parameterDefinition("OutputLayer"), parameter_type="sink")
    assert_parameter(alg.parameterDefinition("CurvatureCorrections"), parameter_type="boolean", default_value=True)
    assert_parameter(alg.parameterDefinition("RefractionCoefficient"), parameter_type="number", default_value=0.13)


def test_alg_settings() -> None:
    alg = ExtractHorizonsAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_check_wrong_params(los_no_target_wrong: QgsVectorLayer, los_local: QgsVectorLayer) -> None:
    alg = ExtractHorizonsAlgorithm()
    alg.initAlgorithm()

    # use layer that is not corrently constructed LoS layer
    params = {"LoSLayer": los_no_target_wrong}

    with pytest.raises(AssertionError, match="Fields specific for LoS not found in current layer"):
        assert_check_parameter_values(alg, params)

    # try to extract global horizon from local LoS
    params = {"LoSLayer": los_local, "HorizonType": 1}

    with pytest.raises(AssertionError, match="Cannot extract global horizon from local LoS"):
        assert_check_parameter_values(alg, params)


@pytest.mark.parametrize(
    "los_fixture_name,horizon_type,additional_fields",
    [
        ("los_local", 0, []),
        ("los_global", 1, []),
        ("los_no_target", 0, [FieldNames.AZIMUTH]),
        ("los_no_target", 2, [FieldNames.AZIMUTH]),
    ],
)
def test_run_alg(los_fixture_name: str, horizon_type: int, additional_fields: typing.List[str], request) -> None:
    alg = ExtractHorizonsAlgorithm()
    alg.initAlgorithm()

    los: QgsVectorLayer = request.getfixturevalue(los_fixture_name)

    horizon_result = NamesConstants.HORIZON_LOCAL
    if horizon_type == 1:
        horizon_result = NamesConstants.HORIZON_GLOBAL
    if horizon_type == 2:
        horizon_result = NamesConstants.HORIZON_GLOBAL

    output_path = result_filename("horizons_local.gpkg")

    params = {
        "LoSLayer": los,
        "HorizonType": horizon_type,
        "OutputLayer": output_path,
        "CurvatureCorrections": True,
        "RefractionCoefficient": 0.13,
    }

    assert_run(alg, params)

    horizon_layer = QgsVectorLayer(output_path)

    assert_layer(horizon_layer, geom_type=Qgis.WkbType.PointZ, crs=los.sourceCrs())
    assert_field_names_exist(
        [FieldNames.HORIZON_TYPE, FieldNames.ID_OBSERVER, FieldNames.ID_TARGET] + additional_fields, horizon_layer
    )

    assert (
        horizon_result
        == sorted(list(horizon_layer.uniqueValues(horizon_layer.fields().lookupField(FieldNames.HORIZON_TYPE))))[0]
    )
