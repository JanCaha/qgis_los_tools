from qgis.core import Qgis, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.processing.parameter_settings.tool_distances_for_sizes import ObjectDistancesAlgorithm
from tests.custom_assertions import (
    assert_algorithm,
    assert_field_names_exist,
    assert_layer,
    assert_parameter,
    assert_run,
)
from tests.utils import result_filename


def test_parameters() -> None:
    alg = ObjectDistancesAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("Angle"), parameter_type="number")

    assert_parameter(alg.parameterDefinition("Size"), parameter_type="matrix")

    assert_parameter(alg.parameterDefinition("OutputTable"), parameter_type="sink")


def test_alg_settings() -> None:
    alg = ObjectDistancesAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_run_alg() -> None:
    alg = ObjectDistancesAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("table.xlsx")

    params = {
        "Angle": 0.1,
        "OutputTable": output_path,
        "Size": ["1", "2", "3", "4", "5"],
    }

    assert_run(alg, params)

    table = QgsVectorLayer(f"{output_path}|layername=table")

    assert_layer(table, geom_type=Qgis.WkbType.NoGeometry, crs=None)

    assert_field_names_exist([FieldNames.SIZE_ANGLE, FieldNames.DISTANCE, FieldNames.SIZE], table)

    assert len(table.allFeatureIds()) == 5
