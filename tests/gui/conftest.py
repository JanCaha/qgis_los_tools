import pytest
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsMemoryProviderUtils,
    QgsPointXY,
    QgsRasterLayer,
    QgsVectorLayer,
)
from qgis.gui import QgsMapCanvas

from los_tools.classes.list_raster import ListOfRasters
from los_tools.classes.sampling_distance_matrix import SamplingDistanceMatrix
from los_tools.constants.fields import Fields


@pytest.fixture
def map_canvas_crs(qgis_canvas: QgsMapCanvas) -> QgsCoordinateReferenceSystem:
    crs = qgis_canvas.mapSettings().destinationCrs()
    return crs


@pytest.fixture(scope="function")
def los_layer(map_canvas_crs: QgsCoordinateReferenceSystem) -> QgsVectorLayer:
    return QgsMemoryProviderUtils.createMemoryLayer(
        "Manually Created LoS",
        Fields.los_plugin_layer_fields,
        Qgis.WkbType.LineString25D,
        map_canvas_crs,
    )


@pytest.fixture(scope="function")
def list_of_rasters(raster_small: QgsRasterLayer, raster_large: QgsRasterLayer) -> ListOfRasters:
    return ListOfRasters([raster_small, raster_large])


@pytest.fixture
def center_point(raster_small: QgsRasterLayer) -> QgsPointXY:
    return raster_small.extent().center()


@pytest.fixture
def sampling_distance_matrix() -> SamplingDistanceMatrix:
    sdm = SamplingDistanceMatrix()
    sdm.data = [[1.0, -1.0], [1.0, 0.0]]
    return sdm
