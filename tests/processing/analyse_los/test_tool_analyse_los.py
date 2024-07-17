import typing

import pytest
from qgis.core import Qgis, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.processing.analyse_los.tool_analyse_los import AnalyseLosAlgorithm
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
    alg = AnalyseLosAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("LoSLayer"), parameter_type="source")

    assert_parameter(alg.parameterDefinition("CurvatureCorrections"), parameter_type="boolean", default_value=True)

    assert_parameter(alg.parameterDefinition("RefractionCoefficient"), parameter_type="number", default_value=0.13)


def test_alg_settings() -> None:
    alg = AnalyseLosAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_check_wrong_params(los_no_target_wrong: QgsVectorLayer) -> None:
    alg = AnalyseLosAlgorithm()
    alg.initAlgorithm()

    # use layer that is not correctly constructed LoS layer
    params = {"LoSLayer": los_no_target_wrong}

    with pytest.raises(AssertionError, match="Fields specific for LoS not found in current layer"):
        assert_check_parameter_values(alg, params)


@pytest.mark.parametrize(
    "los_fixture_name,fields",
    [
        (
            "los_local",
            [
                FieldNames.VISIBLE,
                FieldNames.VIEWING_ANGLE,
                FieldNames.ELEVATION_DIFF,
                FieldNames.ANGLE_DIFF_LH,
                FieldNames.ELEVATION_DIFF_LH,
                FieldNames.SLOPE_DIFFERENCE_LH,
                FieldNames.HORIZON_COUNT,
                FieldNames.DISTANCE_LH,
            ],
        ),
        (
            "los_global",
            [
                FieldNames.VISIBLE,
                FieldNames.ANGLE_DIFF_GH,
                FieldNames.ELEVATION_DIFF_GH,
                FieldNames.HORIZON_COUNT_BEHIND,
                FieldNames.DISTANCE_GH,
            ],
        ),
        (
            "los_no_target",
            [
                FieldNames.MAXIMAL_VERTICAL_ANGLE,
                FieldNames.DISTANCE_GH,
                FieldNames.DISTANCE_LH,
                FieldNames.VERTICAL_ANGLE_LH,
            ],
        ),
    ],
)
def test_run_alg(los_fixture_name: str, fields: typing.List[str], request) -> None:
    los: QgsVectorLayer = request.getfixturevalue(los_fixture_name)

    alg = AnalyseLosAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("los_local_analysed.gpkg")

    params = {"LoSLayer": los, "OutputLayer": output_path}

    assert_run(alg, params)

    output_layer = QgsVectorLayer(output_path)

    assert_layer(output_layer, geom_type=Qgis.WkbType.LineStringZ, crs=los.sourceCrs())

    assert_field_names_exist(
        fields,
        output_layer,
    )
