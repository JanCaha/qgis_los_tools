from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterBoolean,
    QgsField,
    edit)

from qgis.PyQt.QtCore import QVariant

from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.classes.classes_los import LoSLocal, LoSGlobal, LoSWithoutTarget
from los_tools.tools.util_functions import wkt_to_array_points, get_los_type
from los_tools.tools.util_functions import get_doc_file

class AnalyseLosAlgorithm(QgsProcessingAlgorithm):

    LOS_LAYER = "LoSLayer"
    CURVATURE_CORRECTIONS = "CurvatureCorrections"
    REFRACTION_COEFFICIENT = "RefractionCoefficient"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LOS_LAYER,
                "LoS layer",
                [QgsProcessing.TypeVectorLine])
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

        if not (FieldNames.LOS_TYPE in field_names and
                FieldNames.ID_OBSERVER in field_names and
                FieldNames.ID_TARGET in field_names):

            msg = "Fields specific for LoS not found in current layer ({0}, {1}, {2}). " \
                  "Cannot analyse the layer as LoS.".format(FieldNames.LOS_TYPE,
                                                            FieldNames.ID_OBSERVER,
                                                            FieldNames.ID_TARGET)

            return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):

        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)
        curvature_corrections = self.parameterAsBool(parameters, self.CURVATURE_CORRECTIONS, context)
        ref_coeff = self.parameterAsDouble(parameters, self.REFRACTION_COEFFICIENT, context)

        field_names = los_layer.fields().names()

        los_type = get_los_type(los_layer, field_names)

        los_layer_dataprovider = los_layer.dataProvider()

        if los_type == NamesConstants.LOS_LOCAL:
            los_layer_dataprovider.addAttributes([
                QgsField(FieldNames.VISIBLE, QVariant.Bool),
                QgsField(FieldNames.VIEWING_ANGLE, QVariant.Double),
                QgsField(FieldNames.ELEVATION_DIFF, QVariant.Double),
                QgsField(FieldNames.ANGLE_DIFF_LH, QVariant.Double),
                QgsField(FieldNames.ELEVATION_DIFF_LH, QVariant.Double),
                QgsField(FieldNames.SLOPE_DIFFERENCE_LH, QVariant.Double),
                QgsField(FieldNames.HORIZON_COUNT, QVariant.Int),
                QgsField(FieldNames.DISTANCE_LH, QVariant.Double)
            ])
            # los_layer.addAttribute(QgsField(FieldNames.FUZZY_VISIBILITY, QVariant.Double))
        elif los_type == NamesConstants.LOS_GLOBAL:
            los_layer_dataprovider.addAttributes([
                QgsField(FieldNames.VISIBLE, QVariant.Bool),
                QgsField(FieldNames.ANGLE_DIFF_GH, QVariant.Double),
                QgsField(FieldNames.ELEVATION_DIFF_GH, QVariant.Double),
                QgsField(FieldNames.HORIZON_COUNT_BEHIND, QVariant.Int),
                QgsField(FieldNames.DISTANCE_GH, QVariant.Double)
            ])
        elif los_type == NamesConstants.LOS_NO_TARGET:
            los_layer_dataprovider.addAttributes([
                QgsField(FieldNames.MAXIMAL_VERTICAL_ANGLE, QVariant.Double),
                QgsField(FieldNames.DISTANCE_GH, QVariant.Double),
                QgsField(FieldNames.DISTANCE_LH, QVariant.Double),
                QgsField(FieldNames.VERTICAL_ANGLE_LH, QVariant.Double)
            ])

        los_layer.updateFields()

        feature_count = los_layer.featureCount()
        i = 0

        with edit(los_layer):
            for los_feature in los_layer.getFeatures():
                if feedback.isCanceled():
                    break

                if los_type == NamesConstants.LOS_LOCAL:
                    los = LoSLocal(wkt_to_array_points(los_feature.geometry().asWkt()),
                                   observer_offset=los_feature.attribute(FieldNames.OBSERVER_OFFSET),
                                   target_offset=los_feature.attribute(FieldNames.TARGET_OFFSET),
                                   use_curvature_corrections=curvature_corrections,
                                   refraction_coefficient=ref_coeff)

                    los_feature[FieldNames.VISIBLE] = los.is_target_visible()
                    los_feature[FieldNames.VIEWING_ANGLE] = los.get_view_angle()
                    los_feature[FieldNames.ELEVATION_DIFF] = los.get_elevation_difference()
                    los_feature[FieldNames.ANGLE_DIFF_LH] = los.get_angle_difference_local_horizon()
                    los_feature[FieldNames.ELEVATION_DIFF_LH] = los.get_elevation_difference_local_horizon()
                    los_feature[FieldNames.SLOPE_DIFFERENCE_LH] = los.get_los_slope_difference()
                    los_feature[FieldNames.HORIZON_COUNT] = los.get_local_horizon_count()
                    los_feature[FieldNames.DISTANCE_LH] = los.get_local_horizon_distance()

                elif los_type == NamesConstants.LOS_GLOBAL:
                    los = LoSGlobal(wkt_to_array_points(los_feature.geometry().asWkt()),
                                    observer_offset=los_feature.attribute(FieldNames.OBSERVER_OFFSET),
                                    target_offset=los_feature.attribute(FieldNames.TARGET_OFFSET),
                                    target_x=los_feature.attribute(FieldNames.TARGET_X),
                                    target_y=los_feature.attribute(FieldNames.TARGET_Y),
                                    use_curvature_corrections=curvature_corrections,
                                    refraction_coefficient=ref_coeff)

                    los_feature[FieldNames.VISIBLE] = los.is_target_visible()
                    los_feature[FieldNames.ANGLE_DIFF_GH] = los.get_angle_difference_global_horizon()
                    los_feature[FieldNames.ELEVATION_DIFF_GH] = los.get_elevation_difference_global_horizon()
                    los_feature[FieldNames.HORIZON_COUNT_BEHIND] = los.get_horizon_count()
                    los_feature[FieldNames.DISTANCE_GH] = los.get_horizon_distance()

                elif los_type == NamesConstants.LOS_NO_TARGET:
                    los = LoSWithoutTarget(wkt_to_array_points(los_feature.geometry().asWkt()),
                                           observer_offset=los_feature.attribute(FieldNames.OBSERVER_OFFSET),
                                           use_curvature_corrections=curvature_corrections,
                                           refraction_coefficient=ref_coeff)

                    los_feature[FieldNames.MAXIMAL_VERTICAL_ANGLE] = los.get_maximal_vertical_angle()
                    los_feature[FieldNames.DISTANCE_LH] = los.get_max_local_horizon_distance()
                    los_feature[FieldNames.DISTANCE_GH] = los.get_global_horizon_distance()
                    los_feature[FieldNames.VERTICAL_ANGLE_LH] = los.get_max_local_horizon_angle()

                los_layer.updateFeature(los_feature)
                i += 1
                feedback.setProgress(int((i/feature_count)*100))

        return {}

    def name(self):
        return "analyselos"

    def displayName(self):
        return "Analyse LoS"

    def group(self):
        return "LoS Analysis"

    def groupId(self):
        return "losanalysis"

    def createInstance(self):
        return AnalyseLosAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/LoS%20Analysis/tool_analyse_los/"

    def shortHelpString(self):

        return get_doc_file(__file__, self)
