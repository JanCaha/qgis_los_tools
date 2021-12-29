import math

from qgis.core import (QgsProcessingAlgorithm, QgsProcessingParameterMatrix,
                       QgsProcessingParameterNumber, QgsProcessingFeedback, QgsFields, QgsField,
                       QgsWkbTypes, QgsProcessingParameterFeatureSink, QgsFeature)

from qgis.PyQt.QtCore import QVariant

from los_tools.constants.field_names import FieldNames


class ObjectSizesAlgorithm(QgsProcessingAlgorithm):

    ANGLE = "Angle"
    DISTANCES = "Distance"
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

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_TABLE, "Output table"))

    def processAlgorithm(self, parameters, context, feedback: QgsProcessingFeedback):

        angle = self.parameterAsDouble(parameters, self.ANGLE, context)
        distances = self.parameterAsMatrix(parameters, self.DISTANCES, context)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.SIZE_ANGLE, QVariant.Double))
        fields.append(QgsField(FieldNames.DISTANCE, QVariant.Double))
        fields.append(QgsField(FieldNames.SIZE, QVariant.Double))

        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT_TABLE, context, fields,
                                             QgsWkbTypes.NoGeometry)

        result_string_print = "Sizes at distances:\n" \
                              "Distance - Size\n"

        sizes = []

        angle = float(angle)

        for distance in distances:

            distance = float(distance)

            size = round((math.tan(math.radians(angle))) * distance, 3)

            result_string_print += f"{distance} - {size}\n"

            sizes.append(size)

            f = QgsFeature(fields)
            f.setAttribute(f.fieldNameIndex(FieldNames.SIZE_ANGLE), float(angle))
            f.setAttribute(f.fieldNameIndex(FieldNames.DISTANCE), float(distance))
            f.setAttribute(f.fieldNameIndex(FieldNames.SIZE), float(size))

            sink.addFeature(f)

        feedback.pushInfo(result_string_print)

        return {self.OUTPUT_TABLE: dest_id}

    def name(self):
        return "calculatesizes"

    def displayName(self):
        return "Calculate object sizes"

    def group(self):
        return "Object sizes"

    def groupId(self):
        return "objectsizes"

    def createInstance(self):
        return ObjectSizesAlgorithm()

    def helpUrl(self):
        pass
        # return "https://jancaha.github.io/qgis_los_tools/tools/Points%20Creation/tool_points_around/"
