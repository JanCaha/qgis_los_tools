from qgis.core import (
    Qgis,
    QgsFeature,
    QgsGeometry,
    QgsPoint,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterDistance,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingUtils,
)

from los_tools.classes.list_raster import ListOfRasters
from los_tools.constants.field_names import FieldNames
from los_tools.constants.fields import Fields
from los_tools.constants.names_constants import NamesConstants
from los_tools.processing.tools.util_functions import segmentize_los_line
from los_tools.utils import get_doc_file


class CreateLocalLosAlgorithm(QgsProcessingAlgorithm):
    OBSERVER_POINTS_LAYER = "ObserverPoints"
    OBSERVER_ID_FIELD = "ObserverIdField"
    OBSERVER_OFFSET_FIELD = "ObserverOffset"
    TARGET_POINTS_LAYER = "TargetPoints"
    TARGET_ID_FIELD = "TargetIdField"
    TARGET_OFFSET_FIELD = "TargetOffset"
    OUTPUT_LAYER = "OutputLayer"
    LINE_DENSITY = "LineDensity"
    DEM_RASTERS = "DemRasters"

    def initAlgorithm(self, configuration=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(self.DEM_RASTERS, "Raster DEM Layers", QgsProcessing.TypeRaster)
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.OBSERVER_POINTS_LAYER,
                "Observers point layer",
                [QgsProcessing.TypeVectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.OBSERVER_ID_FIELD,
                "Observer ID field",
                parentLayerParameterName=self.OBSERVER_POINTS_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.OBSERVER_OFFSET_FIELD,
                "Observer offset field",
                parentLayerParameterName=self.OBSERVER_POINTS_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TARGET_POINTS_LAYER,
                "Targets point layer",
                [QgsProcessing.TypeVectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.TARGET_ID_FIELD,
                "Target ID field",
                parentLayerParameterName=self.TARGET_POINTS_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.TARGET_OFFSET_FIELD,
                "Target offset field",
                parentLayerParameterName=self.TARGET_POINTS_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterDistance(
                self.LINE_DENSITY,
                "LoS sampling distance",
                parentParameterName=self.OBSERVER_POINTS_LAYER,
                defaultValue=1,
                minValue=0.01,
                maxValue=1000.0,
                optional=False,
            )
        )

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_LAYER, "Output layer"))

    def checkParameterValues(self, parameters, context):
        observers_layer = self.parameterAsSource(parameters, self.OBSERVER_POINTS_LAYER, context)
        targets_layer = self.parameterAsSource(parameters, self.TARGET_POINTS_LAYER, context)

        if observers_layer.sourceCrs().isGeographic():
            msg = "`Observers point layer` crs must be projected. " "Right now it is `geographic`."

            return False, msg

        if not observers_layer.sourceCrs() == targets_layer.sourceCrs():
            msg = "`Observers point layer` and `Targets point layer` crs must be equal. " "Right now they are not."

            return False, msg

        rasters = self.parameterAsLayerList(parameters, self.DEM_RASTERS, context)

        correct, msg = ListOfRasters.validate_bands(rasters)

        if not correct:
            return correct, msg

        correct, msg = ListOfRasters.validate_crs(rasters, crs=observers_layer.sourceCrs())

        if not correct:
            return correct, msg

        correct, msg = ListOfRasters.validate_ordering(rasters)

        if not correct:
            return correct, msg

        correct, msg = ListOfRasters.validate_square_cell_size(rasters)

        if not correct:
            return correct, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):
        list_rasters = ListOfRasters(self.parameterAsLayerList(parameters, self.DEM_RASTERS, context))

        observers_layer = self.parameterAsSource(parameters, self.OBSERVER_POINTS_LAYER, context)

        if observers_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.OBSERVER_POINTS_LAYER))

        observers_id = self.parameterAsString(parameters, self.OBSERVER_ID_FIELD, context)
        observers_offset = self.parameterAsString(parameters, self.OBSERVER_OFFSET_FIELD, context)

        targets_layer = self.parameterAsSource(parameters, self.TARGET_POINTS_LAYER, context)

        if targets_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.TARGET_POINTS_LAYER))

        targets_id = self.parameterAsString(parameters, self.TARGET_ID_FIELD, context)
        targets_offset = self.parameterAsString(parameters, self.TARGET_OFFSET_FIELD, context)

        sampling_distance = self.parameterAsDouble(parameters, self.LINE_DENSITY, context)

        fields = Fields.los_local_fields

        sink, dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_LAYER,
            context,
            fields,
            Qgis.WkbType.LineString25D,
            observers_layer.sourceCrs(),
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LAYER))

        feature_count = observers_layer.featureCount() * targets_layer.featureCount()

        observers_iterator = observers_layer.getFeatures()

        for observer_count, observer_feature in enumerate(observers_iterator):
            if feedback.isCanceled():
                break

            targets_iterators = targets_layer.getFeatures()

            for target_count, target_feature in enumerate(targets_iterators):
                line = QgsGeometry.fromPolyline(
                    [
                        QgsPoint(observer_feature.geometry().asPoint()),
                        QgsPoint(target_feature.geometry().asPoint()),
                    ]
                )

                line = segmentize_los_line(line, segment_length=sampling_distance)

                line = list_rasters.add_z_values(line.points())

                f = QgsFeature(fields)
                f.setGeometry(line)
                f.setAttribute(f.fieldNameIndex(FieldNames.LOS_TYPE), NamesConstants.LOS_LOCAL)
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.ID_OBSERVER),
                    int(observer_feature.attribute(observers_id)),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.ID_TARGET),
                    int(target_feature.attribute(targets_id)),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.OBSERVER_OFFSET),
                    float(observer_feature.attribute(observers_offset)),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.TARGET_OFFSET),
                    float(target_feature.attribute(targets_offset)),
                )

                sink.addFeature(f)

                feedback.setProgress(((observer_count + 1 * target_count + 1 + target_count) / feature_count) * 100)

        return {self.OUTPUT_LAYER: dest_id}

    def name(self):
        return "locallos"

    def displayName(self):
        return "Create Local LoS"

    def group(self):
        return "LoS Creation"

    def groupId(self):
        return "loscreate"

    def createInstance(self):
        return CreateLocalLosAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/LoS%20Creation/tool_create_local_los/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
