from typing import List, Tuple, Optional
import math

from qgis.core import (QgsMapLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,
                       QgsRasterDataProvider, QgsRectangle, QgsPoint, QgsLineString)

from los_tools.tools.util_functions import bilinear_interpolated_value


class ListOfRasters:

    rasters_dp: List[QgsRasterDataProvider]

    def __init__(self, rasters: List[QgsMapLayer]):

        for raster in rasters:
            if not isinstance(raster, QgsRasterLayer):
                raise ValueError("All inputs must be QgsRasterLayer.")

        self.rasters = rasters

        self.order_by_pixel_size()

    def validate_bands(self) -> Tuple[bool, str]:

        for raster in self.rasters:

            dem_band_count = raster.bandCount()

            if dem_band_count != 1:

                msg = f"Rasters can only have one band. Currently there are rasters with `{dem_band_count}` bands."

                return False, msg

        return True, ""

    def validate_crs(self, crs: QgsCoordinateReferenceSystem) -> Tuple[bool, str]:

        for raster in self.rasters:

            if not raster.crs() == crs:

                msg = "`Observers point layer` and raster layers crs must be equal. " \
                    "Right now they are not."

                return False, msg

        return True, ""

    def order_by_pixel_size(self) -> None:

        tuples = []

        for raster in self.rasters:

            tuples.append((raster, raster.extent().width() / raster.width()))

        sorted_by_cell_size = sorted(tuples, key=lambda tup: tup[1])

        self.rasters = [x[0] for x in sorted_by_cell_size]
        self.rasters_dp = [x[0].dataProvider() for x in sorted_by_cell_size]

    def maximal_diagonal_size(self) -> float:

        extent: QgsRectangle = None

        for raster in self.rasters:

            if extent is None:

                extent = raster.extent()

            else:

                extent.combineExtentWith(raster.extent())

        return math.sqrt(math.pow(extent.width(), 2) + math.pow(extent.height(), 2))

    def extract_interpolated_value(self, point: QgsPoint) -> Optional[float]:

        for raster_dp in self.rasters_dp:

            value = bilinear_interpolated_value(raster_dp, point)

            if value is not None:
                return value

        return None

    def add_z_values(self, points: List[QgsPoint]) -> QgsLineString:

        points3d = []

        for point in points:

            z = self.extract_interpolated_value(point)

            if z is not None:
                points3d.append(QgsPoint(point.x(), point.y(), z))

        return QgsLineString(points3d)
