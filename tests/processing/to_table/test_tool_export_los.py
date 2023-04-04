from qgis.core import (QgsVectorLayer, QgsProcessingParameterBoolean, QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSource, QgsProcessingParameterFeatureSink)

from qgis._core import QgsWkbTypes

from los_tools.constants.field_names import FieldNames

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase

from los_tools.processing.to_table.tool_export_los import ExportLoSAlgorithm

from tests.utils_tests import (get_data_path, get_data_path_results)


class ExportLoSAlgorithmTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        super().setUp()

        self.los_global = QgsVectorLayer(get_data_path(file="los_global.gpkg"))

        self.los_local = QgsVectorLayer(get_data_path(file="los_local.gpkg"))

        self.los_no_target = QgsVectorLayer(get_data_path(file="no_target_los.gpkg"))

        self.alg = ExportLoSAlgorithm()
        self.alg.initAlgorithm()

    def test_parameters(self) -> None:
        self.assertIsInstance(self.alg.parameterDefinition("LoSLayer"),
                              QgsProcessingParameterFeatureSource)
        self.assertIsInstance(self.alg.parameterDefinition("CurvatureCorrections"),
                              QgsProcessingParameterBoolean)
        self.assertIsInstance(self.alg.parameterDefinition("RefractionCoefficient"),
                              QgsProcessingParameterNumber)
        self.assertIsInstance(self.alg.parameterDefinition("OutputFile"),
                              QgsProcessingParameterFeatureSink)

        self.assertTrue(self.alg.parameterDefinition("CurvatureCorrections").defaultValue())
        self.assertEqual(
            self.alg.parameterDefinition("RefractionCoefficient").defaultValue(), 0.13)

    def test_alg_settings(self) -> None:

        self.assertAlgSettings()

    def test_check_wrong_params(self) -> None:

        # use layer that is not corrently constructed LoS layer
        params = {"LoSLayer": QgsVectorLayer(get_data_path(file="no_target_los_wrong.gpkg"))}

        self.assertCheckParameterValuesRaisesMessage(
            parameters=params,
            message="Fields specific for LoS not found in current layer (los_type).")

    def test_run_alg(self) -> None:

        fields = [
            FieldNames.ID_LOS, FieldNames.ID_OBSERVER, FieldNames.OBSERVER_OFFSET,
            FieldNames.CSV_OBSERVER_DISTANCE, FieldNames.CSV_ELEVATION, FieldNames.CSV_VISIBLE,
            FieldNames.CSV_HORIZON
        ]

        output_path = get_data_path_results(file="export_los.gpkg")

        params = {
            "LoSLayer": self.los_no_target,
            "OutputFile": output_path,
            "CurvatureCorrections": True,
            "RefractionCoefficient": 0.13
        }

        self.assertRunAlgorithm(parameters=params)

        export_layer = QgsVectorLayer(output_path)

        self.assertEqual(export_layer.wkbType(), QgsWkbTypes.NoGeometry)

        fields_layer = export_layer.fields().names()
        del fields_layer[0]

        self.assertListEqual(fields, fields_layer)

        export_layer = None

        params = {
            "LoSLayer": self.los_local,
            "OutputFile": output_path,
            "CurvatureCorrections": True,
            "RefractionCoefficient": 0.13
        }

        self.assertRunAlgorithm(parameters=params)

        export_layer = QgsVectorLayer(output_path)

        self.assertEqual(export_layer.wkbType(), QgsWkbTypes.NoGeometry)

        fields_layer = export_layer.fields().names()
        del fields_layer[0]

        self.assertListEqual(fields + [FieldNames.ID_TARGET, FieldNames.TARGET_OFFSET],
                             fields_layer)

        export_layer = None

        params = {
            "LoSLayer": self.los_global,
            "OutputFile": output_path,
            "CurvatureCorrections": True,
            "RefractionCoefficient": 0.13
        }

        self.assertRunAlgorithm(parameters=params)

        export_layer = QgsVectorLayer(output_path)

        self.assertEqual(export_layer.wkbType(), QgsWkbTypes.NoGeometry)

        fields_layer = export_layer.fields().names()
        del fields_layer[0]

        self.assertListEqual(
            fields + [
                FieldNames.ID_TARGET, FieldNames.TARGET_OFFSET, FieldNames.TARGET_X,
                FieldNames.TARGET_Y, FieldNames.CSV_TARGET
            ], fields_layer)
