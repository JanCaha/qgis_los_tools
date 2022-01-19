from qgis.core import (QgsField, QgsFeature, QgsWkbTypes, QgsPoint, QgsFields, QgsLineString,
                       QgsProcessingUtils)

from qgis.PyQt.QtCore import QVariant

from los_tools.create_los.tool_create_local_los import CreateLocalLosAlgorithm
from los_tools.tools.util_functions import segmentize_line
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.tools.util_functions import get_doc_file
from los_tools.classes.list_raster import ListOfRasters


class CreateGlobalLosAlgorithm(CreateLocalLosAlgorithm):

    def processAlgorithm(self, parameters, context, feedback):

        list_rasters = ListOfRasters(
            self.parameterAsLayerList(parameters, self.DEM_RASTERS, context))

        observers_layer = self.parameterAsSource(parameters, self.OBSERVER_POINTS_LAYER, context)
        observers_id = self.parameterAsString(parameters, self.OBSERVER_ID_FIELD, context)
        observers_offset = self.parameterAsString(parameters, self.OBSERVER_OFFSET_FIELD, context)

        targets_layer = self.parameterAsSource(parameters, self.TARGET_POINTS_LAYER, context)
        targets_id = self.parameterAsString(parameters, self.TARGET_ID_FIELD, context)
        targets_offset = self.parameterAsString(parameters, self.TARGET_OFFSET_FIELD, context)

        sampling_distance = self.parameterAsDouble(parameters, self.LINE_DENSITY, context)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.LOS_TYPE, QVariant.String))
        fields.append(QgsField(FieldNames.ID_OBSERVER, QVariant.Int))
        fields.append(QgsField(FieldNames.ID_TARGET, QVariant.Int))
        fields.append(QgsField(FieldNames.OBSERVER_OFFSET, QVariant.Double))
        fields.append(QgsField(FieldNames.TARGET_OFFSET, QVariant.Double))
        fields.append(QgsField(FieldNames.TARGET_X, QVariant.Double))
        fields.append(QgsField(FieldNames.TARGET_Y, QVariant.Double))

        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT_LAYER, context,
                                             fields, QgsWkbTypes.LineString25D,
                                             observers_layer.sourceCrs())

        feature_count = observers_layer.featureCount() * targets_layer.featureCount()

        observers_iterator = observers_layer.getFeatures()

        max_length_extension = list_rasters.maximal_diagonal_size()

        for observer_count, observer_feature in enumerate(observers_iterator):

            if feedback.isCanceled():
                break

            targets_iterators = targets_layer.getFeatures()

            for target_count, target_feature in enumerate(targets_iterators):

                line = QgsLineString([
                    QgsPoint(observer_feature.geometry().asPoint()),
                    QgsPoint(target_feature.geometry().asPoint())
                ])

                line_temp = line.clone()
                line_temp.extend(0, max_length_extension)

                line = QgsLineString([
                    QgsPoint(observer_feature.geometry().asPoint()),
                    QgsPoint(target_feature.geometry().asPoint()),
                    line_temp.endPoint()
                ])

                line = segmentize_line(line, segment_length=sampling_distance)

                line = list_rasters.add_z_values(line.points())

                f = QgsFeature(fields)
                f.setGeometry(line)
                f.setAttribute(f.fieldNameIndex(FieldNames.LOS_TYPE), NamesConstants.LOS_GLOBAL)
                f.setAttribute(f.fieldNameIndex(FieldNames.ID_OBSERVER),
                               int(observer_feature.attribute(observers_id)))
                f.setAttribute(f.fieldNameIndex(FieldNames.ID_TARGET),
                               int(target_feature.attribute(targets_id)))
                f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_OFFSET),
                               float(observer_feature.attribute(observers_offset)))
                f.setAttribute(f.fieldNameIndex(FieldNames.TARGET_OFFSET),
                               float(target_feature.attribute(targets_offset)))
                f.setAttribute(f.fieldNameIndex(FieldNames.TARGET_X),
                               float(target_feature.geometry().asPoint().x()))
                f.setAttribute(f.fieldNameIndex(FieldNames.TARGET_Y),
                               float(target_feature.geometry().asPoint().y()))

                sink.addFeature(f)

                feedback.setProgress(
                    ((observer_count + 1 * target_count + 1 + target_count) / feature_count) * 100)

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
