from qgis.core import (
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingUtils,
    QgsProject,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant

from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.processing.tools.util_functions import get_los_type
from los_tools.utils import get_doc_file


class LimitAnglesAlgorithm(QgsProcessingAlgorithm):
    LOS_LAYER = "LoSLayer"
    OBJECT_LAYER = "ObjectLayer"
    OBJECT_LAYER_FIELD_ID = "ObjectLayerID"
    OUTPUT_TABLE = "OutputTable"

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.LOS_LAYER, "LoS layer", [QgsProcessing.TypeVectorLine])
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.OBJECT_LAYER,
                "Object layer",
                [QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.OBJECT_LAYER_FIELD_ID,
                "Objects layer ID field",
                parentLayerParameterName=self.OBJECT_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=False,
            )
        )

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_TABLE, "Output table"))

    def checkParameterValues(self, parameters, context):
        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)

        field_names = los_layer.fields().names()

        if FieldNames.LOS_TYPE not in field_names:
            msg = (
                "Fields specific for LoS without target not found in current layer ({0}). "
                "Cannot extract use this layer ot calculate limit angles.".format(FieldNames.LOS_TYPE)
            )

            return False, msg

        los_type = get_los_type(los_layer, field_names)

        if los_type != NamesConstants.LOS_NO_TARGET:
            msg = "LoS must be of type `{0}` to extract horizon lines but type `{1}` found.".format(
                NamesConstants.LOS_NO_TARGET, los_type
            )

            return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):
        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)

        if los_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.LOS_LAYER))

        object_layer = self.parameterAsVectorLayer(parameters, self.OBJECT_LAYER, context)

        if object_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.OBJECT_LAYER))

        field_id = self.parameterAsString(parameters, self.OBJECT_LAYER_FIELD_ID, context)

        if object_layer.crs() != los_layer.crs():
            coord_transform = QgsCoordinateTransform(object_layer.crs(), los_layer.crs(), QgsProject.instance())
        else:
            coord_transform = None

        fields = QgsFields()
        fields.append(QgsField(FieldNames.ID_OBSERVER, QVariant.Int))
        fields.append(QgsField(FieldNames.ID_OBJECT, QVariant.Int))
        fields.append(QgsField(FieldNames.AZIMUTH_MIN, QVariant.Double))
        fields.append(QgsField(FieldNames.AZIMUTH_MAX, QVariant.Double))

        sink, dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_TABLE,
            context,
            fields,
            QgsWkbTypes.NoGeometry,
            los_layer.sourceCrs(),
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_TABLE))

        id_values = list(los_layer.uniqueValues(los_layer.fields().indexFromName(FieldNames.ID_OBSERVER)))

        total = los_layer.dataProvider().featureCount() * object_layer.dataProvider().featureCount()
        i = 0

        object_layer_features = object_layer.getFeatures()

        for object_layer_feature_count, object_layer_feature in enumerate(object_layer_features):
            object_layer_feature_geom = object_layer_feature.geometry()
            object_id = object_layer_feature.attribute(field_id)

            for id_value in id_values:
                if feedback.isCanceled():
                    break

                geom_transform = QgsGeometry(object_layer_feature_geom)

                if coord_transform:
                    geom_transform.transform(coord_transform)

                request = QgsFeatureRequest()
                request.setFilterRect(geom_transform.boundingBox())
                request.setFilterExpression("{} = '{}'".format(FieldNames.ID_OBSERVER, id_value))
                order_by_clause = QgsFeatureRequest.OrderByClause(FieldNames.AZIMUTH, ascending=True)
                request.setOrderBy(QgsFeatureRequest.OrderBy([order_by_clause]))

                features = los_layer.getFeatures(request)

                azimuths = []

                for feature in features:
                    if feature.geometry().intersects(geom_transform):
                        azimuths.append(feature.attribute(FieldNames.AZIMUTH))

                if 1 < len(azimuths):
                    az_step = azimuths[1] - azimuths[0]

                    if abs((max(azimuths) - min(azimuths)) - (az_step * (len(azimuths) - 1))) > 0.0001:
                        azimuths = [x - 360 if x > 180 else x for x in azimuths]

                    f = QgsFeature(fields)
                    f.setAttribute(f.fieldNameIndex(FieldNames.ID_OBSERVER), int(id_value))
                    f.setAttribute(f.fieldNameIndex(FieldNames.AZIMUTH_MIN), min(azimuths))
                    f.setAttribute(f.fieldNameIndex(FieldNames.AZIMUTH_MAX), max(azimuths))
                    f.setAttribute(f.fieldNameIndex(FieldNames.ID_OBJECT), object_id)

                    sink.addFeature(f)

                i += 1
                feedback.setProgress((i / total) * 100)

        return {self.OUTPUT_TABLE: dest_id}

    def name(self):
        return "limitazimuths"

    def displayName(self):
        return "Extract Limit Azimuths"

    def group(self):
        return "Azimuths"

    def groupId(self):
        return "azimuths"

    def createInstance(self):
        return LimitAnglesAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/Angles/tool_limit_angles_vector/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
