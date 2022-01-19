import math

from qgis.core import (QgsProcessingAlgorithm, QgsProcessingParameterNumber, QgsProcessingFeedback,
                       QgsProcessingOutputNumber)


class ObjectDetectionAngleAlgorithm(QgsProcessingAlgorithm):

    SIZE = "Size"
    DISTANCE = "Distance"
    OUTPUT_ANGLE = "OutputAngle"

    def initAlgorithm(self, config=None):

        param = QgsProcessingParameterNumber(self.SIZE,
                                             "Size of the object (in meters)",
                                             QgsProcessingParameterNumber.Double,
                                             defaultValue=1,
                                             minValue=0.001,
                                             optional=False)

        param.setMetadata({'widget_wrapper': {'decimals': 3}})

        self.addParameter(param)

        param = QgsProcessingParameterNumber(self.DISTANCE,
                                             "Distance of the object (in meters)",
                                             QgsProcessingParameterNumber.Double,
                                             defaultValue=1000,
                                             minValue=0.001,
                                             optional=False)

        param.setMetadata({'widget_wrapper': {'decimals': 3}})

        self.addParameter(param)

        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT_ANGLE,
                "Angle size (in degrees) to detect object of given size and the given distance"))

    def processAlgorithm(self, parameters, context, feedback: QgsProcessingFeedback):

        size = self.parameterAsDouble(parameters, self.SIZE, context)
        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)

        angle = math.degrees(math.atan(size / distance))

        feedback.pushInfo(
            "Angle to detect object of size {0} meters at distance {1} meters is {2} degrees (rounded to 3 decimal places)."
            .format(size, distance, round(angle, 3)))

        return {self.OUTPUT_ANGLE: angle}

    def name(self):
        return "calculateobjectangle"

    def displayName(self):
        return "Calculate object detection angle"

    def group(self):
        return "Object distances"

    def groupId(self):
        return "objectsizes"

    def createInstance(self):
        return ObjectDetectionAngleAlgorithm()

    def helpUrl(self):
        pass
        # return "https://jancaha.github.io/qgis_los_tools/tools/Points%20Creation/tool_points_around/"
