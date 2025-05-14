from qgis.core import Qgis, QgsFeature, QgsGeometry, QgsLineString, QgsPoint, QgsProcessingException, QgsProcessingUtils

from los_tools.classes.list_raster import ListOfRasters
from los_tools.constants.field_names import FieldNames
from los_tools.constants.fields import Fields
from los_tools.constants.names_constants import NamesConstants
from los_tools.processing.create_los.tool_create_local_los import CreateLocalLosAlgorithm
from los_tools.processing.tools.util_functions import segmentize_los_line
from los_tools.utils import get_doc_file


class CreateGlobalLosAlgorithm(CreateLocalLosAlgorithm):
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

        fields = Fields.los_global_fields

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

        max_length_extension = list_rasters.maximal_diagonal_size()

        for observer_count, observer_feature in enumerate(observers_iterator):
            if feedback.isCanceled():
                break

            targets_iterators = targets_layer.getFeatures()

            for target_count, target_feature in enumerate(targets_iterators):
                line = QgsLineString(
                    [
                        QgsPoint(observer_feature.geometry().asPoint()),
                        QgsPoint(target_feature.geometry().asPoint()),
                    ]
                )

                line_temp = line.clone()
                line_temp.extend(0, max_length_extension)

                line = QgsGeometry.fromPolyline(
                    [
                        QgsPoint(observer_feature.geometry().asPoint()),
                        QgsPoint(target_feature.geometry().asPoint()),
                        line_temp.endPoint(),
                    ]
                )

                line = segmentize_los_line(line, segment_length=sampling_distance)

                line = list_rasters.add_z_values(line.points())

                f = QgsFeature(fields)
                f.setGeometry(line)
                f.setAttribute(f.fieldNameIndex(FieldNames.LOS_TYPE), NamesConstants.LOS_GLOBAL)
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
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.TARGET_X),
                    float(target_feature.geometry().asPoint().x()),
                )
                f.setAttribute(
                    f.fieldNameIndex(FieldNames.TARGET_Y),
                    float(target_feature.geometry().asPoint().y()),
                )

                sink.addFeature(f)

                feedback.setProgress(((observer_count + 1 * target_count + 1 + target_count) / feature_count) * 100)

        return {self.OUTPUT_LAYER: dest_id}

    def name(self):
        return "globallos"

    def displayName(self):
        return "Create Global LoS"

    def createInstance(self):
        return CreateGlobalLosAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/LoS%20Creation/tool_create_global_los/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
