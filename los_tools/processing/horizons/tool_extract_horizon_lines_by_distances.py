import typing

from qgis.core import (
    QgsColorRamp,
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsGraduatedSymbolRenderer,
    QgsLineString,
    QgsMapLayer,
    QgsPoint,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterMatrix,
    QgsProcessingParameterNumber,
    QgsProcessingUtils,
    QgsStyle,
    QgsSymbol,
    QgsVectorLayer,
    QgsWkbTypes,
)

from los_tools.classes.classes_los import LoSWithoutTarget
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.processing.tools.util_functions import get_los_type
from los_tools.utils import COLUMN_TYPE, COLUMN_TYPE_STRING, get_doc_file


class ExtractHorizonLinesByDistanceAlgorithm(QgsProcessingAlgorithm):
    LOS_LAYER = "LoSLayer"
    OUTPUT_LAYER = "OutputLayer"
    CURVATURE_CORRECTIONS = "CurvatureCorrections"
    REFRACTION_COEFFICIENT = "RefractionCoefficient"
    DISTANCES = "Distances"

    horizons_types = [NamesConstants.HORIZON_MAX_LOCAL, NamesConstants.HORIZON_GLOBAL]

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.LOS_LAYER, "LoS layer", [QgsProcessing.TypeVectorLine])
        )

        self.addParameter(
            QgsProcessingParameterMatrix(
                self.DISTANCES,
                "Distance limits for horizon lines",
                numberRows=2,
                headers=["Distance"],
                defaultValue=[500, 1000],
            )
        )

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_LAYER, "Output layer"))

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
                "Fields specific for LoS not found in current layer ({0}). "
                "Cannot extract horizon lines from this layer.".format(FieldNames.LOS_TYPE)
            )

            return False, msg

        los_type = get_los_type(los_layer, field_names)

        if los_type != NamesConstants.LOS_NO_TARGET:
            msg = "LoS must be of type `{0}` to extract horizon lines but type `{1}` found.".format(
                NamesConstants.LOS_NO_TARGET, los_type
            )

            return False, msg

        distances = self.parameterAsMatrix(parameters, self.DISTANCES, context)

        if len(distances) < 1:
            msg = f"Length of distances must be at least 1. It is {len(distances)}."

            return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        los_layer: QgsVectorLayer = self.parameterAsVectorLayer(parameters, self.LOS_LAYER, context)

        if los_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.LOS_LAYER))

        self.distances_matrix = self.parameterAsMatrix(parameters, self.DISTANCES, context)

        distances: typing.List[float] = []

        for distance in self.distances_matrix:
            try:
                distances.append(float(distance))
            except ValueError:
                raise QgsProcessingException(f"Cannot convert value `{distance}` to float number.")

        curvature_corrections = self.parameterAsBool(parameters, self.CURVATURE_CORRECTIONS, context)
        ref_coeff = self.parameterAsDouble(parameters, self.REFRACTION_COEFFICIENT, context)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.HORIZON_DISTANCE, COLUMN_TYPE.Double))
        fields.append(QgsField(FieldNames.ID_OBSERVER, COLUMN_TYPE.Int))
        fields.append(QgsField(FieldNames.OBSERVER_X, COLUMN_TYPE.Double))
        fields.append(QgsField(FieldNames.OBSERVER_Y, COLUMN_TYPE.Double))

        horizon_distance_field_index = fields.indexFromName(FieldNames.HORIZON_DISTANCE)
        id_observer_field_index = fields.indexFromName(FieldNames.ID_OBSERVER)
        observer_x_field_index = fields.indexFromName(FieldNames.OBSERVER_X)
        observer_y_field_index = fields.indexFromName(FieldNames.OBSERVER_Y)

        sink, self.dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_LAYER,
            context,
            fields,
            QgsWkbTypes.LineStringZM,
            los_layer.sourceCrs(),
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LAYER))

        id_values = list(los_layer.uniqueValues(los_layer.fields().indexFromName(FieldNames.ID_OBSERVER)))

        total = 100 / (los_layer.featureCount()) if los_layer.featureCount() else 0

        i = 0

        for id_value in id_values:
            request = QgsFeatureRequest()
            request.setFilterExpression("{} = '{}'".format(FieldNames.ID_OBSERVER, id_value))
            order_by_clause = QgsFeatureRequest.OrderByClause(FieldNames.AZIMUTH, ascending=True)
            request.setOrderBy(QgsFeatureRequest.OrderBy([order_by_clause]))

            features = los_layer.getFeatures(request)

            line_points: typing.Dict[float, typing.List[QgsPoint]] = {}
            values: typing.Dict[float, typing.List[float]] = {}

            for distance in distances:
                line_points[distance] = []
                values[distance] = []

            for los_feature in features:
                if feedback.isCanceled():
                    break

                full_los = LoSWithoutTarget(
                    los_feature.geometry(),
                    observer_offset=los_feature.attribute(FieldNames.OBSERVER_OFFSET),
                    use_curvature_corrections=curvature_corrections,
                    refraction_coefficient=ref_coeff,
                )

                for distance in distances:
                    los_limited = LoSWithoutTarget.from_another(full_los, distance_limit=distance)

                    line_points[distance].append(los_limited.get_global_horizon())
                    values[distance].append(los_limited.get_global_horizon_angle())

                i += 1

                feedback.setProgress(int(i * total))

            for distance in distances:

                points = line_points[distance]
                m_values = values[distance]

                if 1 < len(points):
                    line = QgsLineString(points)
                    line.addMValue()

                    for i in range(0, line.numPoints()):
                        line.setMAt(i, m_values[i])

                    f = QgsFeature(fields)
                    f.setGeometry(line)
                    f.setAttribute(id_observer_field_index, id_value)
                    f.setAttribute(
                        observer_x_field_index,
                        los_feature.attribute(FieldNames.OBSERVER_X),
                    )
                    f.setAttribute(
                        observer_y_field_index,
                        los_feature.attribute(FieldNames.OBSERVER_Y),
                    )
                    f.setAttribute(horizon_distance_field_index, distance)

                    sink.addFeature(f)

        return {self.OUTPUT_LAYER: self.dest_id}

    def name(self):
        return "extracthorizonlinesbydistace"

    def displayName(self):
        return "Extract Horizon Lines By Distance"

    def group(self):
        return "Horizons"

    def groupId(self):
        return "horizons"

    def createInstance(self):
        return ExtractHorizonLinesByDistanceAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/Horizons/tool_extract_horizon_lines_by_distances/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)

    def postProcessAlgorithm(self, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        output_layer: QgsMapLayer = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)

        ramp: QgsColorRamp = QgsStyle.defaultStyle().colorRamp("Viridis")
        ramp.invert()

        renderer = QgsGraduatedSymbolRenderer.createRenderer(
            output_layer,
            FieldNames.HORIZON_DISTANCE,
            len(self.distances_matrix),
            QgsGraduatedSymbolRenderer.Mode.EqualInterval,
            QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry),
            ramp,
        )

        output_layer.setRenderer(renderer)

        return {self.OUTPUT_LAYER: self.dest_id}
