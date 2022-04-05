from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterDestination, QgsProcessingUtils,
                       QgsProcessingParameterRasterLayer, QgsRasterLayer, QgsProcessingException)

from qgis.analysis import (QgsRasterCalculatorEntry, QgsRasterCalculator)
import processing
from processing.algs.gdal.GdalUtils import GdalUtils

import tempfile
import uuid

from los_tools.tools.util_functions import get_doc_file


class ReplaceRasterValuesByConstantValueAlgorithm(QgsProcessingAlgorithm):

    RASTER_LAYER = "RasterLayer"
    VECTOR_LAYER = "VectorLayer"
    OUTPUT_RASTER = "OutputRaster"
    RASTER_VALUE = "RasterValue"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterRasterLayer(self.RASTER_LAYER, "Raster Layer",
                                              [QgsProcessing.TypeRaster]))

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.VECTOR_LAYER, "Vector Layer",
                                                [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(
            QgsProcessingParameterNumber(self.RASTER_VALUE, "Replacement value", defaultValue=1))

        self.addParameter(
            QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Output Raster"))

    def processAlgorithm(self, parameters, context, feedback):

        raster_layer = self.parameterAsRasterLayer(parameters, self.RASTER_LAYER, context)

        if raster_layer is None:
            raise QgsProcessingException(self.invalidRasterError(parameters, self.RASTER_LAYER))

        raster_new_value = self.parameterAsDouble(parameters, self.RASTER_VALUE, context)

        vector_layer = self.parameterAsVectorLayer(parameters, self.VECTOR_LAYER, context)

        if vector_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.VECTOR_LAYER))

        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)

        raster_crs = raster_layer.crs()

        raster_one_value = "{}/raster_one_{}.tif".format(tempfile.gettempdir(), uuid.uuid4().hex)

        raster_extent = raster_layer.dataProvider().extent()

        params = {
            'BURN': raster_new_value,
            'DATA_TYPE': 5,
            'EXTENT': raster_extent,
            'EXTRA': '',
            'FIELD': '',
            'INIT': 0,
            'INPUT': vector_layer,
            'INVERT': False,
            'NODATA': None,
            'OPTIONS': '',
            'OUTPUT': raster_one_value,
            'UNITS': 1,
            'WIDTH': raster_extent.width() / raster_layer.dataProvider().xSize(),
            'HEIGHT': raster_extent.height() / raster_layer.dataProvider().ySize()
        }

        processing.run("gdal:rasterize", params)

        temp_raster = QgsRasterLayer(raster_one_value)

        one_value_raster = QgsRasterCalculatorEntry()
        one_value_raster.ref = 'one_value_raster@1'
        one_value_raster.raster = temp_raster
        one_value_raster.bandNumber = 1

        org_raster = QgsRasterCalculatorEntry()
        org_raster.ref = 'org_rast@1'
        org_raster.raster = raster_layer
        org_raster.bandNumber = 1

        raster_entries = []
        raster_entries.append(one_value_raster)
        raster_entries.append(org_raster)

        expression = "({0} != {1}) * {2} + {0}".format(one_value_raster.ref, raster_new_value,
                                                       org_raster.ref)

        calc = QgsRasterCalculator(expression, output_raster,
                                   GdalUtils.getFormatShortNameFromFilename(output_raster),
                                   raster_extent, raster_crs, int(raster_extent.width()),
                                   int(raster_extent.height()), raster_entries,
                                   context.transformContext())

        calc.processCalculation()

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
