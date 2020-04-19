from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterField)

import processing


class CreatePointsInAreaAlgorithm(QgsProcessingAlgorithm):

    INPUT_LAYER = "InputLayer"
    ID_FIELD = "IdField"
    INPUT_RASTER = "InputRaster"
    OUTPUT_LAYER = "OutputLayer"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LAYER,
                "Input polygon layer",
                [QgsProcessing.TypeVectorPolygon])
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.ID_FIELD,
                "ID field to assign to output",
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_RASTER,
                "Raster Layer to align the points to",
                [QgsProcessing.TypeRaster]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LAYER,
                "Output layer")
        )

    def processAlgorithm(self, parameters, context, feedback):

        input_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        id_field = self.parameterAsString(parameters, self.ID_FIELD, context)
        input_raster = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        input_raster = input_raster.dataProvider()

        raster_extent = input_raster.extent()

        points_layer = processing.run("qgis:regularpoints",
                                      {'EXTENT': raster_extent,
                                       'SPACING': raster_extent.width() / input_raster.xSize(),
                                       'INSET': (raster_extent.width() / input_raster.xSize())/2,
                                       'RANDOMIZE': False,
                                       'IS_SPACING': True,
                                       'CRS': input_layer.sourceCrs(),
                                       'OUTPUT': 'TEMPORARY_OUTPUT'},
                                      context=context, feedback=feedback, is_child_algorithm=True)

        points_in_polygon = processing.run("native:extractbylocation",
                                           {'INPUT': points_layer['OUTPUT'],
                                            'PREDICATE': [0],
                                            'INTERSECT': input_layer,
                                            'OUTPUT': 'TEMPORARY_OUTPUT'},
                                           context=context, feedback=feedback, is_child_algorithm=True)

        fields = input_layer.fields().names()
        fields.remove(id_field)

        intersect_polygon = processing.run("qgis:deletecolumn",
                                           {'INPUT': input_layer,
                                            'COLUMN': fields,
                                            'OUTPUT': 'TEMPORARY_OUTPUT'},
                                           context=context, feedback=feedback, is_child_algorithm=True)

        result_layer = processing.run("native:joinattributesbylocation",
                                      {'INPUT': points_in_polygon['OUTPUT'],
                                       'JOIN': intersect_polygon['OUTPUT'],
                                       'PREDICATE': [0],
                                       'JOIN_FIELDS': [],
                                       'METHOD': 0,
                                       'DISCARD_NONMATCHING': False,
                                       'PREFIX': '',
                                       'OUTPUT': parameters[self.OUTPUT_LAYER]},
                                      context=context, feedback=feedback, is_child_algorithm=True)

        return {self.OUTPUT_LAYER: result_layer['OUTPUT']}

    def name(self):
        return "pointsarea"

    def displayName(self):
        return "Create points in polygon"

    def group(self):
        return "Points creation"

    def groupId(self):
        return "pointscreation"

    def createInstance(self):
        return CreatePointsInAreaAlgorithm()
