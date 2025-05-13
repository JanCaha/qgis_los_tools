from qgis.core import (
    QgsApplication,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingUtils,
)

from los_tools.utils import get_doc_file


class ReplaceRasterValuesByFieldValuesAlgorithm(QgsProcessingAlgorithm):
    RASTER_LAYER = "RasterLayer"
    VECTOR_LAYER = "VectorLayer"
    OUTPUT_RASTER = "OutputRaster"
    VALUE_FIELD = "ValueField"

    def initAlgorithm(self, configuration=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(self.RASTER_LAYER, "Raster Layer", [QgsProcessing.TypeRaster])
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.VECTOR_LAYER, "Vector Layer", [QgsProcessing.TypeVectorPolygon])
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.VALUE_FIELD,
                "Field specifying the replacement values",
                parentLayerParameterName=self.VECTOR_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=False,
            )
        )

        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Output Raster"))

    def processAlgorithm(self, parameters, context, feedback):
        raster_layer = self.parameterAsRasterLayer(parameters, self.RASTER_LAYER, context)

        if raster_layer is None:
            raise QgsProcessingException(self.invalidRasterError(parameters, self.RASTER_LAYER))

        value_field_name = self.parameterAsString(parameters, self.VALUE_FIELD, context)

        vector_layer = self.parameterAsVectorLayer(parameters, self.VECTOR_LAYER, context)

        if vector_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.VECTOR_LAYER))

        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)

        alg_gdal_translate = QgsApplication.processingRegistry().algorithmById("gdal:translate")

        params = {
            "INPUT": raster_layer,
            "TARGET_CRS": None,
            "NODATA": None,
            "COPY_SUBDATASETS": False,
            "OPTIONS": "",
            "EXTRA": "",
            "DATA_TYPE": 0,
            "OUTPUT": output_raster,
        }

        alg_gdal_translate.run(params, context, feedback)

        alg_gdal_rasterize = QgsApplication.processingRegistry().algorithmById("gdal:rasterize_over")

        params = {
            "INPUT": vector_layer,
            "INPUT_RASTER": output_raster,
            "FIELD": value_field_name,
            "ADD": False,
            "EXTRA": "",
        }

        alg_gdal_rasterize.run(params, context, feedback)

        return {self.OUTPUT_RASTER: output_raster}

    def name(self):
        return "replacerastervaluesbyfield"

    def displayName(self):
        return "Replace Raster Values by Field Values"

    def group(self):
        return "Raster Editing"

    def groupId(self):
        return "rasterediting"

    def createInstance(self):
        return ReplaceRasterValuesByFieldValuesAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/Raster%20Editing/tool_replace_raster_values/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
