from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFileDestination,
    QgsMessageLog,
    QgsPointXY,
    Qgis)

from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.tools.util_functions import get_horizon_lines_type


class ExportHorizonLinesCSVAlgorithm(QgsProcessingAlgorithm):

    INPUT_HORIZON_LINES_LAYER = "InputHorizonLinesLayer"
    OUTPUT_FILE = "OutputFile"
    ALTERNATIVE_CSV = "AlternativeCSV"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_HORIZON_LINES_LAYER,
                "Input Horizon Lines layer",
                [QgsProcessing.TypeVectorLine])
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_FILE,
                "Output file",
                fileFilter="CSV File (*.csv)"
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ALTERNATIVE_CSV,
                "Alternative CSV format (separator ; and decimal separator ,)"
            )
        )

    def checkParameterValues(self, parameters, context):

        input_horizon_lines_layer = self.parameterAsSource(parameters, self.INPUT_HORIZON_LINES_LAYER, context)

        field_names = input_horizon_lines_layer.fields().names()

        if not FieldNames.HORIZON_TYPE in field_names:
            msg = "Fields specific for horizon lines not found in current layer ({0}). " \
                  "Cannot export the layer as horizon lines.".format(FieldNames.HORIZON_TYPE)

            QgsMessageLog.logMessage(msg,
                                     "los_tools",
                                     Qgis.MessageLevel.Critical)
            return False, msg

        return True, "OK"

    def processAlgorithm(self, parameters, context, feedback):

        input_horizon_lines_layer = self.parameterAsSource(parameters, self.INPUT_HORIZON_LINES_LAYER, context)
        output_file = self.parameterAsFileOutput(parameters, self.OUTPUT_FILE, context)
        alternative_csv = self.parameterAsBool(parameters, self.ALTERNATIVE_CSV, context)

        horizon_lines_type = get_horizon_lines_type(input_horizon_lines_layer)

        feature_count = input_horizon_lines_layer.featureCount()
        total = 100.0 / feature_count if feature_count else 0

        iterator = input_horizon_lines_layer.getFeatures()

        if horizon_lines_type == NamesConstants.HORIZON_MAX_LOCAL:
            csv_string = "{},{},{},{},{}\n".format(FieldNames.ID_OBSERVER,
                                                   FieldNames.HORIZON_TYPE,
                                                   FieldNames.ANGLE,
                                                   FieldNames.VIEWING_ANGLE,
                                                   FieldNames.CSV_HORIZON_DISTANCE)
        elif horizon_lines_type == NamesConstants.HORIZON_GLOBAL:
            csv_string = "{},{},{},{},{},{},{}\n".format(FieldNames.ID_OBSERVER,
                                                         FieldNames.HORIZON_TYPE,
                                                         FieldNames.ANGLE,
                                                         FieldNames.VIEWING_ANGLE,
                                                         FieldNames.CSV_HORIZON_DISTANCE,
                                                         FieldNames.CSV_HORIZON_ANGLE_DIFF,
                                                         FieldNames.CSV_HORIZON_ELEVATION_DIFF)

        for cnt, horizon_line_feature in enumerate(iterator):

            if feedback.isCanceled():
                break

            observer_point = QgsPointXY(horizon_line_feature.attribute(FieldNames.OBSERVER_X),
                                        horizon_line_feature.attribute(FieldNames.OBSERVER_Y))

            observer_id = horizon_line_feature.attribute(FieldNames.ID_OBSERVER)
            horizon_type = horizon_line_feature.attribute(FieldNames.HORIZON_TYPE)

            if horizon_lines_type == NamesConstants.HORIZON_GLOBAL:
                angles_diff = horizon_line_feature.attribute(FieldNames.POINTS_ANGLE_DIFF_GH_LH).split(";")
                elevs_diff = horizon_line_feature.attribute(FieldNames.POINTS_ELEVATION_DIFF_GH_LH).split(";")

            line_geometry = horizon_line_feature.geometry()

            i = 0
            for v in line_geometry.vertices():
                horizon_point = QgsPointXY(v.x(), v.y())

                if horizon_lines_type == NamesConstants.HORIZON_MAX_LOCAL:
                    csv_string += "{},{},{},{},{}\n".format(observer_id,
                                                            horizon_type,
                                                            observer_point.azimuth(horizon_point),
                                                            v.m(),
                                                            observer_point.distance(v.x(), v.y()))
                elif horizon_lines_type == NamesConstants.HORIZON_GLOBAL:
                    csv_string += "{},{},{},{},{}\n".format(observer_id,
                                                            horizon_type,
                                                            observer_point.azimuth(horizon_point),
                                                            v.m(),
                                                            observer_point.distance(v.x(), v.y()),
                                                            angles_diff[i],
                                                            elevs_diff[i])
                i += 1

            feedback.setProgress(int(cnt * total))

        if alternative_csv:
            csv_string = csv_string.replace(",", ";").replace(".", ",")

        txt_file = open(output_file, "w")
        txt_file.write(csv_string)
        txt_file.close()

        return {self.OUTPUT_FILE: txt_file}

    def name(self):
        return "exporthorizonlinescsv"

    def displayName(self):
        return "Export Horizon Lines Layer to CSV"

    def group(self):
        return "Export CSV"

    def groupId(self):
        return "exportcsv"

    def createInstance(self):
        return ExportHorizonLinesCSVAlgorithm()