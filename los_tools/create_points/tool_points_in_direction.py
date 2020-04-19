import numpy as np

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterDistance,
    QgsField,
    QgsFeature,
    QgsWkbTypes,
    QgsGeometry,
    QgsFields)

from qgis.PyQt.QtCore import QVariant

from los_tools.constants.field_names import FieldNames


class CreatePointsInDirectionAlgorithm(QgsProcessingAlgorithm):

    INPUT_LAYER = "InputLayer"
    DIRECTION_LAYER = "DirectionLayer"
    OUTPUT_LAYER = "OutputLayer"
    ANGLE_OFFSET = "AngleOffset"
    ANGLE_STEP = "AngleStep"
    ID_FIELD = "IdField"
    DISTANCE = "Distance"

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
            QgsProcessingParameterFeatureSource(
                self.DIRECTION_LAYER,
                "Main direction point layer",
                [QgsProcessing.TypeVectorPoint])
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.ANGLE_OFFSET,
                "Angle offset from the main direction",
                QgsProcessingParameterNumber.Double,
                defaultValue=20.0,
                minValue=0.0,
                maxValue=180.0,
                optional=False)
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.ANGLE_STEP,
                "Angle step",
                QgsProcessingParameterNumber.Double,
                defaultValue=1.0,
                minValue=0.001,
                maxValue=180.0,
                optional=False)
        )

        self.addParameter(
            QgsProcessingParameterDistance(
                self.DISTANCE,
                "Distance",
                parentParameterName=self.INPUT_LAYER,
                defaultValue=10.0,
                minValue=0.001,
                optional=False)
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LAYER,
                "Output layer")
        )

    def checkParameterValues(self, parameters, context):

        main_direction_layer = self.parameterAsSource(parameters, self.DIRECTION_LAYER, context)

        if main_direction_layer.featureCount() != 1:
            msg = "`Main direction point layer` should only containt one feature. " \
                  "Currently is has `{}` features.".format(main_direction_layer.featureCount())

            return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):

        input_layer = self.parameterAsSource(parameters, self.INPUT_LAYER, context)
        id_field = self.parameterAsString(parameters, self.ID_FIELD, context)
        main_direction_layer = self.parameterAsSource(parameters, self.DIRECTION_LAYER, context)
        angle_offset = self.parameterAsDouble(parameters, self.ANGLE_OFFSET, context)
        angle_step = self.parameterAsDouble(parameters, self.ANGLE_STEP, context)
        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.ID_ORIGINAL_POINT, QVariant.Int))
        fields.append(QgsField(FieldNames.ID_POINT, QVariant.Int))
        fields.append(QgsField(FieldNames.AZIMUTH, QVariant.Double))

        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT_LAYER, context, fields,
                                             QgsWkbTypes.Point, input_layer.sourceCrs())

        feature_count = input_layer.featureCount()
        total = 100.0 / feature_count if feature_count else 0

        iterator = input_layer.getFeatures()

        for cnt, feature in enumerate(iterator):
            if feedback.isCanceled():
                break

            iterator_direction = main_direction_layer.getFeatures()

            for cnt_direction, feature_direction in enumerate(iterator_direction):

                main_angle = feature.geometry().asPoint()\
                    .azimuth(feature_direction.geometry().asPoint())

                angles = np.arange(main_angle - angle_offset,
                                   main_angle + angle_offset + 0.1*angle_step,
                                   step=angle_step).tolist()

                i = 0

                for angle in angles:

                    new_point = feature.geometry().asPoint().project(distance, angle)

                    f = QgsFeature(fields)
                    f.setGeometry(QgsGeometry.fromPointXY(new_point))
                    f.setAttribute(f.fieldNameIndex(FieldNames.ID_ORIGINAL_POINT),
                                   int(feature.attribute(id_field)))
                    f.setAttribute(f.fieldNameIndex(FieldNames.AZIMUTH),
                                   float(angle))
                    f.setAttribute(f.fieldNameIndex(FieldNames.ID_POINT),
                                   int(i))

                    sink.addFeature(f)
                    i += 1

            feedback.setProgress(int(cnt * total))

        return {self.OUTPUT_LAYER: dest_id}

    def name(self):
        return "pointsdirection"

    def displayName(self):
        return "Create points in direction"

    def group(self):
        return "Points creation"

    def groupId(self):
        return "pointscreation"

    def createInstance(self):
        return CreatePointsInDirectionAlgorithm()
