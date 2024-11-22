import math
import re
from typing import List, Optional, Union

import numpy as np
from qgis.core import (
    Qgis,
    QgsGeometry,
    QgsLineString,
    QgsMessageLog,
    QgsPoint,
    QgsPointXY,
    QgsPolygon,
    QgsProcessingException,
    QgsRasterDataProvider,
    QgsRectangle,
    QgsVectorLayer,
    QgsVertexId,
    QgsVertexIterator,
    QgsWkbTypes,
)

from los_tools.constants.field_names import FieldNames


def line_to_polygon(line: QgsLineString, observer_point: QgsPointXY, angle_width: float) -> QgsPolygon:
    angle_width = angle_width / 2

    line_start_point = QgsPointXY(line.startPoint())
    line_end_point = QgsPointXY(line.endPoint())

    azimuth = observer_point.azimuth(line_end_point)

    point_1 = observer_point.project(observer_point.distance(line_start_point), azimuth + angle_width)
    point_2 = observer_point.project(observer_point.distance(line_end_point), azimuth + angle_width)
    point_3 = observer_point.project(observer_point.distance(line_end_point), azimuth - angle_width)
    point_4 = observer_point.project(observer_point.distance(line_start_point), azimuth - angle_width)

    poly = QgsPolygon(QgsLineString([line_start_point, point_1, point_2, line_end_point, point_3, point_4]))

    return poly


def get_los_type(los_layer: QgsVectorLayer, field_names: List[str]) -> str:
    index = field_names.index(FieldNames.LOS_TYPE)
    los_types = los_layer.uniqueValues(index)

    if len(los_types) != 1:
        msg = (
            "More than one type of LoS present in layer. Cannot process such layer. "
            "Existing LoS types are {0}.".format(", ".join(los_types))
        )

        QgsMessageLog.logMessage(msg, "los_tools", Qgis.Critical)

        raise QgsProcessingException(msg)

    return list(los_types)[0]


def get_horizon_lines_type(horizon_lines_layer: QgsVectorLayer) -> str:
    index = horizon_lines_layer.fields().names().index(FieldNames.HORIZON_TYPE)
    horizon_lines_types = horizon_lines_layer.uniqueValues(index)

    if len(horizon_lines_types) != 1:
        msg = (
            "More than one type of horizon lines present in layer. Cannot process such layer. "
            "Existing LoS types are {0}.".format(", ".join(horizon_lines_types))
        )

        QgsMessageLog.logMessage(msg, "los_tools", Qgis.Critical)

        raise QgsProcessingException(msg)

    return list(horizon_lines_types)[0]


def check_existence_los_fields(field_names: List[str]) -> None:
    if not (
        FieldNames.LOS_TYPE in field_names
        or FieldNames.ID_OBSERVER in field_names
        or FieldNames.ID_TARGET in field_names
    ):
        msg = (
            "Fields specific for LoS not found in current layer ({0}, {1}, {2}). "
            "Cannot analyse the layer as LoS.".format(FieldNames.LOS_TYPE, FieldNames.ID_OBSERVER, FieldNames.ID_TARGET)
        )

        QgsMessageLog.logMessage(msg, "los_tools", Qgis.Critical)

        raise QgsProcessingException(msg)


def wkt_to_array_points(wkt: str) -> List[List[float]]:
    reg = re.compile(r"(LineString\s?Z |LINESTRING |MULTILINESTRING |MultiLineString\s?Z )", re.IGNORECASE)

    wkt = reg.sub("", wkt)

    array = wkt.replace("(", "").replace(")", "").split(",")

    array_result: List[List[float]] = []

    for element in array:
        coords = element.strip().split(" ")
        array_result.append([float(coords[0]), float(coords[1]), float(coords[2])])

    return array_result


def line_geometry_to_coords(geom: QgsGeometry) -> List[List[float]]:
    if geom.wkbType() not in [
        QgsWkbTypes.Type.LineString,
        QgsWkbTypes.Type.LineString25D,
        QgsWkbTypes.Type.LineStringZ,
        QgsWkbTypes.Type.MultiLineString,
        QgsWkbTypes.Type.MultiLineString25D,
        QgsWkbTypes.Type.MultiLineStringZ,
    ]:
        raise TypeError("Geometry has to be LineString or MultiLineString optionally with Z coordinate.")

    geom_const = geom.constGet()

    vertex_count = 0

    for i in range(geom_const.partCount()):
        vertex_count += geom_const.vertexCount(i)

    coords = [[0.0 for y in range(3)] for x in range(vertex_count)]

    itv: QgsVertexIterator = geom.vertices()

    i = 0
    while itv.hasNext():
        vertex: QgsPoint = itv.next()
        coords[i][0] = vertex.x()
        coords[i][1] = vertex.y()
        coords[i][2] = vertex.z()
        i += 1

    return coords


def segmentize_los_line(line: QgsGeometry, segment_length: float) -> QgsLineString:
    if not isinstance(line, QgsGeometry):
        raise TypeError("`line` should be `QgsGeometry`.")

    if line.type() != QgsWkbTypes.GeometryType.LineGeometry:
        raise TypeError("Can only properly segmentize Lines.")

    if 3 < line.constGet().vertexCount():
        raise ValueError("Should only segmentize lines with at most 3 vertices.")

    return segmentize_line(line, segment_length)


def segmentize_line(line: QgsGeometry, segment_length: float) -> QgsLineString:
    ideal_length_parts = math.ceil(line.length() / segment_length)
    ideal_length_addition = ideal_length_parts * segment_length - line.length()

    line_extented = QgsLineString([x for x in line.vertices()])
    line_extented.extend(0, ideal_length_addition * 0.9)

    line_geom = QgsGeometry(line_extented)

    line_geom = line_geom.densifyByDistance(distance=np.nextafter(float(segment_length), np.inf))

    line_res = QgsLineString([x for x in line_geom.vertices()])

    line_res.moveVertex(
        QgsVertexId(0, 0, line_geom.constGet().vertexCount() - 1),
        line.vertexAt(line.constGet().vertexCount() - 1),
    )

    return line_res


def get_diagonal_size(raster: QgsRasterDataProvider) -> float:
    extent = raster.extent()
    return math.sqrt(math.pow(extent.width(), 2) + math.pow(extent.height(), 2))


# taken from plugin rasterinterpolation https://plugins.qgis.org/plugins/rasterinterpolation/
def bilinear_interpolated_value(raster: QgsRasterDataProvider, point: Union[QgsPoint, QgsPointXY]) -> Optional[float]:
    # see the implementation of raster data provider, identify method
    # https://github.com/qgis/Quantum-GIS/blob/master/src/core/raster/qgsrasterdataprovider.cpp#L268
    x = point.x()
    y = point.y()

    extent = raster.extent()

    xres = extent.width() / raster.xSize()
    yres = extent.height() / raster.ySize()

    col = round((x - extent.xMinimum()) / xres)
    row = round((extent.yMaximum() - y) / yres)

    xMin = extent.xMinimum() + (col - 1) * xres
    xMax = xMin + 2 * xres
    yMax = extent.yMaximum() - (row - 1) * yres
    yMin = yMax - 2 * yres

    pixelExtent = QgsRectangle(xMin, yMin, xMax, yMax)

    myBlock = raster.block(1, pixelExtent, 2, 2)

    # http://en.wikipedia.org/wiki/Bilinear_interpolation#Algorithm
    v12 = myBlock.value(0, 0)
    v22 = myBlock.value(0, 1)
    v11 = myBlock.value(1, 0)
    v21 = myBlock.value(1, 1)

    if raster.sourceNoDataValue(1) in (v12, v22, v11, v21):
        return None

    x1 = xMin + xres / 2
    x2 = xMax - xres / 2
    y1 = yMin + yres / 2
    y2 = yMax - yres / 2

    value = (
        v11 * (x2 - x) * (y2 - y) + v21 * (x - x1) * (y2 - y) + v12 * (x2 - x) * (y - y1) + v22 * (x - x1) * (y - y1)
    ) / ((x2 - x1) * (y2 - y1))

    if value is not None and value == raster.sourceNoDataValue(1):
        return None

    return value


def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))


def get_max_decimal_numbers(values: List[Union[int, float]]) -> int:
    values = [len(str(x).split(".")[1]) for x in values]

    return int(max(values))


def round_all_values(values: List[Union[int, float]], number_of_digits: int) -> List[Union[int, float]]:
    return [round(x, number_of_digits) for x in values]
