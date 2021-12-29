from qgis.core import QgsVectorLayer, QgsWkbTypes

from los_tools.tools.tool_sizes_at_distances import ObjectSizesAlgorithm
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

    def test_run_alg(self) -> None:

        output_path = get_data_path_results(file="table.xlsx")

        params = {
            "Angle": 0.1,
            "OutputTable": output_path,
            "Distance": ["1000", "2000", "3000", "4000", "5000"]
        }

        self.assertRunAlgorithm(parameters=params)

        table = QgsVectorLayer(output_path)

        self.assertQgsVectorLayer(table, geom_type=QgsWkbTypes.NoGeometry, crs=None)

        self.assertFieldNamesInQgsVectorLayer(
            [FieldNames.SIZE_ANGLE, FieldNames.DISTANCE, FieldNames.SIZE], table)

        self.assertEqual(table.featureCount(), 5)
