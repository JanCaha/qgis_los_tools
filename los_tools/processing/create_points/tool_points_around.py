import numpy as np

from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSource, QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterDistance, QgsField,
                       QgsFeature, QgsWkbTypes, QgsGeometry, QgsFields, QgsPointXY,
                       QgsProcessingUtils, QgsProcessingException)

from qgis.PyQt.QtCore import QVariant

from los_tools.constants.field_names import FieldNames
from los_tools.processing.tools.util_functions import get_max_decimal_numbers, round_all_values
from los_tools.utils import get_doc_file


class CreatePointsAroundAlgorithm(QgsProcessingAlgorithm):

    INPUT_LAYER = "InputLayer"
    OUTPUT_LAYER = "OutputLayer"
    ANGLE_START = "AngleStart"
    ANGLE_END = "AngleEnd"
    ANGLE_STEP = "AngleStep"
    ID_FIELD = "IdField"
    DISTANCE = "Distance"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT_LAYER, "Input point layer",
                                                [QgsProcessing.TypeVectorPoint]))

        self.addParameter(
            QgsProcessingParameterField(self.ID_FIELD,
                                        "ID field to assign to output",
                                        parentLayerParameterName=self.INPUT_LAYER,
                                        type=QgsProcessingParameterField.Numeric,
                                        optional=True))

        self.addParameter(
            QgsProcessingParameterNumber(self.ANGLE_START,
                                         "Minimal angle",
                                         QgsProcessingParameterNumber.Double,
                                         defaultValue=0.0,
                                         minValue=0.0,
                                         maxValue=360.0,
                                         optional=False))

        self.addParameter(
            QgsProcessingParameterNumber(self.ANGLE_END,
                                         "Maximal angle",
                                         QgsProcessingParameterNumber.Double,
                                         defaultValue=359.999,
                                         minValue=0.0,
                                         maxValue=360.0,
                                         optional=False))

        self.addParameter(
            QgsProcessingParameterNumber(self.ANGLE_STEP,
                                         "Angle step",
                                         QgsProcessingParameterNumber.Double,
                                         defaultValue=1.0,
                                         minValue=0.001,
                                         maxValue=360.0,
                                         optional=False))

        self.addParameter(
            QgsProcessingParameterDistance(self.DISTANCE,
                                           "Distance",
                                           parentParameterName=self.INPUT_LAYER,
                                           defaultValue=10.0,
                                           minValue=0.001,
                                           optional=False))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_LAYER, "Output layer"))

    def processAlgorithm(self, parameters, context, feedback):

        input_layer = self.parameterAsSource(parameters, self.INPUT_LAYER, context)

        if input_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_LAYER))

        id_field = self.parameterAsString(parameters, self.ID_FIELD, context)
        angle_min = self.parameterAsDouble(parameters, self.ANGLE_START, context)
        angle_max = self.parameterAsDouble(parameters, self.ANGLE_END, context)
        angle_step = self.parameterAsDouble(parameters, self.ANGLE_STEP, context)

        angles = np.arange(angle_min, angle_max + 0.000000001 * angle_step,
                           step=angle_step).tolist()

        round_digits = get_max_decimal_numbers([angle_min, angle_max, angle_step])

        angles = round_all_values(angles, round_digits)

        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.ID_ORIGINAL_POINT, QVariant.Int))
        fields.append(QgsField(FieldNames.AZIMUTH, QVariant.Double))
        fields.append(QgsField(FieldNames.ANGLE_STEP_POINTS, QVariant.Double))

        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT_LAYER, context, fields,
                                             QgsWkbTypes.Point, input_layer.sourceCrs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LAYER))

        feature_count = input_layer.featureCount()

        iterator = input_layer.getFeatures()

        for cnt, feature in enumerate(iterator):

            if feedback.isCanceled():
                break

            for angle in angles:

                new_point: QgsPointXY = feature.geometry().asPoint().project(distance, angle)

                f = QgsFeature(fields)
                f.setGeometry(QgsGeometry().fromPointXY(new_point))
                f.setAttribute(f.fieldNameIndex(FieldNames.ID_ORIGINAL_POINT),
                               int(feature.attribute(id_field)))
                f.setAttribute(f.fieldNameIndex(FieldNames.AZIMUTH), float(angle))
                f.setAttribute(f.fieldNameIndex(FieldNames.ANGLE_STEP_POINTS), float(angle_step))

                sink.addFeature(f)

            feedback.setProgress((cnt / feature_count) * 100)

        return {self.OUTPUT_LAYER: dest_id}

    def name(self):
        return "pointsaround"

    def displayName(self):
        return "Create Points Around"

    def group(self):
        return "Points Creation"

    def groupId(self):
        return "pointscreation"

    def createInstance(self):
        return CreatePointsAroundAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/Points%20Creation/tool_points_around/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
