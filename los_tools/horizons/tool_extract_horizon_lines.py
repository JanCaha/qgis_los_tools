from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterEnum,
                       QgsProcessingParameterNumber, QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterBoolean, QgsField,
                       QgsFeature, QgsWkbTypes, QgsFeatureRequest, QgsFields, QgsLineString,
                       QgsVectorLayer, QgsProcessingFeedback, QgsProcessingException)

from qgis.PyQt.QtCore import QVariant
from los_tools.constants.field_names import FieldNames
from los_tools.classes.classes_los import LoSWithoutTarget
from los_tools.tools.util_functions import wkt_to_array_points, get_los_type
from los_tools.constants.names_constants import NamesConstants


class ExtractHorizonLinesAlgorithm(QgsProcessingAlgorithm):

    LOS_LAYER = "LoSLayer"
    HORIZON_TYPE = "HorizonType"
    OUTPUT_LAYER = "OutputLayer"
    CURVATURE_CORRECTIONS = "CurvatureCorrections"
    REFRACTION_COEFFICIENT = "RefractionCoefficient"

    horizons_types = [NamesConstants.HORIZON_MAX_LOCAL, NamesConstants.HORIZON_GLOBAL]

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.LOS_LAYER, "LoS layer",
                                                [QgsProcessing.TypeVectorLine]))

        self.addParameter(
            QgsProcessingParameterEnum(self.HORIZON_TYPE,
                                       "Horizon type",
                                       options=self.horizons_types,
                                       defaultValue=1))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_LAYER, "Output layer"))

        self.addParameter(
            QgsProcessingParameterBoolean(self.CURVATURE_CORRECTIONS,
                                          "Use curvature corrections?",
                                          defaultValue=True))

        self.addParameter(
            QgsProcessingParameterNumber(self.REFRACTION_COEFFICIENT,
                                         "Refraction coefficient value",
                                         type=QgsProcessingParameterNumber.Double,
                                         defaultValue=0.13))

    def checkParameterValues(self, parameters, context):

        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)

        field_names = los_layer.fields().names()

        if FieldNames.LOS_TYPE not in field_names:
            msg = "Fields specific for LoS not found in current layer ({0}). " \
                  "Cannot extract horizon lines from this layer.".format(FieldNames.LOS_TYPE)

            return False, msg

        los_type = get_los_type(los_layer, field_names)

        if los_type != NamesConstants.LOS_NO_TARGET:
            msg = "LoS must be of type `{0}` to extract horizon lines but type `{1}` found." \
                .format(NamesConstants.LOS_NO_TARGET, los_type)

            return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback: QgsProcessingFeedback):

        los_layer: QgsVectorLayer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER,
                                                                context)

        if los_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.LOS_LAYER))

        horizon_type = self.horizons_types[self.parameterAsEnum(parameters, self.HORIZON_TYPE,
                                                                context)]
        curvature_corrections = self.parameterAsBool(parameters, self.CURVATURE_CORRECTIONS,
                                                     context)
        ref_coeff = self.parameterAsDouble(parameters, self.REFRACTION_COEFFICIENT, context)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.HORIZON_TYPE, QVariant.String))
        fields.append(QgsField(FieldNames.ID_OBSERVER, QVariant.Int))
        fields.append(QgsField(FieldNames.OBSERVER_X, QVariant.Double))
        fields.append(QgsField(FieldNames.OBSERVER_Y, QVariant.Double))

        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT_LAYER, context, fields,
                                             QgsWkbTypes.LineStringZM, los_layer.sourceCrs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LAYER))

        id_values = list(
            los_layer.uniqueValues(los_layer.fields().indexFromName(FieldNames.ID_OBSERVER)))

        total = 100 / los_layer.featureCount() if los_layer.featureCount() else 0

        i = 0

        for id_value in id_values:

            request = QgsFeatureRequest()
            request.setFilterExpression("{} = '{}'".format(FieldNames.ID_OBSERVER, id_value))
            order_by_clause = QgsFeatureRequest.OrderByClause(FieldNames.AZIMUTH, ascending=True)
            request.setOrderBy(QgsFeatureRequest.OrderBy([order_by_clause]))

            features = los_layer.getFeatures(request)

            line_points = []
            values = []

            for los_feature in features:

                if feedback.isCanceled():
                    break

                los = LoSWithoutTarget(wkt_to_array_points(los_feature.geometry().asWkt()),
                                       observer_offset=los_feature.attribute(
                                           FieldNames.OBSERVER_OFFSET),
                                       use_curvature_corrections=curvature_corrections,
                                       refraction_coefficient=ref_coeff)

                if horizon_type == NamesConstants.HORIZON_GLOBAL:

                    line_points.append(los.get_global_horizon())
                    values.append(los.get_global_horizon_angle())

                elif horizon_type == NamesConstants.HORIZON_MAX_LOCAL:

                    line_points.append(los.get_max_local_horizon(direction_point=True))
                    values.append(los.get_max_local_horizon_angle())

                i += 1

                feedback.setProgress(int(i * total))

            if 1 < len(line_points):

                line = QgsLineString(line_points)
                line.addMValue()

                for i in range(0, line.numPoints()):
                    line.setMAt(i, values[i])

                f = QgsFeature(fields)
                f.setGeometry(line)
                f.setAttribute(f.fieldNameIndex(FieldNames.ID_OBSERVER), id_value)
                f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_X),
                               los_feature.attribute(FieldNames.OBSERVER_X))
                f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_Y),
                               los_feature.attribute(FieldNames.OBSERVER_Y))
                f.setAttribute(f.fieldNameIndex(FieldNames.HORIZON_TYPE), horizon_type)

                sink.addFeature(f)

        return {self.OUTPUT_LAYER: dest_id}

    def name(self):
        return "extracthorizonlines"

    def displayName(self):
        return "Extract Horizon Lines"

    def group(self):
        return "Horizons"

    def groupId(self):
        return "horizons"

    def createInstance(self):
        return ExtractHorizonLinesAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/Horizons/tool_extract_horizon_lines/"
