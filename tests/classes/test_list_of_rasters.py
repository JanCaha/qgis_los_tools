from qgis.core import (QgsRasterLayer, QgsVectorLayer, QgsRasterDataProvider, QgsPoint)

from los_tools.classes.list_raster import ListOfRasters
from los_tools.constants.field_names import FieldNames

from tests.AlgorithmTestCase import QgsProcessingAlgorithmTestCase
from tests.utils_tests import (get_data_path)


class ListOfRastersTest(QgsProcessingAlgorithmTestCase):

    def setUp(self) -> None:

        super().setUp()

        self.raster_small = QgsRasterLayer(get_data_path("dsm.tif"))

        self.raster_large = QgsRasterLayer(get_data_path("srtm.tif"))

        self.raster_wrong_crs = QgsRasterLayer(get_data_path("dsm_epsg_5514.tif"))

        self.vector = QgsVectorLayer(get_data_path("los_local.gpkg"))

    def test_create_object(self):

        list_rasters = ListOfRasters([self.raster_small, self.raster_large])

        self.assertIsInstance(list_rasters, ListOfRasters)

        self.assertIsInstance(list_rasters.rasters, list)
        self.assertIsInstance(list_rasters.rasters_dp, list)
        self.assertIsInstance(list_rasters.rasters[0], QgsRasterLayer)
        self.assertIsInstance(list_rasters.rasters_dp[0], QgsRasterDataProvider)

        with self.assertRaisesRegex(ValueError, "All inputs must be QgsRasterLayer"):
            list_rasters = ListOfRasters([self.raster_small, self.raster_large, self.vector])

        with self.assertRaisesRegex(ValueError, "All CRS must be equal"):
            list_rasters = ListOfRasters(
                [self.raster_small, self.raster_large, self.raster_wrong_crs])

    def test_maximal_diagonal_size(self):

        list_rasters = ListOfRasters([self.raster_small, self.raster_large])

        self.assertEqual(list_rasters.maximal_diagonal_size(), 0)

    def test_extract_interpolated_value(self):

        list_rasters = ListOfRasters([self.raster_small, self.raster_large])

        point_1 = QgsPoint(-336332.2, -1189104.8)
        point_2 = QgsPoint(-337045.6, -1188775.2)
        point_3 = QgsPoint(-334597.8840, -1187659.5597)

        self.assertEqual(list_rasters.extract_interpolated_value(point_1), 1007.409252288644)
        self.assertEqual(list_rasters.extract_interpolated_value(point_2), 1076.6832007948944)
        self.assertIsNone(list_rasters.extract_interpolated_value(point_3))
