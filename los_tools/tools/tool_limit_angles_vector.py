from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsFeatureRequest,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsField,
    QgsFeature,
    QgsWkbTypes,
    QgsFields)

from qgis.PyQt.QtCore import QVariant
from los_tools.constants.field_names import FieldNames
from los_tools.tools.util_functions import get_los_type
from los_tools.constants.names_constants import NamesConstants


class LimitAnglesAlgorithm(QgsProcessingAlgorithm):

    LOS_LAYER = "LoSLayer"
    OBJECT_LAYER = "ObjectLayer"
    OUTPUT_TABLE = "OutputTable"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LOS_LAYER,
                "LoS layer",
                [QgsProcessing.TypeVectorLine])
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.OBJECT_LAYER,
                "Object layer",
                [QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon])
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_TABLE,
                "Output table")
        )

    def checkParameterValues(self, parameters, context):

        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)
        object_layer = self.parameterAsVectorLayer(parameters, self.OBJECT_LAYER, context)

        field_names = los_layer.fields().names()

        if FieldNames.LOS_TYPE not in field_names:

            msg = "Fields specific for LoS without target not found in current layer ({0}). " \
                  "Cannot extract use this layer ot calculate limit angles.".format(FieldNames.LOS_TYPE)

            return False, msg

        los_type = get_los_type(los_layer, field_names)

        if los_type != NamesConstants.LOS_NO_TARGET:

            msg = "LoS must be of type `{0}` to extract horizon lines but type `{1}` found." \
                .format(NamesConstants.LOS_NO_TARGET, los_type)

            return False, msg

        if object_layer.featureCount() != 1:

            msg = "Object layer must have only one feature. Currently it has `{0}` features." \
                .format(object_layer.featureCount())

            return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):

        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)
        object_layer = self.parameterAsVectorLayer(parameters, self.OBJECT_LAYER, context)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.ID_OBSERVER, QVariant.Int))
        fields.append(QgsField(FieldNames.AZIMUTH_MIN, QVariant.Double))
        fields.append(QgsField(FieldNames.AZIMUTH_MAX, QVariant.Double))

        sink, dest_id = self.parameterAsSink(parameters,
                                             self.OUTPUT_TABLE,
                                             context,
                                             fields,
                                             QgsWkbTypes.NoGeometry,
                                             los_layer.sourceCrs())

        id_values = list(los_layer.uniqueValues(los_layer.fields().indexFromName(FieldNames.ID_OBSERVER)))

        total = 100.0 / len(id_values) if len(id_values) > 0 else 0
        i = 0

        object_layer_features = object_layer.getFeatures()

        for object_layer_feature in object_layer_features:
            object_layer_feature_geom = object_layer_feature.geometry()

        for id_value in id_values:

            if feedback.isCanceled():
                break

            request = QgsFeatureRequest()
            request.setFilterExpression("{} = '{}'".format(FieldNames.ID_OBSERVER, id_value))
            order_by_clause = QgsFeatureRequest.OrderByClause(FieldNames.AZIMUTH, ascending=True)
            request.setOrderBy(QgsFeatureRequest.OrderBy([order_by_clause]))

            features = los_layer.getFeatures(request)

            azimuths = []

            for feature in features:

                if feature.geometry().intersects(object_layer_feature_geom):
                    azimuths.append(feature.attribute(FieldNames.AZIMUTH))

            if 1 < len(azimuths):
                f = QgsFeature(fields)
                f.setAttribute(f.fieldNameIndex(FieldNames.ID_OBSERVER),
                               int(id_value))
                f.setAttribute(f.fieldNameIndex(FieldNames.AZIMUTH_MIN),
                               min(azimuths))
                f.setAttribute(f.fieldNameIndex(FieldNames.AZIMUTH_MAX),
                               max(azimuths))

                sink.addFeature(f)

            i += 1
            feedback.setProgress(int(i * total))

        return {self.OUTPUT_TABLE: dest_id}

    def name(self):
        return "limitangles"

    def displayName(self):
        return "Extract Limit Angles"

    def group(self):
        return "Angles"

    def groupId(self):
        return "angles"

    def createInstance(self):
        return LimitAnglesAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/Angles/tool_limit_angles_vector/"
