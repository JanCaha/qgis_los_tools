import numpy as np
import math
import os
import json
from typing import List
import re
from pathlib import Path

from qgis.core import (QgsGeometry,
                       QgsLineString,
                       QgsPoint,
                       QgsPointXY,
                       QgsRasterDataProvider,
                       QgsRectangle,
                       QgsVectorLayer,
                       QgsMessageLog,
                       QgsProcessingUtils,
                       QgsProcessingException,
                       Qgis,
                       QgsProcessingAlgorithm)

from los_tools.constants.field_names import FieldNames


def get_los_type(los_layer: QgsVectorLayer, field_names: List[str]) -> str:

    index = field_names.index(FieldNames.LOS_TYPE)
    los_types = los_layer.uniqueValues(index)

    if len(los_types) != 1:
        msg = "More than one type of LoS present in layer. Cannot process such layer. " \
              "Existing LoS types are {0}.".format(", ".join(los_types))

        QgsMessageLog.logMessage(msg,
                                 "los_tools",
                                 Qgis.MessageLevel.Critical)

        raise QgsProcessingException(msg)

    return list(los_types)[0]


def get_horizon_lines_type(horizon_lines_layer: QgsVectorLayer) -> str:

    index = horizon_lines_layer.fields().names().index(FieldNames.HORIZON_TYPE)
    horizon_lines_types = horizon_lines_layer.uniqueValues(index)

    if len(horizon_lines_types) != 1:
        msg = "More than one type of horizon lines present in layer. Cannot process such layer. " \
              "Existing LoS types are {0}.".format(", ".join(horizon_lines_types))

        QgsMessageLog.logMessage(msg,
                                 "los_tools",
                                 Qgis.MessageLevel.Critical)

        raise QgsProcessingException(msg)

    return list(horizon_lines_types)[0]


def check_existence_los_fields(field_names: List[str]) -> None:

    if not (FieldNames.LOS_TYPE in field_names or
            FieldNames.ID_OBSERVER in field_names or
            FieldNames.ID_TARGET in field_names):
        msg = "Fields specific for LoS not found in current layer ({0}, {1}, {2}). " \
              "Cannot analyse the layer as LoS.".format(FieldNames.LOS_TYPE,
                                                        FieldNames.ID_OBSERVER,
                                                        FieldNames.ID_TARGET)

        QgsMessageLog.logMessage(msg,
                                 "los_tools",
                                 Qgis.MessageLevel.Critical)

        raise QgsProcessingException(msg)


def wkt_to_array_points(wkt: str) -> List[List[float]]:
    reg = re.compile("(LINESTRING |LineStringZ )")
    wkt = reg.sub("", wkt)
    array = wkt.replace("(", "").replace(")", "").split(",")

    array_result: List[List[float]] = []

    for element in array:
        coords = element.strip().split(" ")
        array_result.append([float(coords[0]), float(coords[1]), float(coords[2])])

    return array_result


def segmentize_line(line: QgsLineString, segment_length: float) -> QgsLineString:

    line = QgsGeometry(line)

    line = line.densifyByDistance(distance=np.nextafter(float(segment_length), np.Inf))

    line_res = QgsLineString()
    line_res.fromWkt(line.asWkt())

    return line_res


def get_diagonal_size(raster: QgsRasterDataProvider) -> float:
    extent = raster.extent()
    return math.sqrt(math.pow(extent.width(), 2) + math.pow(extent.height(), 2))


# taken from plugin rasterinterpolation https://plugins.qgis.org/plugins/rasterinterpolation/
def bilinear_interpolated_value(raster: QgsRasterDataProvider, point: (QgsPoint, QgsPointXY)) -> [float, None]:
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
    value = (v11 * (x2 - x) * (y2 - y)
             + v21 * (x - x1) * (y2 - y)
             + v12 * (x2 - x) * (y - y1)
             + v22 * (x - x1) * (y - y1)
             ) / ((x2 - x1) * (y2 - y1))
    if value is not None and value == raster.sourceNoDataValue(1):
        return None
    return value


def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt(math.pow(x1-x2, 2) + math.pow(y1-y2, 2))


def get_doc_file(file_path: str):

    path = Path(file_path)

    file = "{}.help".format(path.stem)

    help_file = path.parent.parent / "doc" / file

    if help_file.exists():
        with open(help_file) as f:
            descriptions = json.load(f)

        return descriptions

    return ""


def log(text):
    QgsMessageLog.logMessage(str(text),
                             "los_tools",
                             Qgis.Info)