from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterRasterDestination,
    QgsProcessingUtils,
    QgsProcessingParameterRasterLayer,
    QgsProcessingException,
    QgsApplication,
)

from los_tools.utils import get_doc_file


class ReplaceRasterValuesByConstantValueAlgorithm(QgsProcessingAlgorithm):
    RASTER_LAYER = "RasterLayer"
    VECTOR_LAYER = "VectorLayer"
    OUTPUT_RASTER = "OutputRaster"
    RASTER_VALUE = "RasterValue"

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.RASTER_LAYER, "Raster Layer", [QgsProcessing.TypeRaster]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.VECTOR_LAYER, "Vector Layer", [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.RASTER_VALUE, "Replacement value", defaultValue=1
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Output Raster")
        )

    def processAlgorithm(self, parameters, context, feedback):
        raster_layer = self.parameterAsRasterLayer(
            parameters, self.RASTER_LAYER, context
        )

        if raster_layer is None:
            raise QgsProcessingException(
                self.invalidRasterError(parameters, self.RASTER_LAYER)
            )

        raster_new_value = self.parameterAsDouble(
            parameters, self.RASTER_VALUE, context
        )

        vector_layer = self.parameterAsVectorLayer(
            parameters, self.VECTOR_LAYER, context
        )

        if vector_layer is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.VECTOR_LAYER)
            )

        output_raster = self.parameterAsOutputLayer(
            parameters, self.OUTPUT_RASTER, context
        )

        alg_gdal_translate = QgsApplication.processingRegistry().algorithmById(
            "gdal:translate"
        )

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

        alg_gdal_rasterize = QgsApplication.processingRegistry().algorithmById(
            "gdal:rasterize_over_fixed_value"
        )

        params = {
            "INPUT": vector_layer,
            "INPUT_RASTER": output_raster,
            "BURN": raster_new_value,
            "ADD": False,
            "EXTRA": "",
        }

        alg_gdal_rasterize.run(params, context, feedback)

        return {self.OUTPUT_RASTER: output_raster}

    def name(self):
        return "replacerastervaluesbyconstant"

    def displayName(self):
        return "Replace Raster Values by Constant Value"

    def group(self):
        return "Raster Editing"

    def groupId(self):
        return "rasterediting"

    def createInstance(self):
        return ReplaceRasterValuesByConstantValueAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/Raster%20Editing/tool_replace_raster_values/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
