from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterField,
    QgsField,
    QgsFeature,
    QgsWkbTypes,
    QgsFields)

from qgis.PyQt.QtCore import QVariant
from los_tools.constants.field_names import FieldNames


class AzimuthPointPolygonAlgorithm(QgsProcessingAlgorithm):

    POINT_LAYER = "PointLayer"
    POINT_LAYER_FIELD_ID = "PointLayerID"
    OBJECT_LAYER = "ObjectLayer"
    OBJECT_LAYER_FIELD_ID = "ObjectLayerID"
    OUTPUT_TABLE = "OutputTable"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POINT_LAYER,
                "Point layer",
                [QgsProcessing.TypeVectorPoint])
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.POINT_LAYER_FIELD_ID,
                "Point layer ID field",
                parentLayerParameterName=self.POINT_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.OBJECT_LAYER,
                "Object layer",
                [QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon])
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.OBJECT_LAYER_FIELD_ID,
                "Object layer ID field",
                parentLayerParameterName=self.OBJECT_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_TABLE,
                "Output table")
        )

    def checkParameterValues(self, parameters, context):

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):

        point_layer = self.parameterAsVectorLayer(parameters, self.POINT_LAYER, context)
        point_field_id = self.parameterAsString(parameters, self.POINT_LAYER_FIELD_ID, context)
        object_layer = self.parameterAsVectorLayer(parameters, self.OBJECT_LAYER, context)
        object_field_id = self.parameterAsString(parameters, self.OBJECT_LAYER_FIELD_ID, context)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.ID_POINT, QVariant.Int))
        fields.append(QgsField(FieldNames.ID_OBJECT, QVariant.Int))
        fields.append(QgsField(FieldNames.AZIMUTH, QVariant.Double))

        sink, dest_id = self.parameterAsSink(parameters,
                                             self.OUTPUT_TABLE,
                                             context,
                                             fields,
                                             QgsWkbTypes.NoGeometry,
                                             point_layer.sourceCrs())

        total = point_layer.dataProvider().featureCount() * object_layer.dataProvider().featureCount()
        i = 0

        object_layer_features = object_layer.getFeatures()

        for object_layer_feature_count, object_layer_feature in enumerate(object_layer_features):

            for point_layer_feature_count, point_layer_feature in enumerate(point_layer.getFeatures()):

                if feedback.isCanceled():
                    break

                azimuth = point_layer_feature.geometry().centroid().asPoint().azimuth(
                    object_layer_feature.geometry().centroid().asPoint())

                if azimuth < 0:
                    azimuth = 360 + azimuth

                f = QgsFeature(fields)
                f.setAttribute(f.fieldNameIndex(FieldNames.ID_POINT),
                               point_layer_feature.attribute(point_field_id))
                f.setAttribute(f.fieldNameIndex(FieldNames.ID_OBJECT),
                               object_layer_feature.attribute(object_field_id))
                f.setAttribute(f.fieldNameIndex(FieldNames.AZIMUTH),
                               azimuth)

                sink.addFeature(f)

                i += 1
                feedback.setProgress((i/total)*100)

        return {self.OUTPUT_TABLE: dest_id}

    def name(self):
        return "azimuth"

    def displayName(self):
        return "Extract Azimuth between Points and centroids of Polygons/Lines"

    def group(self):
        return "Angles"

    def groupId(self):
        return "angles"

    def createInstance(self):
        return AzimuthPointPolygonAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/Angles/tool_azimuth/"
