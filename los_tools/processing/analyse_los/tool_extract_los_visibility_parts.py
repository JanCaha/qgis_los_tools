from qgis.core import (
    Qgis,
    QgsCategorizedSymbolRenderer,
    QgsFeature,
    QgsFeatureIterator,
    QgsField,
    QgsFields,
    QgsLineString,
    QgsMapLayer,
    QgsMultiLineString,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingUtils,
    QgsRendererCategory,
    QgsSymbol,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QMetaType, Qt

from los_tools.classes.classes_los import LoSGlobal, LoSLocal, LoSWithoutTarget
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.constants.textlabels import TextLabels
from los_tools.processing.tools.util_functions import get_los_type
from los_tools.utils import get_doc_file


class ExtractLoSVisibilityPartsAlgorithm(QgsProcessingAlgorithm):
    LOS_LAYER = "LoSLayer"
    OUTPUT_LAYER = "OutputLayer"
    CURVATURE_CORRECTIONS = "CurvatureCorrections"
    REFRACTION_COEFFICIENT = "RefractionCoefficient"

    def initAlgorithm(self, configuration=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.LOS_LAYER, "LoS layer", [QgsProcessing.SourceType.TypeVectorLine])
        )

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_LAYER, "Output LoS parts layer"))

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
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.13,
            )
        )

    def checkParameterValues(self, parameters, context):
        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)

        field_names = los_layer.fields().names()

        if FieldNames.LOS_TYPE not in field_names:
            msg = (
                f"Fields specific for LoS not found in current layer ({FieldNames.LOS_TYPE}). "
                "Cannot extract horizons from this layer."
            )

            return False, msg

        return super().checkParameterValues(parameters, context)

    def postProcessAlgorithm(self, context, feedback):
        output_layer: QgsMapLayer = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)

        symbols = []

        symbol_invisible = QgsSymbol.defaultSymbol(Qgis.GeometryType.Line)
        symbol_invisible.setColor(Qt.GlobalColor.red)
        symbols.append(QgsRendererCategory(False, symbol_invisible, TextLabels.INVISIBLE))

        symbol_visible = QgsSymbol.defaultSymbol(Qgis.GeometryType.Line)
        symbol_visible.setColor(Qt.GlobalColor.green)
        symbols.append(QgsRendererCategory(True, symbol_visible, TextLabels.VISIBLE))

        renderer = QgsCategorizedSymbolRenderer(FieldNames.VISIBLE, symbols)

        output_layer.setRenderer(renderer)

        return {self.OUTPUT_LAYER: self.dest_id}

    def processAlgorithm(self, parameters, context, feedback):
        los_layer: QgsVectorLayer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)

        if los_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.LOS_LAYER))

        curvature_corrections: bool = self.parameterAsBool(parameters, self.CURVATURE_CORRECTIONS, context)
        ref_coeff: float = self.parameterAsDouble(parameters, self.REFRACTION_COEFFICIENT, context)

        field_names = los_layer.fields().names()

        los_type = get_los_type(los_layer, field_names)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.ID_OBSERVER, QMetaType.Type.Int))
        fields.append(QgsField(FieldNames.ID_TARGET, QMetaType.Type.Int))
        fields.append(QgsField(FieldNames.VISIBLE, QMetaType.Type.Bool))

        sink, self.dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_LAYER,
            context,
            fields,
            Qgis.WkbType.MultiLineString25D,
            los_layer.sourceCrs(),
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LAYER))

        feature_count = los_layer.featureCount()

        los_iterator: QgsFeatureIterator = los_layer.getFeatures()

        for feature_number, los_feature in enumerate(los_iterator):
            if feedback.isCanceled():
                break

            if los_type == NamesConstants.LOS_LOCAL:
                los = LoSLocal.from_feature(
                    feature=los_feature,
                    curvature_corrections=curvature_corrections,
                    refraction_coefficient=ref_coeff,
                )

            elif los_type == NamesConstants.LOS_GLOBAL:
                los = LoSGlobal.from_feature(
                    feature=los_feature,
                    curvature_corrections=curvature_corrections,
                    refraction_coefficient=ref_coeff,
                )

            elif los_type == NamesConstants.LOS_NO_TARGET:
                los = LoSWithoutTarget.from_feature(
                    feature=los_feature,
                    curvature_corrections=curvature_corrections,
                    refraction_coefficient=ref_coeff,
                )

            previous_point_visibility = True

            line_string_visible = QgsMultiLineString()
            line_string_invisible = QgsMultiLineString()

            line: QgsLineString = QgsLineString()

            for i in range(0, len(los.points)):
                line.addVertex(los.get_geom_at_index(i))

                if los.visible[i] != previous_point_visibility:
                    if previous_point_visibility:
                        line_string_visible.addGeometry(line)
                    else:
                        line_string_invisible.addGeometry(line)

                    line: QgsLineString = QgsLineString()
                    line.addVertex(los.get_geom_at_index(i))
                    previous_point_visibility = los.visible[i]

                if i == len(los.points) - 1:
                    if los.visible[i]:
                        line_string_visible.addGeometry(line)
                    else:
                        line_string_invisible.addGeometry(line)

            feature_visible = QgsFeature(fields)
            feature_visible.setGeometry(line_string_visible)
            feature_visible.setAttribute(FieldNames.VISIBLE, True)
            feature_visible.setAttribute(FieldNames.ID_OBSERVER, los_feature.attribute(FieldNames.ID_OBSERVER))
            feature_visible.setAttribute(FieldNames.ID_TARGET, los_feature.attribute(FieldNames.ID_TARGET))

            feature_invisible = QgsFeature(fields)
            feature_invisible.setGeometry(line_string_invisible)
            feature_invisible.setAttribute(FieldNames.VISIBLE, False)
            feature_invisible.setAttribute(FieldNames.ID_OBSERVER, los_feature.attribute(FieldNames.ID_OBSERVER))
            feature_invisible.setAttribute(FieldNames.ID_TARGET, los_feature.attribute(FieldNames.ID_TARGET))

            sink.addFeature(feature_visible)
            sink.addFeature(feature_invisible)

            feedback.setProgress((feature_number / feature_count) * 100)

        return {self.OUTPUT_LAYER: self.dest_id}

    def name(self):
        return "extractvisibilitypartslos"

    def displayName(self):
        return "Extract Visible/Invisible Lines from LoS"

    def group(self):
        return "LoS Analysis"

    def groupId(self):
        return "losanalysis"

    def createInstance(self):
        return ExtractLoSVisibilityPartsAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/LoS%20Analysis/tool_extract_visibility_parts/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
