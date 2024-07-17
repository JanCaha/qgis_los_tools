import numpy as np
from osgeo import gdal
from processing.core.Processing import Processing
from qgis.core import QgsPointXY, QgsProcessingParameterField, QgsRasterLayer, QgsVectorLayer

from los_tools.processing.tools.tool_replace_raster_values_by_field import ReplaceRasterValuesByFieldValuesAlgorithm
from tests.custom_assertions import assert_algorithm, assert_parameter, assert_run
from tests.utils import result_filename


def test_parameters() -> None:
    alg = ReplaceRasterValuesByFieldValuesAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("RasterLayer"), "raster")
    assert_parameter(alg.parameterDefinition("VectorLayer"), "source")
    assert_parameter(
        alg.parameterDefinition("ValueField"),
        "field",
        data_type=QgsProcessingParameterField.Numeric,
    )
    assert_parameter(alg.parameterDefinition("OutputRaster"), "rasterDestination")


def test_alg_settings() -> None:
    alg = ReplaceRasterValuesByFieldValuesAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_run_alg(raster_small: QgsRasterLayer, layer_polygons: QgsVectorLayer):
    Processing.initialize()

    alg = ReplaceRasterValuesByFieldValuesAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("raster.tif")

    params = {
        "RasterLayer": raster_small,
        "VectorLayer": layer_polygons,
        "ValueField": "height",
        "OutputRaster": output_path,
    }

    assert_run(alg, params)

    ds = gdal.Open(output_path)
    raster_array = ds.GetRasterBand(1).ReadAsArray()
    unique_values = np.unique(raster_array)

    assert 1200 in unique_values
    assert 1100 in unique_values
    assert 1050 in unique_values

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
        assert new_value in [1200.0, 1100.0, 1050.0]

    ds = None
