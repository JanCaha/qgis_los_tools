import numpy as np

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSink,
    QgsField,
    QgsFeature,
    QgsWkbTypes,
    QgsGeometry,
    QgsFields)

from qgis.PyQt.QtCore import QVariant


class CreatePointsAroundAlgorithm(QgsProcessingAlgorithm):

    INPUT_LAYER = "InputLayer"
    OUTPUT_LAYER = "OutputLayer"
    ANGLE_START = "AngleStart"
    ANGLE_END = "AngleEnd"
    ANGLE_STEP = "AngleStep"
    ID_FIELD = "IdField"
    DISTANCE = "Distance"

    ID_FIELD_NAME = "id_original_point"
    ANGLE_FIELD_NAME = "azimuth"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LAYER,
                "Input point layer",
                [QgsProcessing.TypeVectorPoint])
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.ID_FIELD,
                "ID field to assign to output",
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.ANGLE_START,
                "Minimal angle",
                QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=360.0,
                optional=False)
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.ANGLE_END,
                "Maximal angle",
                QgsProcessingParameterNumber.Double,
                defaultValue=359.0,
                minValue=0.0,
                maxValue=360.0,
                optional=False)
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.ANGLE_STEP,
                "Angle step",
                QgsProcessingParameterNumber.Double,
                defaultValue=1.0,
                minValue=0.001,
                maxValue=360.0,
                optional=False)
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.DISTANCE,
                "Distance",
                QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0.001,
                optional=False)
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LAYER,
                "Output layer")
        )

    def processAlgorithm(self, parameters, context, feedback):

        input_layer = self.parameterAsSource(parameters, self.INPUT_LAYER, context)
        id_field = self.parameterAsString(parameters, self.ID_FIELD, context)
        angle_min = self.parameterAsDouble(parameters, self.ANGLE_START, context)
        angle_max = self.parameterAsDouble(parameters, self.ANGLE_END, context)
        angle_step = self.parameterAsDouble(parameters, self.ANGLE_STEP, context)
        angles = np.arange(angle_min, np.nextafter(angle_max, np.Inf), step=angle_step).tolist()
        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)

        fields = QgsFields()
        fields.append(QgsField(self.ID_FIELD_NAME, QVariant.Int))
        fields.append(QgsField(self.ANGLE_FIELD_NAME, QVariant.Double))

        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT_LAYER, context, fields,
                                             QgsWkbTypes.Point, input_layer.sourceCrs())

        feature_count = input_layer.featureCount()
        total = 100.0 / feature_count if feature_count else 0

        iterator = input_layer.getFeatures()

        for cnt, feature in enumerate(iterator):
            if feedback.isCanceled():
                break

            for angle in angles:

                new_point = feature.geometry().asPoint().project(distance, angle)

                f = QgsFeature(fields)
                f.setGeometry(QgsGeometry.fromPointXY(new_point))
                f.setAttribute(f.fieldNameIndex(self.ID_FIELD_NAME), int(feature.attribute(id_field)))
                f.setAttribute(f.fieldNameIndex(self.ANGLE_FIELD_NAME), float(angle))

                sink.addFeature(f)

            feedback.setProgress(int(cnt * total))

        return {self.OUTPUT_LAYER: dest_id}

    def name(self):
        return "pointsaround"

    def displayName(self):
        return "Create points around"

    def group(self):
        return "Points creation"

    def groupId(self):
        return "pointscreation"

    def createInstance(self):
        return CreatePointsAroundAlgorithm()

    # def shortHelpString(self):
    #     file = os.path.dirname(__file__) + "/doc/tool_points_around.txt"
    #     QgsMessageLog.logMessage(file,
    #                              "los_tools",
    #                              Qgis.MessageLevel.Critical)
    #     if not os.path.exists(file):
    #         return ""
    #     with open(file) as help_file:
    #         help = help_file.read()
    #         QgsMessageLog.logMessage(help,
    #                                  "los_tools",
    #                                  Qgis.MessageLevel.Critical)
    #     return help
