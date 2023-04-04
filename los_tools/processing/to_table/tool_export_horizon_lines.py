from qgis.core import (QgsProcessing, QgsFields, QgsField, QgsFeature, QgsFeatureSink,
                       QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                       QgsProcessingFeatureSource, QgsProcessingParameterFeatureSink, QgsWkbTypes,
                       QgsMessageLog, QgsPointXY, Qgis, QgsFeatureSource, QgsProcessingUtils,
                       QgsProcessingException)

from qgis.PyQt.QtCore import (QVariant)

from los_tools.constants.field_names import FieldNames
from los_tools.utils import get_doc_file


class ExportHorizonLinesAlgorithm(QgsProcessingAlgorithm):

    INPUT_HORIZON_LINES_LAYER = "HorizonLinesLayer"
    OUTPUT = "OutputFile"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT_HORIZON_LINES_LAYER,
                                                "Horizon Lines Layer",
                                                [QgsProcessing.TypeVectorLine]))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, "Output file"))

    def checkParameterValues(self, parameters, context):

        input_horizon_lines_layer: QgsProcessingFeatureSource = self.parameterAsSource(
            parameters, self.INPUT_HORIZON_LINES_LAYER, context)

        field_names = input_horizon_lines_layer.fields().names()

        if FieldNames.HORIZON_TYPE not in field_names:
            msg = "Fields specific for horizon lines not found in current layer ({0}). " \
                  "Cannot to_table the layer as horizon lines.".format(FieldNames.HORIZON_TYPE)

            QgsMessageLog.logMessage(msg, "los_tools", Qgis.MessageLevel.Critical)
            return False, msg

        return True, "OK"

    def processAlgorithm(self, parameters, context, feedback):

        input_horizon_lines_layer: QgsFeatureSource = self.parameterAsSource(
            parameters, self.INPUT_HORIZON_LINES_LAYER, context)

        if input_horizon_lines_layer is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT_HORIZON_LINES_LAYER))

        feature_count = input_horizon_lines_layer.featureCount()

        fields = QgsFields()
        fields.append(QgsField(FieldNames.ID_OBSERVER, QVariant.Int))
        fields.append(QgsField(FieldNames.HORIZON_TYPE, QVariant.String))
        fields.append(QgsField(FieldNames.ANGLE, QVariant.Double))
        fields.append(QgsField(FieldNames.VIEWING_ANGLE, QVariant.Double))
        fields.append(QgsField(FieldNames.CSV_HORIZON_DISTANCE, QVariant.Double))

        sink: QgsFeatureSink
        sink, path_sink = self.parameterAsSink(parameters, self.OUTPUT, context, fields,
                                               QgsWkbTypes.NoGeometry,
                                               input_horizon_lines_layer.sourceCrs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LAYER))

        iterator = input_horizon_lines_layer.getFeatures()

        for cnt, horizon_line_feature in enumerate(iterator):

            if feedback.isCanceled():
                break

            observer_point = QgsPointXY(horizon_line_feature.attribute(FieldNames.OBSERVER_X),
                                        horizon_line_feature.attribute(FieldNames.OBSERVER_Y))

            observer_id = horizon_line_feature.attribute(FieldNames.ID_OBSERVER)
            horizon_type = horizon_line_feature.attribute(FieldNames.HORIZON_TYPE)

            line_geometry = horizon_line_feature.geometry()

            i = 0
            for v in line_geometry.vertices():
                horizon_point = QgsPointXY(v.x(), v.y())

                feature = QgsFeature(fields)

                feature.setAttribute(FieldNames.ID_OBSERVER, observer_id)
                feature.setAttribute(FieldNames.HORIZON_TYPE, horizon_type)
                feature.setAttribute(FieldNames.ANGLE, observer_point.azimuth(horizon_point))
                feature.setAttribute(FieldNames.VIEWING_ANGLE, v.m())
                feature.setAttribute(FieldNames.CSV_HORIZON_DISTANCE,
                                     observer_point.distance(v.x(), v.y()))

                i += 1

                sink.addFeature(feature)

            feedback.setProgress((cnt / feature_count) * 100)

        return {self.OUTPUT: path_sink}

    def name(self):
        return "exporthorizonlines"

    def displayName(self):
        return "Export Horizon Lines Layer"

    def group(self):
        return "Export to Table"

    def groupId(self):
        return "to_table"

    def createInstance(self):
        return ExportHorizonLinesAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/Export%20to%20table/tool_export_horizon_lines/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
