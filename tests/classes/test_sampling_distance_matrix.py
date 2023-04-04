from qgis.core import (QgsVectorLayer, QgsFeature, QgsPoint, QgsLineString)

from los_tools.classes.sampling_distance_matrix import SamplingDistanceMatrix
from los_tools.constants.field_names import FieldNames

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase


class SamplingDistanceMatrixTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        super().setUp()

        self.table = QgsVectorLayer(
            F"NoGeometry?"
            F"field={FieldNames.SIZE_ANGLE}:double&"
            F"field={FieldNames.DISTANCE}:double&"
            F"field={FieldNames.SIZE}:double", "source", "memory")

        self.table_dp = self.table.dataProvider()

        fields = self.table.fields()

        field_index_angle = fields.indexFromName(FieldNames.SIZE_ANGLE)
        field_index_distance = fields.indexFromName(FieldNames.DISTANCE)
        field_index_size = fields.indexFromName(FieldNames.SIZE)

        angle_size = 0.1

        f = QgsFeature(fields)
        f.setAttribute(field_index_angle, angle_size)
        f.setAttribute(field_index_distance, 0)
        f.setAttribute(field_index_size, 0.5)

        self.table_dp.addFeature(f)

        f = QgsFeature(fields)
        f.setAttribute(field_index_angle, angle_size)
        f.setAttribute(field_index_distance, 500)
        f.setAttribute(field_index_size, 0.873)

        self.table_dp.addFeature(f)

        f = QgsFeature(fields)
        f.setAttribute(field_index_angle, angle_size)
        f.setAttribute(field_index_distance, 1000)
        f.setAttribute(field_index_size, 1.745)

        self.table_dp.addFeature(f)

        f = QgsFeature(fields)
        f.setAttribute(field_index_angle, angle_size)
        f.setAttribute(field_index_distance, 1500)
        f.setAttribute(field_index_size, 2.618)

        self.table_dp.addFeature(f)

        f = QgsFeature(fields)
        f.setAttribute(field_index_angle, angle_size)
        f.setAttribute(field_index_distance, 2000)
        f.setAttribute(field_index_size, 3.491)

        self.table_dp.addFeature(f)

        # f = QgsFeature(fields)
        # f.setAttribute(field_index_angle, angle_size)
        # f.setAttribute(field_index_distance, -1)
        # f.setAttribute(field_index_size, 3.491)

        # self.table_dp.addFeature(f)

    def test_create_object(self):

        distance_sampling_matrix = SamplingDistanceMatrix(self.table)

        self.assertIsInstance(distance_sampling_matrix, SamplingDistanceMatrix)

        self.assertIsInstance(distance_sampling_matrix.data, list)
        self.assertEqual(len(distance_sampling_matrix.data), 5)

    def test_len(self):

        distance_sampling_matrix = SamplingDistanceMatrix(self.table)

        self.assertIsInstance(len(distance_sampling_matrix), int)
        self.assertEqual(len(distance_sampling_matrix), 5)

    def test_repr(self):

        distance_sampling_matrix = SamplingDistanceMatrix(self.table)

        self.assertIsInstance(repr(distance_sampling_matrix), str)

    def test_get_rows(self):

        distance_sampling_matrix = SamplingDistanceMatrix(self.table)

        self.assertIsInstance(distance_sampling_matrix.get_row(0), list)

        self.assertIsInstance(distance_sampling_matrix.get_row_distance(0), (int, float))
        self.assertIsInstance(distance_sampling_matrix.get_row_sampling_distance(0), (int, float))

    def test_validate_table(self):

        result, msg = SamplingDistanceMatrix.validate_table(self.table)

        self.assertIsInstance(result, bool)
        self.assertTrue(result)

        self.assertIsInstance(msg, str)
        self.assertEqual(msg, "")

    def test_distances(self):

        distance_sampling_matrix = SamplingDistanceMatrix(self.table)

        self.assertEqual(distance_sampling_matrix.minimum_distance, 0)
        self.assertEqual(distance_sampling_matrix.maximum_distance, 2000)

    def test_next_distance(self):

        distance_sampling_matrix = SamplingDistanceMatrix(self.table)

        self.assertEqual(distance_sampling_matrix.next_distance(0), 0.5)
        self.assertEqual(distance_sampling_matrix.next_distance(250), 250.5)
        self.assertEqual(distance_sampling_matrix.next_distance(495), 495.5)
        self.assertEqual(distance_sampling_matrix.next_distance(501), 501.873)

        self.assertEqual(distance_sampling_matrix.next_distance(900), 900.873)
        self.assertEqual(distance_sampling_matrix.next_distance(1001), 1002.745)

        self.assertEqual(distance_sampling_matrix.next_distance(1490), 1491.745)
        self.assertEqual(distance_sampling_matrix.next_distance(1501), 1503.618)

        self.assertEqual(distance_sampling_matrix.next_distance(1990), 1992.618)
        self.assertEqual(distance_sampling_matrix.next_distance(2001), 2004.491)

    def test_build_line(self):

        distance_sampling_matrix = SamplingDistanceMatrix(self.table)

        start_point = QgsPoint(0, 0)
        end_point = QgsPoint(10, 0)

        line = distance_sampling_matrix.build_line(start_point, end_point)

        self.assertIsInstance(line, QgsLineString)

        self.assertIsInstance(line.asWkt(), str)

        self.assertTrue(
            "LineString (0 0, 0.5 0.00000000000000003, 1 0.00000000000000006, 1.5 0.00000000000000009, 2 0.00000000000000012"
            in line.asWkt())

        self.assertTrue(
            "1994.7643979057593242 0.00000000000012214, 1997.3821989528796621 0.0000000000001223, 2000 0.00000000000012246)"
            in line.asWkt())

    def test_values_minus_one(self):

        fields = self.table.fields()

        field_index_angle = fields.indexFromName(FieldNames.SIZE_ANGLE)
        field_index_distance = fields.indexFromName(FieldNames.DISTANCE)
        field_index_size = fields.indexFromName(FieldNames.SIZE)

        f = QgsFeature(fields)
        f.setAttribute(field_index_angle, 0.1)
        f.setAttribute(field_index_distance, -1)
        f.setAttribute(field_index_size, 3.491)

        self.table_dp.addFeature(f)

        distance_sampling_matrix = SamplingDistanceMatrix(self.table)

        self.assertEqual(distance_sampling_matrix.minimum_distance, -1)

        distance_sampling_matrix.replace_minus_one_with_value(10000)

        self.assertEqual(distance_sampling_matrix.maximum_distance, 10000)
