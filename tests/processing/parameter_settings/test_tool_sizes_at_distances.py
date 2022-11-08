from qgis.core import QgsVectorLayer, QgsWkbTypes

from los_tools.processing.parameter_settings.tool_sizes_at_distances import ObjectSizesAlgorithm
from los_tools.constants.field_names import FieldNames

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase
from tests.utils_tests import get_data_path_results


class ObjectSizesAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        super().setUp()

        self.alg = ObjectSizesAlgorithm()

        self.alg.initAlgorithm()

    def test_parameters(self) -> None:

        self.assertQgsProcessingParameter(self.alg.parameterDefinition("Angle"),
                                          parameter_type="number")

        self.assertQgsProcessingParameter(self.alg.parameterDefinition("Distance"),
                                          parameter_type="matrix")

        self.assertQgsProcessingParameter(self.alg.parameterDefinition("OutputTable"),
                                          parameter_type="sink")

        self.assertQgsProcessingParameter(self.alg.parameterDefinition("DefaultSamplingDistance"),
                                          parameter_type="number")

        self.assertQgsProcessingParameter(self.alg.parameterDefinition("MaximalDistance"),
                                          parameter_type="boolean")

    def test_alg_settings(self) -> None:

        self.assertAlgSettings()

    def test_run_alg(self) -> None:

        output_path = get_data_path_results(file="table.gpkg")

        params = {
            'Angle': 0.1,
            'DefaultSamplingDistance': 1,
            'Distance': [1000, 2000, 3000, 4000, 5000],
            'MaximalDistance': True,
            'OutputTable': output_path
        }

        can_run, msg = self.alg.checkParameterValues(params, context=self.context)
        self.assertTrue(can_run)
        self.assertIn("", msg)

        self.alg.run(parameters=params, context=self.context, feedback=self.feedback)

        table = QgsVectorLayer(f"{output_path}|layername=table")

        self.assertQgsVectorLayer(table, geom_type=QgsWkbTypes.NoGeometry, crs=None)

        self.assertFieldNamesInQgsVectorLayer(
            [FieldNames.SIZE_ANGLE, FieldNames.DISTANCE, FieldNames.SIZE], table)

        self.assertEqual(len(table.allFeatureIds()), 7)

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
