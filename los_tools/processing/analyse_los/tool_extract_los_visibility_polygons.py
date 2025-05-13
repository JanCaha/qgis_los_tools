from qgis.analysis import QgsGeometrySnapper, QgsInternalGeometrySnapper
from qgis.core import (
    Qgis,
    QgsCategorizedSymbolRenderer,
    QgsFeature,
    QgsFeatureIterator,
    QgsField,
    QgsFields,
    QgsLineString,
    QgsMapLayer,
    QgsMultiPolygon,
    QgsPointXY,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingUtils,
    QgsRendererCategory,
    QgsSymbol,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import Qt

from los_tools.classes.classes_los import LoSWithoutTarget
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.constants.textlabels import TextLabels
from los_tools.processing.tools.util_functions import get_los_type, line_to_polygon
from los_tools.utils import COLUMN_TYPE, get_doc_file


class ExtractLoSVisibilityPolygonsAlgorithm(QgsProcessingAlgorithm):
    LOS_LAYER = "LoSLayer"
    OUTPUT_LAYER = "OutputLayer"
    CURVATURE_CORRECTIONS = "CurvatureCorrections"
    REFRACTION_COEFFICIENT = "RefractionCoefficient"

    def initAlgorithm(self, configuration=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.LOS_LAYER, "LoS layer", [QgsProcessing.TypeVectorLine])
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
                type=QgsProcessingParameterNumber.Double,
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

        symbol_invisible = QgsSymbol.defaultSymbol(Qgis.GeometryType.Polygon)
        symbol_invisible.setColor(Qt.red)

        symbol_invisible.symbolLayer(0).setStrokeStyle(Qt.PenStyle(Qt.NoPen))
        symbols.append(QgsRendererCategory(False, symbol_invisible, TextLabels.INVISIBLE))

        symbol_visible = QgsSymbol.defaultSymbol(Qgis.GeometryType.Polygon)
        symbol_visible.setColor(Qt.green)
        symbol_visible.symbolLayer(0).setStrokeStyle(Qt.PenStyle(Qt.NoPen))
        symbols.append(QgsRendererCategory(True, symbol_visible, TextLabels.VISIBLE))

        renderer = QgsCategorizedSymbolRenderer(FieldNames.VISIBLE, symbols)

        output_layer.setRenderer(renderer)

        return {self.OUTPUT_LAYER: self.dest_id}

    def processAlgorithm(self, parameters, context, feedback: QgsProcessingFeedback):
        los_layer: QgsVectorLayer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)

        if los_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.LOS_LAYER))

        curvature_corrections: bool = self.parameterAsBool(parameters, self.CURVATURE_CORRECTIONS, context)
        ref_coeff: float = self.parameterAsDouble(parameters, self.REFRACTION_COEFFICIENT, context)

        field_names = los_layer.fields().names()

        los_type = get_los_type(los_layer, field_names)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.ID_OBSERVER, COLUMN_TYPE.Int))
        fields.append(QgsField(FieldNames.ID_TARGET, COLUMN_TYPE.Int))
        fields.append(QgsField(FieldNames.VISIBLE, COLUMN_TYPE.Bool))

        sink, self.dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_LAYER,
            context,
            fields,
            Qgis.WkbType.MultiPolygon,
            los_layer.sourceCrs(),
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LAYER))

        feature_count = los_layer.featureCount()

        los_iterator: QgsFeatureIterator = los_layer.getFeatures()

        geometry_snapper = QgsInternalGeometrySnapper(0.000001, QgsGeometrySnapper.EndPointToEndPoint)

        for feature_number, los_feature in enumerate(los_iterator):
            if feedback.isCanceled():
                break

            if los_type == NamesConstants.LOS_NO_TARGET:
                los = LoSWithoutTarget(
                    los_feature.geometry(),
                    observer_offset=los_feature.attribute(FieldNames.OBSERVER_OFFSET),
                    use_curvature_corrections=curvature_corrections,
                    refraction_coefficient=ref_coeff,
                )

            previous_point_visibility = True

            polygon_multi_visible = QgsMultiPolygon()
            polygon_multi_invisible = QgsMultiPolygon()

            observer_point = QgsPointXY(
                los_feature.attribute(FieldNames.OBSERVER_X),
                los_feature.attribute(FieldNames.OBSERVER_Y),
            )

            angle_width = los_feature.attribute(FieldNames.ANGLE_STEP)

            line: QgsLineString = QgsLineString()

            for i in range(0, len(los.points)):
                line.addVertex(los.get_geom_at_index(i))

                if los.visible[i] != previous_point_visibility:
                    polygon = line_to_polygon(line, observer_point, angle_width)

                    if polygon.isValid() and 1 < line.vertexCount():
                        if previous_point_visibility:
                            polygon_multi_visible.addGeometry(line_to_polygon(line, observer_point, angle_width))
                        else:
                            polygon_multi_invisible.addGeometry(line_to_polygon(line, observer_point, angle_width))

                    line = QgsLineString()
                    line.addVertex(los.get_geom_at_index(i))
                    previous_point_visibility = los.visible[i]

                if i == len(los.points) - 1:
                    polygon = line_to_polygon(line, observer_point, angle_width)

                    if polygon.isValid() and 1 < line.vertexCount():
                        if los.visible[i]:
                            polygon_multi_visible.addGeometry(line_to_polygon(line, observer_point, angle_width))
                        else:
                            polygon_multi_invisible.addGeometry(line_to_polygon(line, observer_point, angle_width))

            feature_visible = QgsFeature(fields)
            feature_visible.setGeometry(polygon_multi_visible)
            feature_visible.setAttribute(FieldNames.VISIBLE, True)
            feature_visible.setAttribute(FieldNames.ID_OBSERVER, los_feature.attribute(FieldNames.ID_OBSERVER))
            feature_visible.setAttribute(FieldNames.ID_TARGET, los_feature.attribute(FieldNames.ID_TARGET))

            feature_invisible = QgsFeature(fields)
            feature_invisible.setGeometry(polygon_multi_invisible)
            feature_invisible.setAttribute(FieldNames.VISIBLE, False)
            feature_invisible.setAttribute(FieldNames.ID_OBSERVER, los_feature.attribute(FieldNames.ID_OBSERVER))
            feature_invisible.setAttribute(FieldNames.ID_TARGET, los_feature.attribute(FieldNames.ID_TARGET))

            geom_visible = geometry_snapper.snapFeature(feature_visible)
            feature_visible.setGeometry(geom_visible)

            geom_invisible = geometry_snapper.snapFeature(feature_invisible)
            feature_invisible.setGeometry(geom_invisible)

            sink.addFeature(feature_visible)
            sink.addFeature(feature_invisible)

            feedback.setProgress((feature_number / feature_count) * 100)

        return {self.OUTPUT_LAYER: self.dest_id}

    def name(self):
        return "extractvisibilitypolygonslos"

    def displayName(self):
        return "Extract Visible/Invisible Polygons from LoS"

    def group(self):
        return "LoS Analysis"

    def groupId(self):
        return "losanalysis"

    def createInstance(self):
        return ExtractLoSVisibilityPolygonsAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/LoS%20Analysis/tool_extract_visibility_polygons/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
