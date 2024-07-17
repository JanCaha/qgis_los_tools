import numpy as np
from osgeo import gdal
from processing.core.Processing import Processing
from qgis.core import QgsPointXY, QgsRasterLayer, QgsVectorLayer

from los_tools.processing.tools.tool_replace_raster_values_by_constant import (
    ReplaceRasterValuesByConstantValueAlgorithm,
)
from tests.custom_assertions import assert_algorithm, assert_parameter, assert_run
from tests.utils import result_filename


def test_parameters() -> None:
    alg = ReplaceRasterValuesByConstantValueAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("RasterLayer"), "raster")
    assert_parameter(alg.parameterDefinition("VectorLayer"), "source")
    assert_parameter(alg.parameterDefinition("RasterValue"), "number")
    assert_parameter(alg.parameterDefinition("OutputRaster"), "rasterDestination")


def test_alg_settings() -> None:
    alg = ReplaceRasterValuesByConstantValueAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_run_alg(raster_small: QgsRasterLayer, layer_polygons: QgsVectorLayer):
    Processing.initialize()

    alg = ReplaceRasterValuesByConstantValueAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("raster.tif")

    params = {
        "RasterLayer": raster_small,
        "VectorLayer": layer_polygons,
        "RasterValue": -100,
        "OutputRaster": output_path,
    }

    assert_run(alg, params)

    raster_new = QgsRasterLayer(output_path, "new raster", "gdal")

    points = [
        QgsPointXY(-336484.00, -1189103.24),
        QgsPointXY(-336378.35, -1189152.49),
        QgsPointXY(-336510.77, -1189168.83),
        QgsPointXY(-336391.02, -1189095.07),
        QgsPointXY(-336352.81, -1189095.48),
    ]

    for point in points:
        assert raster_small.dataProvider().sample(point, 1) == raster_new.dataProvider().sample(point, 1)

    points = [
        QgsPointXY(-336478.89, -1189048.48),
        QgsPointXY(-336421.47, -1189091.80),
        QgsPointXY(-336324.40, -1189098.54),
        QgsPointXY(-336340.34, -1189116.73),
        QgsPointXY(-336469.297, -1189033.700),
    ]

    for point in points:
        new_value, _ = raster_new.dataProvider().sample(point, 1)
        assert raster_small.dataProvider().sample(point, 1) != new_value
        assert new_value == -100
