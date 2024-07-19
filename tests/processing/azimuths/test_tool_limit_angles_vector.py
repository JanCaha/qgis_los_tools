import typing
import unittest

import pytest
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.processing.azimuths.tool_limit_angles_vector import LimitAnglesAlgorithm
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
    alg = LimitAnglesAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("LoSLayer"), parameter_type="source")

    assert_parameter(alg.parameterDefinition("ObjectLayer"), parameter_type="source")

    assert_parameter(alg.parameterDefinition("OutputTable"), parameter_type="sink")


def test_alg_settings() -> None:
    alg = LimitAnglesAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_check_wrong_params(
    los_no_target_wrong: QgsVectorLayer,
    layer_polygon: QgsVectorLayer,
) -> None:
    alg = LimitAnglesAlgorithm()
    alg.initAlgorithm()

    params = {
        "LoSLayer": los_no_target_wrong,
        "ObjectLayer": layer_polygon,
        "OutputTable": result_filename("poly.gpkg"),
    }

    with pytest.raises(AssertionError, match="Fields specific for LoS without target not found in current layer"):
        assert_check_parameter_values(alg, params)


@pytest.mark.parametrize(
    "los_fixture_name,polygon_fixture_name",
    [
        (
            "los_no_target",
            "layer_polygon",
        ),
        (
            "los_no_target",
            "layer_polygon_crs_5514",
        ),
    ],
)
def test_run_alg(los_fixture_name: str, polygon_fixture_name: str, request) -> None:
    los: QgsVectorLayer = request.getfixturevalue(los_fixture_name)
    layer_polygon: QgsVectorLayer = request.getfixturevalue(polygon_fixture_name)

    fields = [
        FieldNames.AZIMUTH_MIN,
        FieldNames.AZIMUTH_MAX,
        FieldNames.ID_OBSERVER,
        FieldNames.ID_OBJECT,
    ]

    alg = LimitAnglesAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("angles.gpkg")

    params = {
        "LoSLayer": los,
        "ObjectLayerID": "fid",
        "ObjectLayer": layer_polygon,
        "OutputTable": output_path,
    }

    assert_run(alg, params)

    table = QgsVectorLayer(output_path)

    unique_ids = los.uniqueValues(los.fields().lookupField(FieldNames.ID_OBSERVER))

    assert table.featureCount() == len(unique_ids)

    assert_field_names_exist(
        fields,
        table,
    )
