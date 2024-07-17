import typing

import pytest
from qgis.core import Qgis, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.processing.analyse_los.tool_extract_points_los import ExtractPointsLoSAlgorithm
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
    alg = ExtractPointsLoSAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("LoSLayer"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("OutputLayer"), parameter_type="sink")
    assert_parameter(alg.parameterDefinition("CurvatureCorrections"), parameter_type="boolean", default_value=True)
    assert_parameter(alg.parameterDefinition("RefractionCoefficient"), parameter_type="number", default_value=0.13)
    assert_parameter(alg.parameterDefinition("OnlyVisiblePoints"), parameter_type="boolean", default_value=False)


def test_alg_settings() -> None:
    alg = ExtractPointsLoSAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_check_wrong_params(los_no_target_wrong: QgsVectorLayer) -> None:
    alg = ExtractPointsLoSAlgorithm()
    alg.initAlgorithm()

    # use layer that is not correctly constructed LoS layer
    params = {"LoSLayer": los_no_target_wrong}

    with pytest.raises(AssertionError, match="Fields specific for LoS not found in current layer"):
        assert_check_parameter_values(alg, params)


@pytest.mark.parametrize(
    "los_fixture_name,fields,extended_attributes",
    [
        ("los_local", [FieldNames.ID_OBSERVER, FieldNames.ID_TARGET, FieldNames.VISIBLE], False),
        (
            "los_no_target",
            [
                FieldNames.ANGLE_DIFF_GH,
                FieldNames.ELEVATION_DIFF_GH,
                FieldNames.ANGLE_DIFF_LH,
                FieldNames.ELEVATION_DIFF_LH,
            ],
            True,
        ),
    ],
)
def test_run_alg(los_fixture_name: str, fields: typing.List[str], extended_attributes: bool, request) -> None:
    los: QgsVectorLayer = request.getfixturevalue(los_fixture_name)

    alg = ExtractPointsLoSAlgorithm()
    alg.initAlgorithm()

    output_path_all = result_filename("points_los_local_all.gpkg")

    params = {
        "LoSLayer": los,
        "OutputLayer": output_path_all,
        "CurvatureCorrections": True,
        "RefractionCoefficient": 0.13,
        "OnlyVisiblePoints": False,
        "ExtendedAttributes": extended_attributes,
    }

    assert_run(alg, parameters=params)

    local_los_all_points = QgsVectorLayer(output_path_all)

    assert_layer(local_los_all_points, geom_type=Qgis.WkbType.PointZ, crs=los.sourceCrs())

    assert_field_names_exist(fields, local_los_all_points)

    output_path_visible = result_filename("points_los_local_visible.gpkg")

    params = {
        "LoSLayer": los,
        "OutputLayer": output_path_all,
        "CurvatureCorrections": True,
        "RefractionCoefficient": 0.13,
        "OnlyVisiblePoints": True,
        "ExtendedAttributes": extended_attributes,
    }

    assert_run(alg, parameters=params)

    local_los_visible_points = QgsVectorLayer(output_path_visible)

    assert local_los_visible_points.featureCount() < local_los_all_points.featureCount()
