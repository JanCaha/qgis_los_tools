from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterBoolean,
    QgsField,
    QgsFeature,
    QgsWkbTypes,
    QgsFields,
    QgsMessageLog,
    Qgis)

from qgis.PyQt.QtCore import QVariant
from los_tools.constants.field_names import FieldNames
from los_tools.classes.classes_los import LoSLocal, LoSGlobal, LoSWithoutTarget
from los_tools.tools.util_functions import wkt_to_array_points, get_los_type
from los_tools.constants.names_constants import NamesConstants


class ExtractPointsLoSAlgorithm(QgsProcessingAlgorithm):

    LOS_LAYER = "LoSLayer"
    OUTPUT_LAYER = "OutputLayer"
    CURVATURE_CORRECTIONS = "CurvatureCorrections"
    REFRACTION_COEFFICIENT = "RefractionCoefficient"
    ONLY_VISIBLE = "OnlyVisiblePoints"

    horizons_types = [NamesConstants.HORIZON_LOCAL,
                      NamesConstants.HORIZON_GLOBAL]

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LOS_LAYER,
                "LoS layer",
                [QgsProcessing.TypeVectorLine])
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

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ONLY_VISIBLE,
                "Export only visible points"
            )
        )

    def checkParameterValues(self, parameters, context):

        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)

        field_names = los_layer.fields().names()

        if FieldNames.LOS_TYPE not in field_names:

            msg = "Fields specific for LoS not found in current layer ({0}). " \
                  "Cannot extract horizons from this layer.".format(FieldNames.LOS_TYPE)
            QgsMessageLog.logMessage(msg,
                                     "los_tools",
                                     Qgis.MessageLevel.Critical)
            return False, msg

        return True, "OK"

    def processAlgorithm(self, parameters, context, feedback):

        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)
        curvature_corrections = self.parameterAsBool(parameters, self.CURVATURE_CORRECTIONS, context)
        ref_coeff = self.parameterAsDouble(parameters, self.REFRACTION_COEFFICIENT, context)
        only_visible = self.parameterAsBool(parameters, self.ONLY_VISIBLE, context)

        field_names = los_layer.fields().names()

        los_type = get_los_type(los_layer, field_names)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.ID_OBSERVER, QVariant.Int))
        fields.append(QgsField(FieldNames.ID_TARGET, QVariant.Int))
        fields.append(QgsField(FieldNames.VISIBLE, QVariant.Bool))

        sink, dest_id = self.parameterAsSink(parameters,
                                             self.OUTPUT_LAYER,
                                             context,
                                             fields,
                                             QgsWkbTypes.Point25D,
                                             los_layer.sourceCrs())

        feature_count = los_layer.featureCount()
        total = 100.0 / feature_count if feature_count else 0

        los_iterator = los_layer.getFeatures()

        for feature_number, los_feature in enumerate(los_iterator):

            if feedback.isCanceled():
                break

            if los_type == NamesConstants.LOS_LOCAL:
                los = LoSLocal(wkt_to_array_points(los_feature.geometry().asWkt()),
                               observer_offset=los_feature.attribute(FieldNames.OBSERVER_OFFSET),
                               target_offset=los_feature.attribute(FieldNames.TARGET_OFFSET),
                               use_curvature_corrections=curvature_corrections,
                               refraction_coefficient=ref_coeff)

            elif los_type == NamesConstants.LOS_GLOBAL:
                los = LoSGlobal(wkt_to_array_points(los_feature.geometry().asWkt()),
                                observer_offset=los_feature.attribute(FieldNames.OBSERVER_OFFSET),
                                target_offset=los_feature.attribute(FieldNames.TARGET_OFFSET),
                                target_x=los_feature.attribute(FieldNames.TARGET_X),
                                target_y=los_feature.attribute(FieldNames.TARGET_Y),
                                use_curvature_corrections=curvature_corrections,
                                refraction_coefficient=ref_coeff)

            elif los_type == NamesConstants.LOS_NO_TARGET:
                los = LoSWithoutTarget(wkt_to_array_points(los_feature.geometry().asWkt()),
                                       observer_offset=los_feature.attribute(FieldNames.OBSERVER_OFFSET),
                                       use_curvature_corrections=curvature_corrections,
                                       refraction_coefficient=ref_coeff)

            for i in range(0, len(los.points)):

                export_point = False

                if only_visible:
                    if los.visible[i]:
                        export_point = True
                else:
                    export_point = True

                if export_point:

                    f = QgsFeature(fields)
                    f.setGeometry(los.get_geom_at_index(i))
                    f.setAttribute(f.fieldNameIndex(FieldNames.ID_OBSERVER),
                                   los_feature.attribute(FieldNames.ID_OBSERVER))
                    f.setAttribute(f.fieldNameIndex(FieldNames.ID_TARGET),
                                   los_feature.attribute(FieldNames.ID_TARGET))
                    f.setAttribute(f.fieldNameIndex(FieldNames.VISIBLE),
                                   los.visible[i])

                    sink.addFeature(f)

            feedback.setProgress(int(feature_number * total))

        return {self.OUTPUT_LAYER: dest_id}

    def name(self):
        return "extractpointslos"

    def displayName(self):
        return "Extract Points from LoS"

    def group(self):
        return "LoS Points"

    def groupId(self):
        return "points"

    def createInstance(self):
        return ExtractPointsLoSAlgorithm()
