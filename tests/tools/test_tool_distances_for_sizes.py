from qgis.core import QgsVectorLayer, QgsWkbTypes

from los_tools.tools.tools_distances_for_sizes import ObjectDistancesAlgorithm
from los_tools.constants.field_names import FieldNames

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase
from tests.utils_tests import get_data_path_results


class ExtractPointsLoSAlgorithmTest(QgsProcessingAlgorithmTestCase):
    def setUp(self) -> None:

        super().setUp()

        self.alg = ObjectDistancesAlgorithm()
        self.alg.initAlgorithm()

    def test_parameters(self) -> None:

        self.assertQgsProcessingParameter(
            self.alg.parameterDefinition("Angle"), parameter_type="number"
        )

        self.assertQgsProcessingParameter(
            self.alg.parameterDefinition("Size"), parameter_type="matrix"
        )

        self.assertQgsProcessingParameter(
            self.alg.parameterDefinition("OutputTable"), parameter_type="sink"
        )

    def test_run_alg(self) -> None:

        output_path = get_data_path_results(file="table.xlsx")

        params = {
            "Angle": 0.1,
            "OutputTable": output_path,
            "Size": ["1", "2", "3", "4", "5"],
        }

        self.assertRunAlgorithm(parameters=params)

        table = QgsVectorLayer(output_path)

        self.assertQgsVectorLayer(table, geom_type=QgsWkbTypes.NoGeometry, crs=None)

        self.assertFieldNamesInQgsVectorLayer(
            [FieldNames.SIZE_ANGLE, FieldNames.DISTANCE, FieldNames.SIZE], table
        )

        self.assertEqual(table.featureCount(), 5)
