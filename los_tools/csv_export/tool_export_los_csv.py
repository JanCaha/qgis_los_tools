from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFileDestination,
    QgsMessageLog,
    Qgis)

from los_tools.tools.util_functions import wkt_to_array_points, get_los_type
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.classes.classes_los import LoSLocal, LoSGlobal, LoSWithoutTarget


class ExportLoSCSVAlgorithm(QgsProcessingAlgorithm):

    INPUT_LOS_LAYER = "InputLOSLayer"
    OUTPUT_FILE = "OutputFile"
    CURVATURE_CORRECTIONS = "CurvatureCorrections"
    REFRACTION_COEFFICIENT = "RefractionCoefficient"
    ALTERNATIVE_CSV = "AlternativeCSV"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LOS_LAYER,
                "Input LoS layer",
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
                self.CURVATURE_CORRECTIONS,
                "Use curvature corrections?",
                defaultValue=True)
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.REFRACTION_COEFFICIENT,
                "Refraction coefficient value",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.13
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ALTERNATIVE_CSV,
                "Alternative CSV format (separator ; and decimal separator ,)"
            )
        )

    def checkParameterValues(self, parameters, context):

        input_los_layer = self.parameterAsSource(parameters, self.INPUT_LOS_LAYER, context)

        field_names = input_los_layer.fields().names()

        if FieldNames.LOS_TYPE not in field_names:
            msg = "Fields specific for LoS not found in current layer ({0}). " \
                  "Cannot export the layer as horizon lines.".format(FieldNames.LOS_TYPE)

            QgsMessageLog.logMessage(msg,
                                     "los_tools",
                                     Qgis.MessageLevel.Critical)
            return False, msg

        return True, "OK"

    def processAlgorithm(self, parameters, context, feedback):

        input_los_layer = self.parameterAsSource(parameters, self.INPUT_LOS_LAYER, context)
        output_file = self.parameterAsFileOutput(parameters, self.OUTPUT_FILE, context)
        curvature_corrections = self.parameterAsBool(parameters, self.CURVATURE_CORRECTIONS, context)
        ref_coeff = self.parameterAsDouble(parameters, self.REFRACTION_COEFFICIENT, context)
        alternative_csv = self.parameterAsBool(parameters, self.ALTERNATIVE_CSV, context)

        feature_count = input_los_layer.featureCount()
        total = 100.0 / feature_count if feature_count else 0

        iterator = input_los_layer.getFeatures()

        txt_file = open(output_file, "w")

        los_type = get_los_type(input_los_layer, input_los_layer.fields().names())

        if los_type == NamesConstants.LOS_LOCAL:
            csv_string = "{},{},{},{},{},{},{},{}\n" \
                .format(FieldNames.ID_OBSERVER,
                        FieldNames.ID_TARGET,
                        FieldNames.OBSERVER_OFFSET,
                        FieldNames.TARGET_OFFSET,
                        FieldNames.CSV_OBSERVER_DISTANCE,
                        FieldNames.CSV_ELEVATION,
                        FieldNames.CSV_VISIBLE,
                        FieldNames.CSV_HORIZON)

        elif los_type == NamesConstants.LOS_GLOBAL:
            csv_string = "{},{},{},{},{},{},{},{},{},{},{}\n" \
                .format(FieldNames.ID_OBSERVER,
                        FieldNames.ID_TARGET,
                        FieldNames.OBSERVER_OFFSET,
                        FieldNames.TARGET_OFFSET,
                        FieldNames.TARGET_X,
                        FieldNames.TARGET_Y,
                        FieldNames.CSV_OBSERVER_DISTANCE,
                        FieldNames.CSV_ELEVATION,
                        FieldNames.CSV_TARGET,
                        FieldNames.CSV_VISIBLE,
                        FieldNames.CSV_HORIZON)

        elif los_type == NamesConstants.LOS_NO_TARGET:
            csv_string = "{},{},{},{},{},{}\n" \
                .format(FieldNames.ID_OBSERVER,
                        FieldNames.OBSERVER_OFFSET,
                        FieldNames.CSV_OBSERVER_DISTANCE,
                        FieldNames.CSV_ELEVATION,
                        FieldNames.CSV_VISIBLE,
                        FieldNames.CSV_HORIZON)

        for cnt, los_feature in enumerate(iterator):

            if feedback.isCanceled():
                break

            if los_type == NamesConstants.LOS_LOCAL:
                observer_id = los_feature.attribute(FieldNames.ID_OBSERVER)
                target_id = los_feature.attribute(FieldNames.ID_TARGET)
                observer_offset = los_feature.attribute(FieldNames.OBSERVER_OFFSET)
                target_offset = los_feature.attribute(FieldNames.TARGET_OFFSET)

                los = LoSLocal(wkt_to_array_points(los_feature.geometry().asWkt()),
                               observer_offset=observer_offset,
                               target_offset=target_offset,
                               use_curvature_corrections=curvature_corrections,
                               refraction_coefficient=ref_coeff)

                for i in range(0, len(los.points)):

                    csv_string += "{},{},{},{},{},{},{},{}\n" \
                        .format(observer_id,
                                target_id,
                                observer_offset,
                                target_offset,
                                los.points[i][2],
                                los.points[i][3],
                                int(los.visible[i]),
                                int(los.horizon[i]))

            elif los_type == NamesConstants.LOS_GLOBAL:
                observer_id = los_feature.attribute(FieldNames.ID_OBSERVER)
                target_id = los_feature.attribute(FieldNames.ID_TARGET)
                observer_offset = los_feature.attribute(FieldNames.OBSERVER_OFFSET)
                target_offset = los_feature.attribute(FieldNames.TARGET_OFFSET)
                target_x = los_feature.attribute(FieldNames.TARGET_X)
                target_y = los_feature.attribute(FieldNames.TARGET_Y)

                los = LoSGlobal(wkt_to_array_points(los_feature.geometry().asWkt()),
                                observer_offset=observer_offset,
                                target_offset=target_offset,
                                target_x=target_x,
                                target_y=target_y,
                                use_curvature_corrections=curvature_corrections,
                                refraction_coefficient=ref_coeff)

                for i in range(0, len(los.points)):

                    is_target = 1 if i == los.target_index else 0

                    csv_string += "{},{},{},{},{},{},{},{},{},{},{}\n" \
                        .format(observer_id,
                                target_id,
                                observer_offset,
                                target_offset,
                                target_x,
                                target_y,
                                los.points[i][2],
                                los.points[i][3],
                                is_target,
                                int(los.visible[i]),
                                int(los.horizon[i]))

            elif los_type == NamesConstants.LOS_NO_TARGET:
                observer_id = los_feature.attribute(FieldNames.ID_OBSERVER)
                observer_offset = los_feature.attribute(FieldNames.OBSERVER_OFFSET)

                los = LoSWithoutTarget(wkt_to_array_points(los_feature.geometry().asWkt()),
                                       observer_offset=los_feature.attribute(FieldNames.OBSERVER_OFFSET),
                                       use_curvature_corrections=curvature_corrections,
                                       refraction_coefficient=ref_coeff)

                for i in range(0, len(los.points)):

                    csv_string += "{},{},{},{},{},{}\n" \
                        .format(observer_id,
                                observer_offset,
                                los.points[i][2],
                                los.points[i][3],
                                int(los.visible[i]),
                                int(los.horizon[i]))

            feedback.setProgress(int(cnt * total))

        if alternative_csv:
            csv_string = csv_string.replace(",", ";").replace(".", ",")

        txt_file.write(csv_string)
        txt_file.close()

        return {self.OUTPUT_FILE: txt_file}

    def name(self):
        return "exportloscsv"

    def displayName(self):
        return "Export Los Layer to CSV"

    def group(self):
        return "Export CSV"

    def groupId(self):
        return "exportcsv"

    def createInstance(self):
        return ExportLoSCSVAlgorithm()
