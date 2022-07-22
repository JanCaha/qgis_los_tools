from typing import List, Tuple, Optional
import math

from qgis.core import (QgsMapLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,
                       QgsRasterDataProvider, QgsRectangle, QgsPoint, QgsLineString,
                       qgsDoubleNearSig)

from los_tools.tools.util_functions import bilinear_interpolated_value


class ListOfRasters:

    def __init__(self, rasters: List[QgsMapLayer]):

        first_crs = rasters[0].crs()

        for raster in rasters:
            if not isinstance(raster, QgsRasterLayer):
                raise ValueError("All inputs must be QgsRasterLayer.")
            if not first_crs == raster.crs():
                raise ValueError("All CRS must be equal.")

        self.rasters = rasters

        self.order_by_pixel_size()

    @staticmethod
    def validate_bands(rasters: List[QgsMapLayer]) -> Tuple[bool, str]:

        for raster in rasters:

            dem_band_count = raster.bandCount()

            if dem_band_count != 1:

                msg = f"Rasters can only have one band. Currently there are rasters with `{dem_band_count}` bands."

                return False, msg

        return True, ""

    @staticmethod
    def validate_crs(rasters: List[QgsMapLayer],
                     crs: QgsCoordinateReferenceSystem) -> Tuple[bool, str]:

        first_raster_crs = rasters[0].crs()

        for raster in rasters:

            if not first_raster_crs == raster.crs():

                msg = "All CRS for all rasters must be equal. " \
                    "Right now they are not."

                return False, msg

            if not raster.crs() == crs:

                msg = "Provided crs template and raster layers crs must be equal. " \
                    "Right now they are not."

                return False, msg

        return True, ""

    @staticmethod
    def validate_ordering(rasters: List[QgsMapLayer]) -> Tuple[bool, str]:

        values: List[float] = []

        for raster in rasters:

            values.append(raster.extent().width() / raster.width())

        if len(rasters) != len(set(values)):

            return False, "Raster cell sizes must be unique to form complete ordering. " \
                          "Rasters are order strictly by cell size, same cell size for multiple rasters does not allow strict ordering. " \
                          f"The values [{','.join([str(x) for x in values])}] are not unique."

        return True, ""

    @staticmethod
    def validate_square_cell_size(rasters: List[QgsMapLayer]) -> Tuple[bool, str]:

        for raster in rasters:

            xres = raster.extent().width() / raster.width()
            yres = raster.extent().height() / raster.height()

            if qgsDoubleNearSig(xres, yres, significantDigits=3):

                return False, "Rasters have to have square cells. "\
                    f"Right now they are not squared for `{raster.name()}`."

        return True, ""

    def order_by_pixel_size(self) -> None:

        tuples = []

        for raster in self.rasters:

            tuples.append((raster, raster.extent().width() / raster.width()))

        sorted_by_cell_size = sorted(tuples, key=lambda tup: tup[1])

        self.rasters = [x[0] for x in sorted_by_cell_size]

    @property
    def rasters_dp(self) -> List[QgsRasterDataProvider]:
        return [x.dataProvider() for x in self.rasters]

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
