import math

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterMatrix,
    QgsProcessingParameterNumber,
    QgsProcessingFeedback,
    QgsFields,
    QgsField,
    QgsWkbTypes,
    QgsProcessingParameterFeatureSink,
    QgsFeature)

from qgis.PyQt.QtCore import QVariant

from los_tools.constants.field_names import FieldNames


class ObjectDistancesAlgorithm(QgsProcessingAlgorithm):

    ANGLE = "Angle"
    SIZES = "Size"
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
                optional=False)
        )

        self.addParameter(
            QgsProcessingParameterMatrix(
                self.SIZES,
                "Sizes of object to calculate (in meters)",
                numberRows=1,
                headers=["Size"],
                defaultValue=[1]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_TABLE,
                "Output table")
        )

    def processAlgorithm(self, parameters, context, feedback: QgsProcessingFeedback):

        angle = self.parameterAsDouble(parameters, self.ANGLE, context)
        sizes = self.parameterAsMatrix(parameters, self.SIZES, context)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.SIZE_ANGLE, QVariant.Double))
        fields.append(QgsField(FieldNames.DISTANCE, QVariant.Double))
        fields.append(QgsField(FieldNames.SIZE, QVariant.Double))

        sink, dest_id = self.parameterAsSink(parameters,
                                             self.OUTPUT_TABLE,
                                             context,
                                             fields,
                                             QgsWkbTypes.NoGeometry)

        result_string_print = "Sizes at distances:\n" \
                              "Size - Distance\n"

        angle = float(angle)

        for size in sizes:

            size = float(size)

            distance = round(size / math.tan(math.radians(angle)), 3)

            result_string_print += f"{size} - {distance}\n"

            f = QgsFeature(fields)
            f.setAttribute(f.fieldNameIndex(FieldNames.SIZE_ANGLE),
                           float(angle))
            f.setAttribute(f.fieldNameIndex(FieldNames.DISTANCE),
                           float(distance))
            f.setAttribute(f.fieldNameIndex(FieldNames.SIZE),
                           float(size))

            sink.addFeature(f)

        feedback.pushInfo(result_string_print)

        return {self.OUTPUT_TABLE: dest_id}

    def name(self):
        return "calculatedistances"

    def displayName(self):
        return "Calculate object distances"

    def group(self):
        return "Object distances"

    def groupId(self):
        return "objectsizes"

    def createInstance(self):
        return ObjectDistancesAlgorithm()

    def helpUrl(self):
        pass
        # return "https://jancaha.github.io/qgis_los_tools/tools/Points%20Creation/tool_points_around/"
