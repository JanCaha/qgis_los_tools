from typing import Union

from qgis.core import (
    QgsFeature,
    QgsFeatureIterator,
    QgsField,
    QgsFields,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingUtils,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QMetaType

from los_tools.classes.classes_los import LoSGlobal, LoSLocal, LoSWithoutTarget
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.processing.tools.util_functions import get_los_type
from los_tools.utils import get_doc_file


class AnalyseLosAlgorithm(QgsProcessingAlgorithm):
    LOS_LAYER = "LoSLayer"
    CURVATURE_CORRECTIONS = "CurvatureCorrections"
    REFRACTION_COEFFICIENT = "RefractionCoefficient"
    OUTPUT_LAYER = "OutputLayer"

    def initAlgorithm(self, configuration=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.LOS_LAYER, "LoS layer", [QgsProcessing.TypeVectorLine])
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CURVATURE_CORRECTIONS,
                "Use curvature corrections?",
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.REFRACTION_COEFFICIENT,
                "Refraction coefficient value",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.13,
            )
        )

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_LAYER, "Output layer"))

    def checkParameterValues(self, parameters, context):
        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)

        field_names = los_layer.fields().names()

        if not (
            FieldNames.LOS_TYPE in field_names
            and FieldNames.ID_OBSERVER in field_names
            and FieldNames.ID_TARGET in field_names
        ):
            msg = (
                "Fields specific for LoS not found in current layer "
                f"({FieldNames.LOS_TYPE}, {FieldNames.ID_OBSERVER}, {FieldNames.ID_TARGET}). "
                "Cannot analyse the layer as LoS."
            )

            return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        los_layer: QgsVectorLayer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)

        if los_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.LOS_LAYER))

        curvature_corrections = self.parameterAsBool(parameters, self.CURVATURE_CORRECTIONS, context)
        ref_coeff = self.parameterAsDouble(parameters, self.REFRACTION_COEFFICIENT, context)

        field_names = los_layer.fields().names()

        los_type = get_los_type(los_layer, field_names)

        fields = QgsFields()

        los_layer_attributes = los_layer.dataProvider().fields().toList()

        for attribute in los_layer_attributes:
            fields.append(QgsField(attribute.name(), attribute.type()))

        if los_type == NamesConstants.LOS_LOCAL:
            fields.append(QgsField(FieldNames.VISIBLE, QMetaType.Type.Bool))
            fields.append(QgsField(FieldNames.VIEWING_ANGLE, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.ELEVATION_DIFF, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.ANGLE_DIFF_LH, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.ELEVATION_DIFF_LH, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.SLOPE_DIFFERENCE_LH, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.HORIZON_COUNT, QMetaType.Type.Int))
            fields.append(QgsField(FieldNames.DISTANCE_LH, QMetaType.Type.Double))
            # los_layer.addAttribute(QgsField(FieldNames.FUZZY_VISIBILITY, QMetaType.Type.Double))

        elif los_type == NamesConstants.LOS_GLOBAL:
            fields.append(QgsField(FieldNames.VISIBLE, QMetaType.Type.Bool))
            fields.append(QgsField(FieldNames.ANGLE_DIFF_GH, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.ELEVATION_DIFF_GH, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.HORIZON_COUNT_BEHIND, QMetaType.Type.Int))
            fields.append(QgsField(FieldNames.DISTANCE_GH, QMetaType.Type.Double))

        elif los_type == NamesConstants.LOS_NO_TARGET:
            fields.append(QgsField(FieldNames.MAXIMAL_VERTICAL_ANGLE, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.DISTANCE_GH, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.DISTANCE_LH, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.VERTICAL_ANGLE_LH, QMetaType.Type.Double))

        sink, dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_LAYER,
            context,
            fields,
            los_layer.wkbType(),
            los_layer.sourceCrs(),
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LAYER))

        feature_count = los_layer.dataProvider().featureCount()

        feedback.pushInfo(f"Analysing {feature_count} features.")

        los_layer_iterator: QgsFeatureIterator = los_layer.getFeatures()

        for los_layer_count, los_feature in enumerate(los_layer_iterator):
            if feedback.isCanceled():
                break

            f = QgsFeature(fields)
            f.setGeometry(los_feature.geometry())

            # copy attributes
            attributes = los_feature.attributes()
            i = 0
            for att in attributes:
                f.setAttribute(i, att)
                i += 1

            los: Union[LoSLocal, LoSGlobal, LoSWithoutTarget]

            if los_type == NamesConstants.LOS_LOCAL:
                los = LoSLocal.from_feature(
                    feature=los_feature,
                    curvature_corrections=curvature_corrections,
                    refraction_coefficient=ref_coeff,
                )

                f.setAttribute(f.fieldNameIndex(FieldNames.VISIBLE), los.is_target_visible())
                f.setAttribute(f.fieldNameIndex(FieldNames.VIEWING_ANGLE), los.get_view_angle())
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.ELEVATION_DIFF),
                    los.get_elevation_difference(),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.ANGLE_DIFF_LH),
                    los.get_angle_difference_local_horizon(),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.ELEVATION_DIFF_LH),
                    los.get_elevation_difference_local_horizon(),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.SLOPE_DIFFERENCE_LH),
                    los.get_los_slope_difference(),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.HORIZON_COUNT),
                    los.get_local_horizon_count(),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.DISTANCE_LH),
                    los.get_local_horizon_distance(),
                )

            elif los_type == NamesConstants.LOS_GLOBAL:
                los = LoSGlobal.from_feature(
                    feature=los_feature,
                    curvature_corrections=curvature_corrections,
                    refraction_coefficient=ref_coeff,
                )

                f.setAttribute(f.fieldNameIndex(FieldNames.VISIBLE), los.is_target_visible())
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.ANGLE_DIFF_GH),
                    los.get_angle_difference_global_horizon(),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.ELEVATION_DIFF_GH),
                    los.get_elevation_difference_global_horizon(),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.HORIZON_COUNT_BEHIND),
                    los.get_horizon_count(),
                )
                f.setAttribute(f.fieldNameIndex(FieldNames.DISTANCE_GH), los.get_horizon_distance())

            elif los_type == NamesConstants.LOS_NO_TARGET:
                los = LoSWithoutTarget.from_feature(
                    feature=los_feature,
                    curvature_corrections=curvature_corrections,
                    refraction_coefficient=ref_coeff,
                )

                f.setAttribute(
                    f.fieldNameIndex(FieldNames.MAXIMAL_VERTICAL_ANGLE),
                    los.get_maximal_vertical_angle(),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.DISTANCE_LH),
                    los.get_max_local_horizon_distance(),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.DISTANCE_GH),
                    los.get_global_horizon_distance(),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.VERTICAL_ANGLE_LH),
                    los.get_max_local_horizon_angle(),
                )

            sink.addFeature(f)

            feedback.setProgress((los_layer_count / feature_count) * 100)

        return {self.OUTPUT_LAYER: dest_id}

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
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
