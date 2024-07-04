from qgis.core import QgsFeature, QgsLineString, QgsPoint, QgsVectorLayer

from los_tools.classes.sampling_distance_matrix import SamplingDistanceMatrix
from los_tools.constants.field_names import FieldNames
from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase


def test_creation(table_angle_distance_size: QgsVectorLayer):
    distance_sampling_matrix = SamplingDistanceMatrix(table_angle_distance_size)

    assert isinstance(distance_sampling_matrix, SamplingDistanceMatrix)

    assert isinstance(distance_sampling_matrix.data, list)
    assert len(distance_sampling_matrix.data) == 5


def test_repr(table_angle_distance_size: QgsVectorLayer):
    distance_sampling_matrix = SamplingDistanceMatrix(table_angle_distance_size)

    isinstance(repr(distance_sampling_matrix), str)


def test_get_rows(table_angle_distance_size: QgsVectorLayer):

    distance_sampling_matrix = SamplingDistanceMatrix(table_angle_distance_size)

    assert isinstance(distance_sampling_matrix.get_row(0), list)

    assert isinstance(distance_sampling_matrix.get_row_distance(0), (int, float))
    assert isinstance(distance_sampling_matrix.get_row_sampling_distance(0), (int, float))


def test_validate_table(table_angle_distance_size: QgsVectorLayer):

    result, msg = SamplingDistanceMatrix.validate_table(table_angle_distance_size)

    assert isinstance(result, bool)
    assert result

    assert isinstance(msg, str)
    assert msg == ""


def test_distances(table_angle_distance_size: QgsVectorLayer):

    distance_sampling_matrix = SamplingDistanceMatrix(table_angle_distance_size)

    assert distance_sampling_matrix.minimum_distance == 0
    assert distance_sampling_matrix.maximum_distance == 2000


def test_next_distance(table_angle_distance_size: QgsVectorLayer):

    distance_sampling_matrix = SamplingDistanceMatrix(table_angle_distance_size)

    assert distance_sampling_matrix.next_distance(0) == 0.5
    assert distance_sampling_matrix.next_distance(250) == 250.5
    assert distance_sampling_matrix.next_distance(495) == 495.5
    assert distance_sampling_matrix.next_distance(501) == 501.873
    assert distance_sampling_matrix.next_distance(900) == 900.873
    assert distance_sampling_matrix.next_distance(1001) == 1002.745
    assert distance_sampling_matrix.next_distance(1490) == 1491.745
    assert distance_sampling_matrix.next_distance(1501) == 1503.618
    assert distance_sampling_matrix.next_distance(1990) == 1992.618
    assert distance_sampling_matrix.next_distance(2001) == 2004.491


def test_build_line(table_angle_distance_size: QgsVectorLayer):

    distance_sampling_matrix = SamplingDistanceMatrix(table_angle_distance_size)

    start_point = QgsPoint(0, 0)
    end_point = QgsPoint(10, 0)

    line = distance_sampling_matrix.build_line(start_point, end_point)

    assert isinstance(line, QgsLineString)

    assert isinstance(line.asWkt(), str)

    assert (
        "LineString (0 0, 0.5 0.00000000000000003, 1 0.00000000000000006, 1.5 0.00000000000000009, 2 0.00000000000000012"
        in line.asWkt()
    )

    assert (
        "1994.7643979057593242 0.00000000000012214, 1997.3821989528796621 0.0000000000001223, 2000 0.00000000000012246)"
        in line.asWkt()
    )


def test_values_minus_one(table_angle_distance_size: QgsVectorLayer):

    fields = table_angle_distance_size.fields()

    field_index_angle = fields.indexFromName(FieldNames.SIZE_ANGLE)
    field_index_distance = fields.indexFromName(FieldNames.DISTANCE)
    field_index_size = fields.indexFromName(FieldNames.SIZE)

    f = QgsFeature(fields)
    f.setAttribute(field_index_angle, 0.1)
    f.setAttribute(field_index_distance, -1)
    f.setAttribute(field_index_size, 3.491)

    table_dp = table_angle_distance_size.dataProvider()

    table_dp.addFeature(f)

    distance_sampling_matrix = SamplingDistanceMatrix(table_angle_distance_size)

    assert distance_sampling_matrix.minimum_distance == -1

    distance_sampling_matrix.replace_minus_one_with_value(10000)

    assert distance_sampling_matrix.maximum_distance == 10000
