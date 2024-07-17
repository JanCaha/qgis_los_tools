from qgis.core import Qgis, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.processing.create_points.tool_points_around import CreatePointsAroundAlgorithm
from tests.custom_assertions import (
    assert_algorithm,
    assert_field_names_exist,
    assert_layer,
    assert_parameter,
    assert_run,
)
from tests.utils import result_filename


def test_parameters() -> None:
    alg = CreatePointsAroundAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("InputLayer"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("IdField"), parameter_type="field", parent_parameter="InputLayer")
    assert_parameter(alg.parameterDefinition("AngleStart"), parameter_type="number", default_value=0)
    assert_parameter(alg.parameterDefinition("AngleEnd"), parameter_type="number", default_value=359.999)
    assert_parameter(alg.parameterDefinition("AngleStep"), parameter_type="number", default_value=1)
    assert_parameter(alg.parameterDefinition("Distance"), parameter_type="distance", default_value=10)
    assert_parameter(alg.parameterDefinition("OutputLayer"), parameter_type="sink")


def test_alg_settings() -> None:
    alg = CreatePointsAroundAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_run(layer_points: QgsVectorLayer) -> None:
    alg = CreatePointsAroundAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("points_around.gpkg")

    params = {
        "InputLayer": layer_points,
        "IdField": "id_point",
        "AngleStart": 0,
        "AngleEnd": 359,
        "AngleStep": 1,
        "Distance": 5,
        "OutputLayer": output_path,
    }

    assert_run(alg, parameters=params)

    output_layer = QgsVectorLayer(output_path)

    assert_layer(output_layer, Qgis.WkbType.Point, crs=layer_points.crs())
    assert output_layer.featureCount() == 2160

    assert_field_names_exist(
        [FieldNames.ID_ORIGINAL_POINT, FieldNames.AZIMUTH, FieldNames.ANGLE_STEP_POINTS], output_layer
    )
