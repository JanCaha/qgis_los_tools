import math

import numpy as np
import pytest
from qgis.core import QgsFeatureRequest, QgsProcessingContext, QgsProcessingFeedback, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.processing.create_points.tool_points_in_direction import CreatePointsInDirectionAlgorithm
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
    alg = CreatePointsInDirectionAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("InputLayer"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("IdField"), parameter_type="field", parent_parameter="InputLayer")
    assert_parameter(alg.parameterDefinition("DirectionLayer"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("AngleOffset"), parameter_type="number", default_value=20)
    assert_parameter(alg.parameterDefinition("AngleStep"), parameter_type="number", default_value=1)
    assert_parameter(alg.parameterDefinition("Distance"), parameter_type="distance", default_value=10)
    assert_parameter(alg.parameterDefinition("OutputLayer"), parameter_type="sink")


def test_alg_settings() -> None:
    alg = CreatePointsInDirectionAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_wrong_params(layer_points: QgsVectorLayer) -> None:
    alg = CreatePointsInDirectionAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("points_direction.gpkg")

    params = {
        "InputLayer": layer_points,
        "IdField": "id_point",
        "DirectionLayer": layer_points,
        "AngleOffset": 10,
        "AngleStep": 0.5,
        "Distance": 10,
        "OutputLayer": output_path,
    }

    with pytest.raises(AssertionError, match="`Main direction point layer` should only containt one feature."):
        assert_check_parameter_values(alg, parameters=params)


def test_run(layer_points: QgsVectorLayer, layer_point: QgsVectorLayer) -> None:
    alg = CreatePointsInDirectionAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("points_direction.gpkg")

    angle_offset = 20
    angle_step = 1
    distance = 10

    params = {
        "InputLayer": layer_points,
        "IdField": "id_point",
        "DirectionLayer": layer_point,
        "AngleOffset": angle_offset,
        "AngleStep": angle_step,
        "Distance": distance,
        "OutputLayer": output_path,
    }

    assert_run(alg, parameters=params)

    output_layer = QgsVectorLayer(output_path)

    assert_field_names_exist(
        [FieldNames.ID_ORIGINAL_POINT, FieldNames.ID_POINT, FieldNames.AZIMUTH, FieldNames.ANGLE_STEP_POINTS],
        output_layer,
    )

    unique_ids_orig = list(layer_points.uniqueValues(layer_points.fields().lookupField("id_point")))
    unique_ids_new = list(output_layer.uniqueValues(output_layer.fields().lookupField(FieldNames.ID_ORIGINAL_POINT)))

    assert unique_ids_orig == unique_ids_new

    angles = np.arange(0 - angle_offset, 0 + angle_offset + 0.1 * angle_step, step=angle_step).tolist()

    number_of_elements = len(angles) * len(unique_ids_orig)

    assert number_of_elements == output_layer.featureCount()

    for id_orig in unique_ids_orig:
        request = QgsFeatureRequest()
        request.setFilterExpression(f"{FieldNames.ID_ORIGINAL_POINT} = '{id_orig}'")
        order_by_clause = QgsFeatureRequest.OrderByClause(FieldNames.AZIMUTH, ascending=True)
        request.setOrderBy(QgsFeatureRequest.OrderBy([order_by_clause]))

        features = list(output_layer.getFeatures(request))

        for i in range(0, len(features) - 1):
            assert features[i].geometry().distance(features[i + 1].geometry()) == pytest.approx(
                math.radians(angle_step) * distance, abs=0.00001
            )
