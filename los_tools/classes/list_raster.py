import math
from typing import List, Optional, Tuple

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsCoordinateTransformContext,
    QgsGeometry,
    QgsLineString,
    QgsMapLayer,
    QgsPoint,
    QgsPointXY,
    QgsRasterDataProvider,
    QgsRasterLayer,
    QgsRectangle,
    qgsFloatNear,
)

from los_tools.processing.tools.util_functions import bilinear_interpolated_value


class ListOfRasters:
    def __init__(self, rasters: List[QgsMapLayer]):
        self.rasters: List[QgsRasterLayer] = []

        if rasters:
            first_crs = rasters[0].crs()

            for raster in rasters:
                if not isinstance(raster, QgsRasterLayer):
                    raise ValueError("All inputs must be QgsRasterLayer.")
                if not first_crs == raster.crs():
                    raise ValueError("All CRS must be equal.")

                self.rasters.append(raster)

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
    def validate_crs(rasters: List[QgsMapLayer], crs: QgsCoordinateReferenceSystem = None) -> Tuple[bool, str]:
        if crs is None:
            crs = rasters[0].crs()

        first_raster_crs = rasters[0].crs()

        for raster in rasters:
            if not first_raster_crs == raster.crs():
                msg = "All CRS for all rasters must be equal. Right now they are not."

                return False, msg

            if not raster.crs() == crs:
                msg = "Provided crs template and raster layers crs must be equal. Right now they are not."

                return False, msg

        return True, ""

    @staticmethod
    def validate_ordering(rasters: List[QgsMapLayer]) -> Tuple[bool, str]:
        values: List[float] = []

        for raster in rasters:
            values.append(raster.extent().width() / raster.width())

        if len(rasters) != len(set(values)):
            return (
                False,
                "Raster cell sizes must be unique to form complete ordering. "
                "Rasters are order strictly by cell size, "
                "same cell size for multiple rasters does not allow strict ordering. "
                f"The values [{','.join([str(x) for x in values])}] are not unique.",
            )

        return True, ""

    @staticmethod
    def validate_square_cell_size(rasters: List[QgsMapLayer]) -> Tuple[bool, str]:
        for raster in rasters:
            xres = raster.extent().width() / raster.width()
            yres = raster.extent().height() / raster.height()

            if not qgsFloatNear(xres, yres, epsilon=0.001):
                return (
                    False,
                    "Rasters have to have square cells. "
                    f"Right now they are not squared for `{raster.name()}` {xres} != {yres} .",
                )

        return True, ""

    @staticmethod
    def validate(rasters: List[QgsMapLayer]) -> bool:
        if not rasters:
            return False

        return (
            ListOfRasters.validate_crs(rasters)[0]
            and ListOfRasters.validate_bands(rasters)[0]
            and ListOfRasters.validate_ordering(rasters)[0]
            and ListOfRasters.validate_square_cell_size(rasters)[0]
        )

    def crs(self) -> QgsCoordinateReferenceSystem:
        return self.rasters[0].crs()

    def is_valid(self) -> bool:
        return (
            self.validate_crs(self.rasters)[0]
            and self.validate_bands(self.rasters)[0]
            and self.validate_ordering(self.rasters)[0]
            and self.validate_square_cell_size(self.rasters)[0]
        )

    def is_empty(self) -> bool:
        if self.rasters:
            return False
        return True

    def extent_polygon(self) -> QgsGeometry:
        geoms = []
        for raster in self.rasters:
            geoms.append(QgsGeometry.fromRect(raster.extent()))
        return QgsGeometry.unaryUnion(geoms)

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
        extent: Optional[QgsRectangle] = None

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

    def _convert_point_to_crs_of_raster(self, point: QgsPointXY, crs: QgsCoordinateReferenceSystem) -> QgsPoint:
        if crs.toWkt() == self.rasters[0].crs().toWkt():
            return QgsPoint(point.x(), point.y())

        transformer = QgsCoordinateTransform(crs, self.rasters[0].crs(), QgsCoordinateTransformContext())
        geom = QgsGeometry.fromPointXY(point)
        geom.transform(transformer)
        transformed_point = geom.asPoint()
        return QgsPoint(transformed_point.x(), transformed_point.y())

    def extract_interpolated_value_at_point(self, point: QgsPointXY, crs: QgsCoordinateReferenceSystem) -> float:
        return self.extract_interpolated_value(self._convert_point_to_crs_of_raster(point, crs))

    def sampling_from_raster_at_point(self, point: QgsPointXY, crs: QgsCoordinateReferenceSystem) -> str:
        point = self._convert_point_to_crs_of_raster(point, crs)
        for i, raster_dp in enumerate(self.rasters_dp):
            value = bilinear_interpolated_value(raster_dp, point)
            if value is not None:
                return self.rasters[i].name()
        return None

    def add_z_values(self, points: List[QgsPoint]) -> QgsLineString:
        points3d = []

        for point in points:
            z = self.extract_interpolated_value(point)

            if z is not None:
                points3d.append(QgsPoint(point.x(), point.y(), z))

        return QgsLineString(points3d)
