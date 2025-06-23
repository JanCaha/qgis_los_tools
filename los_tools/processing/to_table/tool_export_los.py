from qgis.core import (
    Qgis,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingUtils,
)
from qgis.PyQt.QtCore import QMetaType

from los_tools.classes.classes_los import LoSGlobal, LoSLocal, LoSWithoutTarget
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.processing.tools.util_functions import get_los_type
from los_tools.utils import get_doc_file


class ExportLoSAlgorithm(QgsProcessingAlgorithm):
    INPUT_LOS_LAYER = "LoSLayer"
    OUTPUT = "OutputFile"
    CURVATURE_CORRECTIONS = "CurvatureCorrections"
    REFRACTION_COEFFICIENT = "RefractionCoefficient"

    def initAlgorithm(self, configuration=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT_LOS_LAYER, "LoS layer", [QgsProcessing.TypeVectorLine])
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

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, "Output file"))

    def checkParameterValues(self, parameters, context):
        input_los_layer = self.parameterAsSource(parameters, self.INPUT_LOS_LAYER, context)

        field_names = input_los_layer.fields().names()

        if FieldNames.LOS_TYPE not in field_names:
            msg = (
                f"Fields specific for LoS not found in current layer ({FieldNames.LOS_TYPE}). "
                "Cannot to_table the layer as horizon lines."
            )

            return False, msg

        return True, "OK"

    def processAlgorithm(self, parameters, context, feedback):
        input_los_layer = self.parameterAsSource(parameters, self.INPUT_LOS_LAYER, context)

        if input_los_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_LOS_LAYER))

        curvature_corrections = self.parameterAsBool(parameters, self.CURVATURE_CORRECTIONS, context)
        ref_coeff = self.parameterAsDouble(parameters, self.REFRACTION_COEFFICIENT, context)

        feature_count = input_los_layer.featureCount()
        iterator = input_los_layer.getFeatures()

        los_type = get_los_type(input_los_layer, input_los_layer.fields().names())

        fields = QgsFields()

        fields.append(QgsField(FieldNames.ID_LOS, QMetaType.Type.Int))
        fields.append(QgsField(FieldNames.ID_OBSERVER, QMetaType.Type.Int))
        fields.append(QgsField(FieldNames.OBSERVER_OFFSET, QMetaType.Type.Double))
        fields.append(QgsField(FieldNames.CSV_OBSERVER_DISTANCE, QMetaType.Type.Double))
        fields.append(QgsField(FieldNames.CSV_ELEVATION, QMetaType.Type.Double))
        fields.append(QgsField(FieldNames.CSV_VISIBLE, QMetaType.Type.Bool))
        fields.append(QgsField(FieldNames.CSV_HORIZON, QMetaType.Type.Bool))

        if los_type == NamesConstants.LOS_LOCAL:
            fields.append(QgsField(FieldNames.ID_TARGET, QMetaType.Type.Int))
            fields.append(QgsField(FieldNames.TARGET_OFFSET, QMetaType.Type.Double))

        elif los_type == NamesConstants.LOS_GLOBAL:
            fields.append(QgsField(FieldNames.ID_TARGET, QMetaType.Type.Int))
            fields.append(QgsField(FieldNames.TARGET_OFFSET, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.TARGET_X, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.TARGET_Y, QMetaType.Type.Double))
            fields.append(QgsField(FieldNames.CSV_TARGET, QMetaType.Type.Bool))

        # elif los_type == NamesConstants.LOS_NO_TARGET:
        #     pass

        sink: QgsFeatureSink
        sink, path_sink = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            Qgis.WkbType.NoGeometry,
            input_los_layer.sourceCrs(),
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        los_feature: QgsFeature
        for cnt, los_feature in enumerate(iterator):
            if feedback.isCanceled():
                break

            los_id = los_feature.id()
            observer_id = los_feature.attribute(FieldNames.ID_OBSERVER)
            observer_offset = los_feature.attribute(FieldNames.OBSERVER_OFFSET)

            if los_type == NamesConstants.LOS_LOCAL:
                target_id = los_feature.attribute(FieldNames.ID_TARGET)
                target_offset = los_feature.attribute(FieldNames.TARGET_OFFSET)

                los = LoSLocal.from_feature(
                    feature=los_feature,
                    curvature_corrections=curvature_corrections,
                    refraction_coefficient=ref_coeff,
                )

            elif los_type == NamesConstants.LOS_GLOBAL:
                target_id = los_feature.attribute(FieldNames.ID_TARGET)
                target_offset = los_feature.attribute(FieldNames.TARGET_OFFSET)
                target_x = los_feature.attribute(FieldNames.TARGET_X)
                target_y = los_feature.attribute(FieldNames.TARGET_Y)

                los = LoSGlobal.from_feature(
                    feature=los_feature,
                    curvature_corrections=curvature_corrections,
                    refraction_coefficient=ref_coeff,
                )

            # elif los_type == NamesConstants.LOS_NO_TARGET:
            else:
                los = LoSWithoutTarget.from_feature(
                    feature=los_feature,
                    curvature_corrections=curvature_corrections,
                    refraction_coefficient=ref_coeff,
                )

            for i, _ in enumerate(los.points):
                feature = QgsFeature(fields)

                if los_type == NamesConstants.LOS_LOCAL:
                    feature.setAttributes(
                        [
                            los_id,
                            observer_id,
                            observer_offset,
                            los.points[i].distance,
                            los.points[i].z,
                            los.visible[i],
                            los.horizon[i],
                            target_id,
                            target_offset,
                        ]
                    )

                elif los_type == NamesConstants.LOS_GLOBAL:
                    is_target = i == los.target_index

                    feature.setAttributes(
                        [
                            los_id,
                            observer_id,
                            observer_offset,
                            los.points[i].distance,
                            los.points[i].z,
                            los.visible[i],
                            los.horizon[i],
                            target_id,
                            target_offset,
                            target_x,
                            target_y,
                            is_target,
                        ]
                    )

                # elif los_type == NamesConstants.LOS_NO_TARGET:
                else:
                    feature.setAttributes(
                        [
                            los_id,
                            observer_id,
                            observer_offset,
                            los.points[i].distance,
                            los.points[i].z,
                            los.visible[i],
                            los.horizon[i],
                        ]
                    )

                sink.addFeature(feature)

            feedback.setProgress((cnt / feature_count) * 100)

        return {self.OUTPUT: path_sink}

    def name(self):
        return "exportlos"

    def displayName(self):
        return "Export LoS Layer"

    def group(self):
        return "Export to Table"

    def groupId(self):
        return "to_table"

    def createInstance(self):
        return ExportLoSAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/Export%20to%20table/tool_export_los/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
