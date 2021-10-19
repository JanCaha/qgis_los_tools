import math
import numpy as np
from typing import List, Any, NoReturn, Optional

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterMatrix,
    QgsProcessingParameterMultipleLayers,
    QgsField,
    QgsFeature,
    QgsWkbTypes,
    QgsPoint,
    QgsFields,
    QgsLineString,
    QgsGeometry,
    QgsProcessingUtils,
    QgsRasterDataProvider,
    QgsRasterLayer)

from qgis.PyQt.QtCore import QVariant
from los_tools.tools.util_functions import bilinear_interpolated_value, get_diagonal_size
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.tools.util_functions import get_doc_file, log


class CreateNoTargetLosAlgorithmV2(QgsProcessingAlgorithm):

    OBSERVER_POINTS_LAYER = "ObserverPoints"
    OBSERVER_ID_FIELD = "ObserverIdField"
    OBSERVER_OFFSET_FIELD = "ObserverOffset"
    TARGET_POINTS_LAYER = "TargetPoints"
    TARGET_ID_FIELD = "TargetIdField"
    TARGET_DEFINITION_ID_FIELD = "TargetDefinitionIdField"
    OUTPUT_LAYER = "OutputLayer"

    DEM_RASTERS = "DemRasters"
    LINE_SETTINGS = "LineSettings"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.DEM_RASTERS,
                "Raster DEM Layers",
                QgsProcessing.TypeRaster
            )
        )

        self.addParameter(
            QgsProcessingParameterMatrix(
                self.LINE_SETTINGS,
                "Sampling distance - distance matrix: ",
                numberRows=3,
                headers=["Sampling distance", "Distance limit"],
                defaultValue=[1, "Inf"]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.OBSERVER_POINTS_LAYER,
                "Observers point layer",
                [QgsProcessing.TypeVectorPoint])
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.OBSERVER_ID_FIELD,
                "Observer ID field",
                parentLayerParameterName=self.OBSERVER_POINTS_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.OBSERVER_OFFSET_FIELD,
                "Observer offset field",
                parentLayerParameterName=self.OBSERVER_POINTS_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TARGET_POINTS_LAYER,
                "Targets point layer",
                [QgsProcessing.TypeVectorPoint])
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.TARGET_ID_FIELD,
                "Target ID field",
                parentLayerParameterName=self.TARGET_POINTS_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.TARGET_DEFINITION_ID_FIELD,
                "Target and Observer agreement ID field",
                parentLayerParameterName=self.TARGET_POINTS_LAYER,
                type=QgsProcessingParameterField.Numeric,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LAYER,
                "Output layer")
        )

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

        rasters = self.parameterAsLayerList(parameters, self.DEM_RASTERS, context)

        for raster in rasters:

            dem_band_count = raster.bandCount()

            if dem_band_count != 1:

                msg = f"`{raster.name()}` can only have one band. Currently there are `{dem_band_count}` bands."

                return False, msg

            if not raster.crs() == observers_layer.sourceCrs():

                msg = f"`Observers point layer` and `{raster.name()}` crs must be equal. " \
                      f"Right now they are not."

                return False, msg

            return SamplingDistanceMatrix.validate_table(self.parameterAsMatrix(parameters, self.LINE_SETTINGS, context))

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):

        observers_layer = self.parameterAsSource(parameters, self.OBSERVER_POINTS_LAYER, context)
        observers_id = self.parameterAsString(parameters, self.OBSERVER_ID_FIELD, context)
        observers_offset = self.parameterAsString(parameters, self.OBSERVER_OFFSET_FIELD, context)
        targets_layer = self.parameterAsSource(parameters, self.TARGET_POINTS_LAYER, context)
        targets_id = self.parameterAsString(parameters, self.TARGET_ID_FIELD, context)
        target_definition_id_field = self.parameterAsString(parameters, self.TARGET_DEFINITION_ID_FIELD, context)

        self.rasters = self.get_raster_ordered_by_pixel_size(self.parameterAsLayerList(parameters, self.DEM_RASTERS, context))

        self.distances = SamplingDistanceMatrix(self.parameterAsMatrix(parameters, self.LINE_SETTINGS, context))

        fields = QgsFields()
        fields.append(QgsField(FieldNames.LOS_TYPE, QVariant.String))
        fields.append(QgsField(FieldNames.ID_OBSERVER, QVariant.Int))
        fields.append(QgsField(FieldNames.ID_TARGET, QVariant.Int))
        fields.append(QgsField(FieldNames.OBSERVER_OFFSET, QVariant.Double))
        fields.append(QgsField(FieldNames.AZIMUTH, QVariant.Double))
        fields.append(QgsField(FieldNames.OBSERVER_X, QVariant.Double))
        fields.append(QgsField(FieldNames.OBSERVER_Y, QVariant.Double))

        sink, dest_id = self.parameterAsSink(parameters,
                                             self.OUTPUT_LAYER,
                                             context,
                                             fields,
                                             QgsWkbTypes.LineString25D,
                                             observers_layer.sourceCrs())

        feature_count = targets_layer.featureCount()

        observers_iterator = observers_layer.getFeatures()

        max_length_extension = self.distances.maximum_distance

        if math.isinf(max_length_extension):

            max_length_extension = 0

            for rast in self.rasters:

                diagonal_distance = get_diagonal_size(rast)

                if max_length_extension < diagonal_distance:
                    max_length_extension = diagonal_distance

        self.distances.replace_inf_with_value(max_length_extension)

        i = 0

        for observer_count, observer_feature in enumerate(observers_iterator):
            if feedback.isCanceled():
                break

            targets_iterators = targets_layer.getFeatures()

            for target_count, target_feature in enumerate(targets_iterators):

                if observer_feature.attribute(observers_id) == target_feature.attribute(target_definition_id_field):

                    start_point = QgsPoint(observer_feature.geometry().asPoint())
                    end_point = QgsPoint(target_feature.geometry().asPoint())

                    line = self.build_line(start_point, end_point)

                    points = line.points()

                    points3d = []

                    for p in points:

                        z = self.extract_interpolated_value(p)

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

                    sink.addFeature(f)
                    i += 1
                    feedback.setProgress((i/feature_count)*100)

        return {self.OUTPUT_LAYER: dest_id}

    def extract_interpolated_value(self, point: QgsPoint) -> Optional[float]:

        for rast in self.rasters:

            value = bilinear_interpolated_value(rast, point)

            if value is not None:
                return value

    def build_line(self,
                   origin_point: QgsPoint,
                   next_point: QgsPoint):

        directional_line = QgsLineString([origin_point, next_point])

        lines = []

        for i in range(len(self.distances)):

            if i == 0:

                if self.distances.get_row_distance(i) < directional_line.straightDistance2d():
                    point = directional_line.interpolatePoint(self.distances.get_row_sampling_distance(i))
                    line = QgsLineString([directional_line.startPoint(),
                                          point])

                else:
                    line = directional_line
                    line.extend(0, self.distances.get_row_distance(i) - directional_line.straightDistance2d())

                line = QgsGeometry(line)
                line = line.densifyByDistance(distance=np.nextafter(self.distances.get_row_sampling_distance(i), np.Inf))

                line_res = QgsLineString()
                line_res.fromWkt(line.asWkt())

                lines.append(line_res)

            else:

                this_line: QgsLineString = lines[-1].clone()
                this_line.extend(0, self.distances.get_row_distance(i) - self.distances.get_row_distance(i-1))
                this_line = QgsLineString([lines[-1].endPoint(),
                                           this_line.endPoint()])

                line = QgsGeometry(this_line)
                line = line.densifyByDistance(distance=np.nextafter(self.distances.get_row_sampling_distance(i), np.Inf))

                line_res = QgsLineString()
                line_res.fromWkt(line.asWkt())

                lines.append(line_res)

        result_line = QgsLineString()

        for line_part in lines:
            result_line.append(line_part)

        return result_line

    def get_raster_ordered_by_pixel_size(self, layer_list: List[QgsRasterLayer]) -> List[QgsRasterDataProvider]:

        tuples = []

        rast: QgsRasterLayer

        for rast in layer_list:
            tuples.append((rast, rast.extent().width() / rast.width()))

        sorted_by_second = sorted(tuples, key=lambda tup: tup[1])

        raster_from_top = [x[0].dataProvider() for x in sorted_by_second]

        return raster_from_top

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
        return "https://jancaha.github.io/qgis_los_tools/tools/LoS%20Creation/tool_create_notarget_los/"

    def shortHelpString(self):
        return QgsProcessingUtils.formatHelpMapAsHtml(get_doc_file(__file__), self)


class SamplingDistanceMatrix:

    NUMBER_OF_COLUMNS = 2

    INDEX_SAMPLING_DISTANCE = 0
    INDEX_DISTANCE = 1

    def __init__(self, data: List[Any]):

        self.data = []

        i = 0

        while i < len(data):

            distance = data[i+1]

            if str(distance).lower() == "inf":
                distance = math.inf

            self.data.append([float(data[i]), float(distance)])

            i += 2

        self.data = sorted(self.data, key=lambda d: d[self.INDEX_DISTANCE])

    def __repr__(self):

        strings = ["Sampling distance, Distance Limit"]

        for row in self.data:

            strings.append(f"{row[0]}, {row[1]}")

        return "\n".join(strings)

    def __len__(self):
        return len(self.data)

    def replace_inf_with_value(self, value: float) -> NoReturn:

        if math.isinf(self.maximum_distance):

            self.data[-1][self.INDEX_DISTANCE] = value

            while self.data[-1][self.INDEX_DISTANCE] < self.data[-2][self.INDEX_DISTANCE]:
                self.data.remove(self.data[-2])

    def get_row(self, index: int) -> List[float]:
        return self.data[index]

    def get_row_distance(self, index: int):
        return self.get_row(index)[self.INDEX_DISTANCE]

    def get_row_sampling_distance(self, index: int):
        return self.get_row(index)[self.INDEX_SAMPLING_DISTANCE]

    @staticmethod
    def validate_table(data: List[Any]):

        i = 0

        while i < len(data):

            distance = data[i + 1]

            if str(distance).lower() == "inf":
                distance = math.inf

            try:
                float(data[i])
            except ValueError as e:
                return False, f"Cannot convert value `{data[i]}` into type float."

            try:
                float(data[i+1])
            except ValueError as e:
                return False, f"Cannot convert value `{data[i+1]}` into type float."

            i += 2

        return True, ""

    @property
    def maximum_distance(self) -> float:
        return self.data[-1][self.INDEX_DISTANCE]

    def next_distance(self, current_distance: float) -> float:

        value_to_add = 0

        for row in self.data:
            if current_distance < row[self.INDEX_DISTANCE]:
                value_to_add = row[self.INDEX_SAMPLING_DISTANCE]

        return current_distance + value_to_add
