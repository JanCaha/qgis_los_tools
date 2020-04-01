import math
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterBoolean,
    QgsField,
    QgsFeature,
    QgsWkbTypes,
    QgsFeatureRequest,
    QgsFields,
    QgsLineString,
    QgsMessageLog,
    Qgis)

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

    horizons_types = [NamesConstants.HORIZON_MAX_LOCAL,
                      NamesConstants.HORIZON_GLOBAL]

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LOS_LAYER,
                "LoS layer",
                [QgsProcessing.TypeVectorLine])
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.HORIZON_TYPE,
                "Horizon type",
                options=self.horizons_types,
                defaultValue=1)
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LAYER,
                "Output layer")
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CURVATURE_CORRECTIONS,
                "Use curvature corrections?",
                defaultValue=True)
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.REFRACTION_COEFFICIENT,
                "Refraction coefficient value",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.13
            )
        )

    def checkParameterValues(self, parameters, context):

        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)

        field_names = los_layer.fields().names()

        if not FieldNames.LOS_TYPE in field_names:
            msg = "Fields specific for LoS not found in current layer ({0}). " \
                  "Cannot extract horizon lines from this layer.".format(FieldNames.LOS_TYPE)

            QgsMessageLog.logMessage(msg,
                                     "los_tools",
                                     Qgis.MessageLevel.Critical)
            return False, msg

        los_type = get_los_type(los_layer, field_names)

        if los_type != NamesConstants.LOS_NO_TARGET:
            msg = "LoS must be of type `{0}` to extract horizon lines but type `{1}` found." \
                .format(NamesConstants.LOS_NO_TARGET, los_type)

            QgsMessageLog.logMessage(msg,
                                     "los_tools",
                                     Qgis.MessageLevel.Critical)

            return False, msg

        return True, "OK"

    def processAlgorithm(self, parameters, context, feedback):

        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)
        horizon_type = self.horizons_types[self.parameterAsEnum(parameters, self.HORIZON_TYPE, context)]
        curvature_corrections = self.parameterAsBool(parameters, self.CURVATURE_CORRECTIONS, context)
        ref_coeff = self.parameterAsDouble(parameters, self.REFRACTION_COEFFICIENT, context)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.HORIZON_TYPE, QVariant.String))
        fields.append(QgsField(FieldNames.ID_OBSERVER, QVariant.Int))
        fields.append(QgsField(FieldNames.OBSERVER_X, QVariant.Double))
        fields.append(QgsField(FieldNames.OBSERVER_Y, QVariant.Double))
        # test
        if horizon_type == NamesConstants.HORIZON_GLOBAL:
            fields.append(QgsField(FieldNames.POINTS_ANGLE_DIFF_GH_LH, QVariant.String))
            fields.append(QgsField(FieldNames.POINTS_ELEVATION_DIFF_GH_LH, QVariant.String))
            fields.append(QgsField(FieldNames.POINTS_DISTANCE_GH, QVariant.String))

        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT_LAYER, context, fields,
                                             QgsWkbTypes.LineStringZM, los_layer.sourceCrs())

        id_values = list(los_layer.uniqueValues(los_layer.fields().indexFromName(FieldNames.ID_OBSERVER)))

        total = 100.0 / len(id_values) if len(id_values) > 0 else 0
        i = 0

        for id_value in id_values:

            if feedback.isCanceled():
                break

            request = QgsFeatureRequest()
            request.setFilterExpression("{} = '{}'".format(FieldNames.ID_OBSERVER, id_value))
            order_by_clause = QgsFeatureRequest.OrderByClause(FieldNames.AZIMUTH, ascending=True)
            request.setOrderBy(QgsFeatureRequest.OrderBy([order_by_clause]))

            features = los_layer.getFeatures(request)

            line_points = []
            view_angles = []
            angle_diff_local_horizon = []
            elev_diff_local_horizon = []
            distances = []

            for los_feature in features:

                los = LoSWithoutTarget(wkt_to_array_points(los_feature.geometry().asWkt()),
                                       observer_offset=los_feature.attribute(FieldNames.OBSERVER_OFFSET),
                                       use_curvature_corrections=curvature_corrections,
                                       refraction_coefficient=ref_coeff)

                if horizon_type == NamesConstants.HORIZON_GLOBAL:
                    line_points.append(los.get_global_horizon())
                    view_angles.append(los.get_global_horizon_angle())
                    angle_diff_local_horizon.append(los.get_global_horizon_angle() - los.get_max_local_horizon_angle())
                    elev_diff_local_horizon.append(
                        math.tan(math.radians(los.get_global_horizon_angle() - los.get_max_local_horizon_angle()) *
                                 los.get_global_horizon_distance() - los.get_max_local_horizon_distance())
                    )
                    distances.append(los.get_global_horizon_distance())
                elif horizon_type == NamesConstants.HORIZON_MAX_LOCAL:
                    line_points.append(los.get_max_local_horizon(direction_point=True))
                    view_angles.append(los.get_max_local_horizon_angle())

            if 1 < len(line_points):
                line = QgsLineString(line_points)
                line.addMValue()

                for i in range(0, line.numPoints()):
                    line.setMAt(i, view_angles[i])

                f = QgsFeature(fields)
                f.setGeometry(line)
                f.setAttribute(f.fieldNameIndex(FieldNames.ID_OBSERVER),
                               id_value)
                f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_X),
                               los_feature.attribute(FieldNames.OBSERVER_X))
                f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_Y),
                               los_feature.attribute(FieldNames.OBSERVER_Y))
                f.setAttribute(f.fieldNameIndex(FieldNames.HORIZON_TYPE),
                               horizon_type)
                if horizon_type == NamesConstants.HORIZON_GLOBAL:
                    f.setAttribute(f.fieldNameIndex(FieldNames.POINTS_ANGLE_DIFF_GH_LH),
                                   ";".join(map(str, angle_diff_local_horizon)))
                    f.setAttribute(f.fieldNameIndex(FieldNames.POINTS_ELEVATION_DIFF_GH_LH),
                                   ";".join(map(str, elev_diff_local_horizon)))
                    f.setAttribute(f.fieldNameIndex(FieldNames.POINTS_DISTANCE_GH),
                                   ";".join(map(str, distances)))

                sink.addFeature(f)
                i += 1

                feedback.setProgress(int(i*total))

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
