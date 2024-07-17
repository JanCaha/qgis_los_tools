import typing

import pytest
from qgis.core import Qgis, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.processing.to_table.tool_export_los import ExportLoSAlgorithm
from tests.custom_assertions import (
    assert_algorithm,
    assert_check_parameter_values,
    assert_field_names_exist,
    assert_parameter,
    assert_run,
)
from tests.utils import result_filename


def test_parameters() -> None:
    alg = ExportLoSAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("LoSLayer"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("CurvatureCorrections"), parameter_type="boolean", default_value=True)
    assert_parameter(alg.parameterDefinition("RefractionCoefficient"), parameter_type="number", default_value=0.13)
    assert_parameter(alg.parameterDefinition("OutputFile"), parameter_type="sink")


def test_alg_settings() -> None:
    alg = ExportLoSAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_check_wrong_params(los_no_target_wrong: QgsVectorLayer) -> None:
    alg = ExportLoSAlgorithm()
    alg.initAlgorithm()

    # use layer that is not correctly constructed LoS layer
    params = {"LoSLayer": los_no_target_wrong}

    with pytest.raises(AssertionError, match="Fields specific for LoS not found in current layer"):
        assert_check_parameter_values(alg, params)


result_fields = [
    FieldNames.ID_LOS,
    FieldNames.ID_OBSERVER,
    FieldNames.OBSERVER_OFFSET,
    FieldNames.CSV_OBSERVER_DISTANCE,
    FieldNames.CSV_ELEVATION,
    FieldNames.CSV_VISIBLE,
    FieldNames.CSV_HORIZON,
]


@pytest.mark.parametrize(
    "los_fixture_name,fields",
    [
        (
            "los_no_target",
            result_fields,
        ),
        (
            "los_local",
            result_fields
            + [
                FieldNames.ID_TARGET,
                FieldNames.TARGET_OFFSET,
            ],
        ),
        (
            "los_global",
            result_fields
            + [
                FieldNames.ID_TARGET,
                FieldNames.TARGET_OFFSET,
                FieldNames.TARGET_X,
                FieldNames.TARGET_Y,
                FieldNames.CSV_TARGET,
            ],
        ),
    ],
)
def test_run_alg(los_fixture_name: str, fields: typing.List[str], request) -> None:
    los: QgsVectorLayer = request.getfixturevalue(los_fixture_name)

    alg = ExportLoSAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("exported.gpkg")

    params = {
        "LoSLayer": los,
        "OutputFile": output_path,
        "CurvatureCorrections": True,
        "RefractionCoefficient": 0.13,
    }

    assert_run(alg, parameters=params)

    export_layer = QgsVectorLayer(output_path)

    assert export_layer.wkbType() == Qgis.WkbType.NoGeometry

    assert_field_names_exist(fields, export_layer)
