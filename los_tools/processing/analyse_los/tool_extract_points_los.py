from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSource, QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterBoolean, QgsField, QgsFeature, QgsWkbTypes, QgsFields,
                       QgsVectorLayer, QgsFeatureIterator, QgsProcessingUtils, QgsMapLayer,
                       QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer,
                       QgsProcessingException)

from qgis.PyQt.QtCore import QVariant, Qt
from los_tools.constants.field_names import FieldNames
from los_tools.constants.textlabels import TextLabels
from los_tools.classes.classes_los import LoSLocal, LoSGlobal, LoSWithoutTarget
from los_tools.processing.tools.util_functions import get_los_type
from los_tools.utils import get_doc_file
from los_tools.constants.names_constants import NamesConstants


class ExtractPointsLoSAlgorithm(QgsProcessingAlgorithm):

    LOS_LAYER = "LoSLayer"
    OUTPUT_LAYER = "OutputLayer"
    CURVATURE_CORRECTIONS = "CurvatureCorrections"
    REFRACTION_COEFFICIENT = "RefractionCoefficient"
    ONLY_VISIBLE = "OnlyVisiblePoints"
    EXTENDED_ATTRIBUTES = "ExtendedAttributes"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.LOS_LAYER, "LoS layer",
                                                [QgsProcessing.TypeVectorLine]))

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

        self.addParameter(
            QgsProcessingParameterBoolean(self.ONLY_VISIBLE,
                                          "Export only visible points",
                                          defaultValue=False))

        self.addParameter(
            QgsProcessingParameterBoolean(self.EXTENDED_ATTRIBUTES,
                                          "Calculate extended attributes?",
                                          defaultValue=False))

    def checkParameterValues(self, parameters, context):

        los_layer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)

        field_names = los_layer.fields().names()

        if FieldNames.LOS_TYPE not in field_names:

            msg = "Fields specific for LoS not found in current layer ({0}). " \
                  "Cannot extract horizons from this layer.".format(FieldNames.LOS_TYPE)

            return False, msg

        return super().checkParameterValues(parameters, context)

    def postProcessAlgorithm(self, context, feedback):

        output_layer: QgsMapLayer = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)

        symbols = []

        symbol_invisible = QgsSymbol.defaultSymbol(QgsWkbTypes.PointGeometry)
        symbol_invisible.setColor(Qt.red)
        symbols.append(QgsRendererCategory(False, symbol_invisible, TextLabels.INVISIBLE))

        symbol_visible = QgsSymbol.defaultSymbol(QgsWkbTypes.PointGeometry)
        symbol_visible.setColor(Qt.green)
        symbols.append(QgsRendererCategory(True, symbol_visible, TextLabels.VISIBLE))

        renderer = QgsCategorizedSymbolRenderer(FieldNames.VISIBLE, symbols)

        output_layer.setRenderer(renderer)
        output_layer.triggerRepaint()

        return {self.OUTPUT_LAYER: self.dest_id}

    def processAlgorithm(self, parameters, context, feedback):

        los_layer: QgsVectorLayer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER,
                                                                context)

        if los_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.LOS_LAYER))

        curvature_corrections: bool = self.parameterAsBool(parameters, self.CURVATURE_CORRECTIONS,
                                                           context)
        ref_coeff: float = self.parameterAsDouble(parameters, self.REFRACTION_COEFFICIENT, context)
        only_visible: bool = self.parameterAsBool(parameters, self.ONLY_VISIBLE, context)
        extended_attributes: bool = self.parameterAsBool(parameters, self.EXTENDED_ATTRIBUTES,
                                                         context)

        field_names = los_layer.fields().names()

        los_type = get_los_type(los_layer, field_names)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.ID_OBSERVER, QVariant.Int))
        fields.append(QgsField(FieldNames.ID_TARGET, QVariant.Int))
        fields.append(QgsField(FieldNames.VISIBLE, QVariant.Bool))

        if extended_attributes:

            fields.append(QgsField(FieldNames.ELEVATION_DIFF_LH, QVariant.Double))
            fields.append(QgsField(FieldNames.ANGLE_DIFF_LH, QVariant.Double))

            if los_type == NamesConstants.LOS_GLOBAL or los_type == NamesConstants.LOS_NO_TARGET:

                fields.append(QgsField(FieldNames.ELEVATION_DIFF_GH, QVariant.Double))
                fields.append(QgsField(FieldNames.ANGLE_DIFF_GH, QVariant.Double))

        sink, self.dest_id = self.parameterAsSink(parameters, self.OUTPUT_LAYER, context, fields,
                                                  QgsWkbTypes.Point25D, los_layer.sourceCrs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LAYER))

        feature_count = los_layer.featureCount()

        los_iterator: QgsFeatureIterator = los_layer.getFeatures()

        for feature_number, los_feature in enumerate(los_iterator):

            if feedback.isCanceled():
                break

            if los_type == NamesConstants.LOS_LOCAL:

                los = LoSLocal.from_feature(feature=los_feature,
                                            curvature_corrections=curvature_corrections,
                                            refraction_coefficient=ref_coeff)

            elif los_type == NamesConstants.LOS_GLOBAL:

                los = LoSGlobal.from_feature(feature=los_feature,
                                             curvature_corrections=curvature_corrections,
                                             refraction_coefficient=ref_coeff)

            elif los_type == NamesConstants.LOS_NO_TARGET:

                los = LoSWithoutTarget.from_feature(feature=los_feature,
                                                    curvature_corrections=curvature_corrections,
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
                    f.setAttribute(f.fieldNameIndex(FieldNames.VISIBLE), los.visible[i])

                    if extended_attributes:

                        f.setAttribute(f.fieldNameIndex(FieldNames.ELEVATION_DIFF_LH),
                                       los.get_elevation_difference_horizon_at_point(i))
                        f.setAttribute(f.fieldNameIndex(FieldNames.ANGLE_DIFF_LH),
                                       los.get_angle_difference_horizon_at_point(i))

                        if los_type == NamesConstants.LOS_GLOBAL or los_type == NamesConstants.LOS_NO_TARGET:

                            f.setAttribute(f.fieldNameIndex(FieldNames.ELEVATION_DIFF_GH),
                                           los.get_elevation_difference_global_horizon_at_point(i))
                            f.setAttribute(f.fieldNameIndex(FieldNames.ANGLE_DIFF_GH),
                                           los.get_angle_difference_global_horizon_at_point(i))

                    sink.addFeature(f)

            feedback.setProgress((feature_number / feature_count) * 100)

        return {self.OUTPUT_LAYER: self.dest_id}

    def name(self):
        return "extractpointslos"

    def displayName(self):
        return "Extract Visible/Invisible Points from LoS"

    def group(self):
        return "LoS Analysis"

    def groupId(self):
        return "losanalysis"

    def createInstance(self):
        return ExtractPointsLoSAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/LoS%20Points/tool_extract_points_los/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
