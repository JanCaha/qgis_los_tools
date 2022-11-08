import math

from qgis.core import (QgsProcessingAlgorithm, QgsProcessingParameterMatrix,
                       QgsProcessingParameterBoolean, QgsProcessingParameterNumber,
                       QgsProcessingFeedback, QgsFields, QgsField, QgsWkbTypes,
                       QgsProcessingParameterFeatureSink, QgsFeature, QgsProcessingException,
                       QgsProcessingUtils)

from qgis.PyQt.QtCore import QVariant

from los_tools.constants.field_names import FieldNames
from ..tools.util_functions import get_doc_file


class ObjectSizesAlgorithm(QgsProcessingAlgorithm):

    ANGLE = "Angle"
    DISTANCES = "Distance"
    MAXIMALDISTANCE = "MaximalDistance"
    DEFAULT_SAMPLING_DISTANCE = "DefaultSamplingDistance"
    OUTPUT_TABLE = "OutputTable"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterNumber(self.ANGLE,
                                         "Angle size of object (in degrees)",
                                         QgsProcessingParameterNumber.Double,
                                         defaultValue=0.1,
                                         minValue=0.0,
                                         maxValue=100.0,
                                         optional=False))

        self.addParameter(
            QgsProcessingParameterMatrix(self.DISTANCES,
                                         "Distances to calculate object size (in meters)",
                                         numberRows=1,
                                         headers=["Distance"],
                                         defaultValue=[1000]))

        param = QgsProcessingParameterNumber(self.DEFAULT_SAMPLING_DISTANCE,
                                             "Default sampling size (in meters)",
                                             defaultValue=1,
                                             type=QgsProcessingParameterNumber.Double)
        param.setMetadata({'widget_wrapper': {'decimals': 3}})

        self.addParameter(param)

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.MAXIMALDISTANCE,
                "Add maximal distance value (with sampling equal to maximal sampling distance)",
                defaultValue=False))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_TABLE, "Output table"))

    def checkParameterValues(self, parameters, context):

        distances = self.parameterAsMatrix(parameters, self.DISTANCES, context)

        if len(distances) < 1:
            msg = f"Legth of distances must be at least 1. It is {len(distances)}."

            return False, msg

        for distance in distances:

            try:
                float(distance)

            except ValueError:

                msg = f"Cannot convert value `{distance}` to float number."

                return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback: QgsProcessingFeedback):

        angle = self.parameterAsDouble(parameters, self.ANGLE, context)
        distances = self.parameterAsMatrix(parameters, self.DISTANCES, context)
        maximal_distance = self.parameterAsBoolean(parameters, self.MAXIMALDISTANCE, context)
        default_sampling_size = self.parameterAsDouble(parameters, self.DEFAULT_SAMPLING_DISTANCE,
                                                       context)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.SIZE_ANGLE, QVariant.Double))
        fields.append(QgsField(FieldNames.DISTANCE, QVariant.Double))
        fields.append(QgsField(FieldNames.SIZE, QVariant.Double))

        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT_TABLE, context, fields,
                                             QgsWkbTypes.NoGeometry)

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_TABLE))

        result_string_print = "Sizes at distances:\n" \
                              "Distance - Size\n"

        angle = float(angle)

        maximal_sampling_distance = 0

        f = QgsFeature(fields)
        f.setAttribute(f.fieldNameIndex(FieldNames.SIZE_ANGLE), float(angle))
        f.setAttribute(f.fieldNameIndex(FieldNames.DISTANCE), 0)
        f.setAttribute(f.fieldNameIndex(FieldNames.SIZE), default_sampling_size)

        sink.addFeature(f)

        result_string_print += f"{0} - {default_sampling_size}\n"

        for distance in distances:

            distance = float(distance)

            size = round((math.tan(math.radians(angle))) * distance, 3)

            result_string_print += f"{distance} - {size}\n"

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
        return "calculatesizes"

    def displayName(self):
        return "Calculate Object Sizes"

    def group(self):
        return "Calculate Parameters Settings"

    def groupId(self):
        return "parametersettings"

    def createInstance(self):
        return ObjectSizesAlgorithm()

    def helpUrl(self):
        pass
        return "https://jancaha.github.io/qgis_los_tools/tools/Calculate%20Parameters%20Settings/tool_sizes_at_distances/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
