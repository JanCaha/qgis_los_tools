from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField, QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterMultipleLayers, QgsField, QgsFeature, QgsWkbTypes,
                       QgsPoint, QgsFields, QgsLineString, QgsProcessingFeedback)

from qgis.PyQt.QtCore import QVariant
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.classes.list_raster import ListOfRasters
from los_tools.classes.sampling_distance_matrix import SamplingDistanceMatrix


class CreateNoTargetLosAlgorithmV2(QgsProcessingAlgorithm):

    OBSERVER_POINTS_LAYER = "ObserverPoints"
    OBSERVER_ID_FIELD = "ObserverIdField"
    OBSERVER_OFFSET_FIELD = "ObserverOffset"
    TARGET_POINTS_LAYER = "TargetPoints"
    TARGET_ID_FIELD = "TargetIdField"
    TARGET_DEFINITION_ID_FIELD = "TargetDefinitionIdField"
    OUTPUT_LAYER = "OutputLayer"

    DEM_RASTERS = "DemRasters"
    LINE_SETTINGS_TABLE = "LineSettingsTable"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterMultipleLayers(self.DEM_RASTERS, "Raster DEM Layers",
                                                 QgsProcessing.TypeRaster))

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.LINE_SETTINGS_TABLE,
                                                "Sampling distance - distance table",
                                                [QgsProcessing.TypeVector]))

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.OBSERVER_POINTS_LAYER,
                                                "Observers point layer",
                                                [QgsProcessing.TypeVectorPoint]))

        self.addParameter(
            QgsProcessingParameterField(self.OBSERVER_ID_FIELD,
                                        "Observer ID field",
                                        parentLayerParameterName=self.OBSERVER_POINTS_LAYER,
                                        type=QgsProcessingParameterField.Numeric,
                                        optional=False))

        self.addParameter(
            QgsProcessingParameterField(self.OBSERVER_OFFSET_FIELD,
                                        "Observer offset field",
                                        parentLayerParameterName=self.OBSERVER_POINTS_LAYER,
                                        type=QgsProcessingParameterField.Numeric,
                                        optional=False))

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.TARGET_POINTS_LAYER, "Targets point layer",
                                                [QgsProcessing.TypeVectorPoint]))

        self.addParameter(
            QgsProcessingParameterField(self.TARGET_ID_FIELD,
                                        "Target ID field",
                                        parentLayerParameterName=self.TARGET_POINTS_LAYER,
                                        type=QgsProcessingParameterField.Numeric,
                                        optional=False))

        self.addParameter(
            QgsProcessingParameterField(self.TARGET_DEFINITION_ID_FIELD,
                                        "Target and Observer agreement ID field",
                                        parentLayerParameterName=self.TARGET_POINTS_LAYER,
                                        type=QgsProcessingParameterField.Numeric,
                                        optional=False))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_LAYER, "Output layer"))

    def checkParameterValues(self, parameters, context):

        observers_layer = self.parameterAsSource(parameters, self.OBSERVER_POINTS_LAYER, context)
        targets_layer = self.parameterAsSource(parameters, self.TARGET_POINTS_LAYER, context)

        if observers_layer.sourceCrs().isGeographic():
            msg = "`Observers point layer` crs must be projected. " \
                  "Right now it is `geographic`."

            return False, msg

        if not observers_layer.sourceCrs() == targets_layer.sourceCrs():
            msg = "`Observers point layer` and `Targets point layer` crs must be equal. " \
                  "Right now they are not."

            return False, msg

        list_rasters = ListOfRasters(
            self.parameterAsLayerList(parameters, self.DEM_RASTERS, context))

        correct, msg = list_rasters.validate_bands()

        if not correct:
            return correct, msg

        correct, msg = list_rasters.validate_crs(crs=observers_layer.sourceCrs())

        if not correct:
            return correct, msg

        line_settings_table = self.parameterAsVectorLayer(parameters, self.LINE_SETTINGS_TABLE,
                                                          context)

        validation, msg = SamplingDistanceMatrix.validate_table(line_settings_table)

        if not validation:
            return validation, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback: QgsProcessingFeedback):

        observers_layer = self.parameterAsSource(parameters, self.OBSERVER_POINTS_LAYER, context)
        observers_id = self.parameterAsString(parameters, self.OBSERVER_ID_FIELD, context)
        observers_offset = self.parameterAsString(parameters, self.OBSERVER_OFFSET_FIELD, context)
        targets_layer = self.parameterAsSource(parameters, self.TARGET_POINTS_LAYER, context)
        targets_id = self.parameterAsString(parameters, self.TARGET_ID_FIELD, context)
        target_definition_id_field = self.parameterAsString(parameters,
                                                            self.TARGET_DEFINITION_ID_FIELD,
                                                            context)

        list_rasters = ListOfRasters(
            self.parameterAsLayerList(parameters, self.DEM_RASTERS, context))

        line_settings_table = self.parameterAsVectorLayer(parameters, self.LINE_SETTINGS_TABLE,
                                                          context)

        distance_matrix = SamplingDistanceMatrix(line_settings_table)

        fields = QgsFields()
        fields.append(QgsField(FieldNames.LOS_TYPE, QVariant.String))
        fields.append(QgsField(FieldNames.ID_OBSERVER, QVariant.Int))
        fields.append(QgsField(FieldNames.ID_TARGET, QVariant.Int))
        fields.append(QgsField(FieldNames.OBSERVER_OFFSET, QVariant.Double))
        fields.append(QgsField(FieldNames.AZIMUTH, QVariant.Double))
        fields.append(QgsField(FieldNames.OBSERVER_X, QVariant.Double))
        fields.append(QgsField(FieldNames.OBSERVER_Y, QVariant.Double))
        fields.append(QgsField(FieldNames.ANGLE_STEP, QVariant.Double))

        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT_LAYER, context,
                                             fields, QgsWkbTypes.LineString25D,
                                             observers_layer.sourceCrs())

        feature_count = targets_layer.featureCount()

        observers_iterator = observers_layer.getFeatures()

        distance_matrix.replace_minus_one_with_value(list_rasters.maximal_diagonal_size())

        for observer_feature in observers_iterator:

            targets_iterators = targets_layer.getFeatures()

            for target_count, target_feature in enumerate(targets_iterators):

                if feedback.isCanceled():
                    break

                if observer_feature.attribute(observers_id) == target_feature.attribute(
                        target_definition_id_field):

                    start_point = QgsPoint(observer_feature.geometry().asPoint())
                    direction_point = QgsPoint(target_feature.geometry().asPoint())

                    line = distance_matrix.build_line(start_point, direction_point)

                    points = line.points()

                    points3d = []

                    for p in points:

                        z = list_rasters.extract_interpolated_value(p)

                        if z is not None:
                            points3d.append(QgsPoint(p.x(), p.y(), z))

                    line = QgsLineString(points3d)

                    f = QgsFeature(fields)
                    f.setGeometry(line)
                    f.setAttribute(f.fieldNameIndex(FieldNames.LOS_TYPE),
                                   NamesConstants.LOS_NO_TARGET)
                    f.setAttribute(f.fieldNameIndex(FieldNames.ID_OBSERVER),
                                   int(observer_feature.attribute(observers_id)))
                    f.setAttribute(f.fieldNameIndex(FieldNames.ID_TARGET),
                                   int(target_feature.attribute(targets_id)))
                    f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_OFFSET),
                                   float(observer_feature.attribute(observers_offset)))
                    f.setAttribute(f.fieldNameIndex(FieldNames.AZIMUTH),
                                   target_feature.attribute(FieldNames.AZIMUTH))
                    f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_X),
                                   observer_feature.geometry().asPoint().x())
                    f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_Y),
                                   observer_feature.geometry().asPoint().y())

                    # TODO compatability with older version
                    if FieldNames.ANGLE_STEP in targets_layer.fields().names():
                        f.setAttribute(f.fieldNameIndex(FieldNames.ANGLE_STEP),
                                       target_feature.attribute(FieldNames.ANGLE_STEP))

                    sink.addFeature(f)
                    feedback.setProgress((target_count / feature_count) * 100)

        return {self.OUTPUT_LAYER: dest_id}

    def name(self):
        return "notargetlos2"

    def displayName(self):
        return "Create no target LoS V2"

    def group(self):
        return "LoS Creation"

    def groupId(self):
        return "loscreate"

    def createInstance(self):
        return CreateNoTargetLosAlgorithmV2()

    def helpUrl(self):
        # return "https://jancaha.github.io/qgis_los_tools/tools/LoS%20Creation/tool_create_notarget_los/"
        pass

    def shortHelpString(self):
        # return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
        pass
