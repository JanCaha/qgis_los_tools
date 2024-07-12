import pytest
from qgis.core import Qgis, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.processing.to_table.tool_export_horizon_lines import ExportHorizonLinesAlgorithm
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
    alg = ExportHorizonLinesAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("HorizonLinesLayer"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("OutputFile"), parameter_type="sink")


def test_alg_settings() -> None:
    alg = ExportHorizonLinesAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_check_wrong_params(los_no_target_wrong: QgsVectorLayer) -> None:
    alg = ExportHorizonLinesAlgorithm()
    alg.initAlgorithm()

    # use layer that is not correct horizon lines layer
    params = {"HorizonLinesLayer": los_no_target_wrong}

    with pytest.raises(AssertionError, match="Fields specific for horizon lines not found in current layer"):
        assert_check_parameter_values(alg, params)


@pytest.mark.parametrize(
    "horizon_lines_name",
    [("horizon_line_local"), ("horizon_line_global")],
)
def test_run_alg(horizon_lines_name: str, request) -> None:
    los: QgsVectorLayer = request.getfixturevalue(horizon_lines_name)

    fields = [
        FieldNames.ID_OBSERVER,
        FieldNames.HORIZON_TYPE,
        FieldNames.ANGLE,
        FieldNames.VIEWING_ANGLE,
        FieldNames.CSV_HORIZON_DISTANCE,
    ]

    alg = ExportHorizonLinesAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("export_horizon_lines.gpkg")

    params = {
        "HorizonLinesLayer": los,
        "OutputFile": output_path,
    }

    assert_run(alg, parameters=params)

    export_layer = QgsVectorLayer(output_path)

    assert_layer(export_layer, geom_type=Qgis.WkbType.NoGeometry)

    assert_field_names_exist(fields, export_layer)
