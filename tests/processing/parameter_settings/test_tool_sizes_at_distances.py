from qgis.core import Qgis, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.processing.parameter_settings.tool_sizes_at_distances import ObjectSizesAlgorithm
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
    alg = ObjectSizesAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("Angle"), parameter_type="number")

    assert_parameter(alg.parameterDefinition("Distance"), parameter_type="matrix")

    assert_parameter(alg.parameterDefinition("OutputTable"), parameter_type="sink")

    assert_parameter(alg.parameterDefinition("DefaultSamplingDistance"), parameter_type="number")

    assert_parameter(alg.parameterDefinition("MaximalDistance"), parameter_type="boolean")


def test_alg_settings() -> None:
    alg = ObjectSizesAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_run_alg() -> None:
    alg = ObjectSizesAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("table.gpkg")

    params = {
        "Angle": 0.1,
        "DefaultSamplingDistance": 1,
        "Distance": [1000, 2000, 3000, 4000, 5000],
        "MaximalDistance": True,
        "OutputTable": output_path,
    }

    assert_run(alg, params)

    table = QgsVectorLayer(f"{output_path}|layername=table")

    assert_layer(table, geom_type=Qgis.WkbType.NoGeometry, crs=None)

    assert_field_names_exist([FieldNames.SIZE_ANGLE, FieldNames.DISTANCE, FieldNames.SIZE], table)

    assert len(table.allFeatureIds()) == 7

    angles = []
    distances = []
    sampling_sizes = []

    for feature in table.getFeatures():
        angles.append(feature.attribute(FieldNames.SIZE_ANGLE))
        distances.append(feature.attribute(FieldNames.DISTANCE))
        sampling_sizes.append(feature.attribute(FieldNames.SIZE))

    assert angles == [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    assert distances == [0, 1000, 2000, 3000, 4000, 5000, -1]
    assert sampling_sizes == [1.0, 1.745, 3.491, 5.236, 6.981, 8.727, 8.727]
