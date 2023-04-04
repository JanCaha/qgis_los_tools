from qgis.core import (QgsVectorLayer, QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)

from qgis._core import QgsWkbTypes

from los_tools.constants.field_names import FieldNames

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase

from los_tools.processing.to_table.tool_export_horizon_lines import ExportHorizonLinesAlgorithm

from tests.utils_tests import (get_data_path, get_data_path_results)


class ExportHorizonLinesAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        super().setUp()

        self.horizon_lines_global = QgsVectorLayer(get_data_path(file="horizon_line_global.gpkg"))
        self.horizon_lines_local = QgsVectorLayer(get_data_path(file="horizon_line_local.gpkg"))

        self.alg = ExportHorizonLinesAlgorithm()
        self.alg.initAlgorithm()

    def test_parameters(self) -> None:
        self.assertIsInstance(self.alg.parameterDefinition("HorizonLinesLayer"),
                              QgsProcessingParameterFeatureSource)
        self.assertIsInstance(self.alg.parameterDefinition("OutputFile"),
                              QgsProcessingParameterFeatureSink)

    def test_alg_settings(self) -> None:

        self.assertAlgSettings()

    def test_check_wrong_params(self) -> None:

        # use layer that is not correct horizon lines layer
        params = {
            "HorizonLinesLayer": QgsVectorLayer(get_data_path(file="no_target_los_wrong.gpkg"))
        }

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="Fields specific for horizon lines not found in current layer")

    def test_run_alg(self) -> None:

        fields = [
            FieldNames.ID_OBSERVER, FieldNames.HORIZON_TYPE, FieldNames.ANGLE,
            FieldNames.VIEWING_ANGLE, FieldNames.CSV_HORIZON_DISTANCE
        ]

        output_path = get_data_path_results(file="export_horizon_lines.gpkg")

        params = {
            "HorizonLinesLayer": self.horizon_lines_local,
            "OutputFile": output_path,
        }

        self.assertRunAlgorithm(parameters=params)

        export_layer = QgsVectorLayer(output_path)

        self.assertEqual(export_layer.wkbType(), QgsWkbTypes.NoGeometry)

        fields_layer = export_layer.fields().names()
        del fields_layer[0]

        self.assertListEqual(fields, fields_layer)

        export_layer = None

        params = {
            "HorizonLinesLayer": self.horizon_lines_global,
            "OutputFile": output_path,
        }

        self.assertRunAlgorithm(parameters=params)

        export_layer = QgsVectorLayer(output_path)

        self.assertEqual(export_layer.wkbType(), QgsWkbTypes.NoGeometry)

        fields_layer = export_layer.fields().names()
        del fields_layer[0]

        self.assertListEqual(fields, fields_layer)
