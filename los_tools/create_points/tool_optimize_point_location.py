import math

from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFeatureSource, QgsProcessingParameterDistance,
                       QgsProcessingParameterFeatureSink, QgsRasterDataProvider, QgsRasterLayer,
                       QgsRectangle, QgsRasterBlock, QgsPoint, QgsFeature, QgsPointXY,
                       QgsProcessingFeatureSource, QgsProcessingUtils, QgsProcessingException,
                       qgsFloatNear)

from los_tools.tools.util_functions import get_doc_file


class OptimizePointLocationAlgorithm(QgsProcessingAlgorithm):

    INPUT_LAYER = "InputLayer"
    INPUT_RASTER = "InputRaster"
    OUTPUT_LAYER = "OutputLayer"
    DISTANCE = "Distance"
    MASK_RASTER = "MaskRaster"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT_RASTER, "Location optimization raster",
                                              [QgsProcessing.TypeRaster]))

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT_LAYER,
                                                "Input point layer (points to optimize)",
                                                [QgsProcessing.TypeVectorPoint]))

        self.addParameter(
            QgsProcessingParameterDistance(self.DISTANCE,
                                           "Search radius",
                                           defaultValue=30.0,
                                           minValue=0.001,
                                           optional=False,
                                           parentParameterName=self.INPUT_RASTER))

        self.addParameter(
            QgsProcessingParameterRasterLayer(self.MASK_RASTER,
                                              "Mask raster", [QgsProcessing.TypeRaster],
                                              optional=True))

        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT_LAYER,
                                              "Output layer (optimized points)"))

    def checkParameterValues(self, parameters, context):

        raster = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        raster_crs = raster.crs()
        raster_band_count = raster.bandCount()

        if raster_band_count != 1:
            msg = "`Location optimization raster` can only have one band." \
                  " Currently there are `{0}` bands.".format(raster_band_count)

            return False, msg

        input_layer = self.parameterAsSource(parameters, self.INPUT_LAYER, context)

        if input_layer.sourceCrs().isGeographic():
            msg = "`Input point layer` crs must be projected. " \
                  "Right now it is `geographic`."

            return False, msg

        if not raster_crs == input_layer.sourceCrs():
            msg = "`Input point layer` and `Location optimization raster` crs must be equal. " \
                  "Right now they are not."

            return False, msg

        raster_extent = raster.dataProvider().extent()

        xres = raster_extent.width() / raster.dataProvider().xSize()
        yres = raster_extent.height() / raster.dataProvider().ySize()

        if not qgsFloatNear(xres, yres, epsilon=0.001):
            msg = "Raster must have equal resolution in both directions."

            return False, msg

        mask_raster = self.parameterAsRasterLayer(parameters, self.MASK_RASTER, context)

        if mask_raster is not None:

            if mask_raster.bandCount() != 1:
                msg = "`Mask raster` can only have one band. Currently there are `{0}` bands.".format(
                    raster_band_count)

                return False, msg

            if raster_crs != mask_raster.crs():
                msg = "CRS for `Mask raster` and `Location optimization raster` must be equal."

                return False, msg

            if not raster.dataProvider().extent() == mask_raster.dataProvider().extent():
                msg = "`Mask raster` extent must be the same as `Location optimization raster`."

                return False, msg

            if not raster.dataProvider().xSize() == mask_raster.dataProvider().xSize():
                msg = "`Mask raster` cell size must be same as cell size for `Location optimization raster`."

                return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):

        input_layer: QgsProcessingFeatureSource = self.parameterAsSource(
            parameters, self.INPUT_LAYER, context)

        if input_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_LAYER))

        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)

        raster: QgsRasterLayer = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER,
                                                             context)

        if raster is None:
            raise QgsProcessingException(self.invalidRasterError(parameters, self.INPUT_RASTER))

        raster: QgsRasterDataProvider = raster.dataProvider()

        mask_raster = self.parameterAsRasterLayer(parameters, self.MASK_RASTER, context)

        if mask_raster is not None:
            mask_raster: QgsRasterDataProvider = mask_raster.dataProvider()

        sink, dest_id = self.parameterAsSink(parameters,
                                             self.OUTPUT_LAYER,
                                             context,
                                             fields=input_layer.fields(),
                                             geometryType=input_layer.wkbType(),
                                             crs=input_layer.sourceCrs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LAYER))

        raster_extent: QgsRectangle = raster.extent()

        max_size = math.sqrt(
            math.pow(raster_extent.width(), 2) + math.pow(raster_extent.height(), 2))

        if max_size < distance:
            distance = max_size

        cell_size = raster_extent.width() / raster.xSize()
        distance_cells = int(distance / cell_size)

        no_data_value = raster.sourceNoDataValue(1)

        if mask_raster is not None:
            mask_no_data_value = mask_raster.sourceNoDataValue(1)

        feature_count = input_layer.featureCount()

        input_layer_iterator = input_layer.getFeatures()

        for input_feature_count, input_layer_feature in enumerate(input_layer_iterator):

            if feedback.isCanceled():
                break

            point: QgsPointXY = input_layer_feature.geometry().asPoint()

            col = round((point.x() - raster_extent.xMinimum()) / cell_size)
            row = round((raster_extent.yMaximum() - point.y()) / cell_size)

            x_min = raster_extent.xMinimum() + (col - distance_cells)
            x_max = x_min + 2 * distance_cells
            y_max = raster_extent.yMaximum() - (row - distance_cells)
            y_min = y_max - 2 * distance_cells

            pixel_extent: QgsRectangle = QgsRectangle(x_min, y_min, x_max, y_max)

            block_values: QgsRasterBlock = raster.block(1, pixel_extent, distance_cells * 2,
                                                        distance_cells * 2)

            if mask_raster is not None:
                mask_block_values: QgsRasterBlock = mask_raster.block(
                    1, pixel_extent, distance_cells * 2, distance_cells * 2)

            max_value_x = -math.inf
            max_value_y = -math.inf
            max_value = -math.inf

            for i in range(0, block_values.width()):
                for j in range(0, block_values.height()):

                    dist = math.sqrt(
                        math.pow(distance_cells - i, 2) + math.pow(distance_cells - j, 2))

                    value = block_values.value(i, j)

                    if value != no_data_value and max_value < value and dist < distance_cells:

                        if mask_raster is not None:
                            mask_value = mask_block_values.value(i, j)
                            if 0 < mask_value != mask_no_data_value:
                                max_value = value
                                max_value_x = j
                                max_value_y = i
                        else:
                            max_value = value
                            max_value_x = j
                            max_value_y = i

            if max_value != -math.inf:
                max_value_x = max_value_x - distance_cells
                max_value_y = max_value_y - distance_cells

                max_value_x = pixel_extent.center().x() + cell_size / 2 + max_value_x * cell_size
                max_value_y = pixel_extent.center().y() - cell_size / 2 - max_value_y * cell_size
            else:
                max_value_x = point.x()
                max_value_y = point.y()

            f = QgsFeature(input_layer.fields())
            f.setGeometry(QgsPoint(max_value_x, max_value_y))
            f.setAttributes(input_layer_feature.attributes())
            sink.addFeature(f)

            feedback.setProgress((input_feature_count / feature_count) * 100)

        return {self.OUTPUT_LAYER: dest_id}

    def name(self):
        return "pointlocationoptimization"

    def displayName(self):
        return "Optimize Point Location"

    def group(self):
        return "Points Creation"

    def groupId(self):
        return "pointscreation"

    def createInstance(self):
        return OptimizePointLocationAlgorithm()

    def helpUrl(self):
        return "https://jancaha.github.io/qgis_los_tools/tools/Points%20Creation/tool_optimize_point_location/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)
