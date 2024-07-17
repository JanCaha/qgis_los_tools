import math

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterMatrix,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingFeedback,
    QgsFields,
    QgsField,
    QgsWkbTypes,
    QgsProcessingParameterFeatureSink,
    QgsFeature,
    QgsProcessingException,
    QgsProcessingUtils,
)

from qgis.PyQt.QtCore import QVariant

from los_tools.constants.field_names import FieldNames
from los_tools.utils import get_doc_file


class ObjectDistancesAlgorithm(QgsProcessingAlgorithm):
    ANGLE = "Angle"
    SIZES = "Size"
    MAXIMALDISTANCE = "MaximalDistance"
    OUTPUT_TABLE = "OutputTable"

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ANGLE,
                "Angle size of object (in degrees)",
                QgsProcessingParameterNumber.Double,
                defaultValue=0.1,
                minValue=0.0,
                maxValue=100.0,
                optional=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterMatrix(
                self.SIZES,
                "Sizes of object to calculate (in meters)",
                numberRows=1,
                headers=["Size"],
                defaultValue=[1],
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.MAXIMALDISTANCE,
                "Add maximal distance value (with sampling equal to maximal sampling distance)",
                defaultValue=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT_TABLE, "Output table")
        )

    def processAlgorithm(self, parameters, context, feedback: QgsProcessingFeedback):
        angle = self.parameterAsDouble(parameters, self.ANGLE, context)
        sizes = self.parameterAsMatrix(parameters, self.SIZES, context)
        maximal_distance = self.parameterAsBoolean(
            parameters, self.MAXIMALDISTANCE, context
        )

        fields = QgsFields()
        fields.append(QgsField(FieldNames.SIZE_ANGLE, QVariant.Double))
        fields.append(QgsField(FieldNames.DISTANCE, QVariant.Double))
        fields.append(QgsField(FieldNames.SIZE, QVariant.Double))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT_TABLE, context, fields, QgsWkbTypes.NoGeometry
        )

        if sink is None:
            raise QgsProcessingException(
                self.invalidSinkError(parameters, self.OUTPUT_TABLE)
            )

        result_string_print = "Sizes at distances:\n" "Size - Distance\n"

        angle = float(angle)

        maximal_sampling_distance = 0

        for size in sizes:
            size = float(size)

            distance = round(size / math.tan(math.radians(angle)), 3)

            result_string_print += f"{size} - {distance}\n"

            if maximal_sampling_distance < size:
                maximal_sampling_distance = size

            f = QgsFeature(fields)
            f.setAttribute(f.fieldNameIndex(FieldNames.SIZE_ANGLE), float(angle))
            f.setAttribute(f.fieldNameIndex(FieldNames.DISTANCE), float(distance))
            f.setAttribute(f.fieldNameIndex(FieldNames.SIZE), float(size))

            sink.addFeature(f)

        if maximal_distance:
            f = QgsFeature(fields)
            f.setAttribute(f.fieldNameIndex(FieldNames.SIZE_ANGLE), float(angle))
            f.setAttribute(f.fieldNameIndex(FieldNames.DISTANCE), -1)
            f.setAttribute(f.fieldNameIndex(FieldNames.SIZE), maximal_sampling_distance)

            result_string_print += f"{-1} - {maximal_sampling_distance}\n"

            sink.addFeature(f)

        feedback.pushInfo(result_string_print)

        return {self.OUTPUT_TABLE: dest_id}

    def name(self):
        return "calculatedistances"

    def displayName(self):
        return "Calculate Object Distances"

    def group(self):
        return "Calculate Parameters Settings"

    def groupId(self):
        return "parametersettings"

    def createInstance(self):
        return ObjectDistancesAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools//Calculate%20Parameters%20Settings/tool_distances_for_sizes/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
