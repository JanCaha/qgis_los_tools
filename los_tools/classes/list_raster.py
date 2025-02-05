import math
import pathlib
import typing
from typing import Dict, List, Optional, Tuple

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
from qgis.PyQt.QtCore import QFile, QIODevice
from qgis.PyQt.QtXml import QDomDocument

from los_tools.constants.plugin import PluginConstants
from los_tools.processing.tools.util_functions import bilinear_interpolated_value


class ListOfRasters:

    def __init__(self, rasters: List[QgsMapLayer]):

        self._dict_rasters: Dict[str, QgsRasterLayer] = {}

        if rasters:
            first_crs = rasters[0].crs()

            for raster in rasters:
                if not isinstance(raster, QgsRasterLayer):
                    raise ValueError("All inputs must be QgsRasterLayer.")
                if not first_crs == raster.crs():
                    raise ValueError("All CRS must be equal.")

                self._dict_rasters[raster.id()] = raster

            self.order_by_pixel_size()

    def __len__(self):
        return len(self._dict_rasters)

    def __repr__(self):
        return f"ListOfRasters: [{", ".join([x.name() for x in self.rasters])}]"

    def raster_to_use(self) -> str:
        return ", ".join([x.name() for x in self.rasters])

    @property
    def rasters(self) -> List[QgsRasterLayer]:
        return list(self._dict_rasters.values())

    @property
    def raster_ids(self) -> List[str]:
        return list(self._dict_rasters.keys())

    def remove_raster(self, raster_id: str) -> None:
        if raster_id in self._dict_rasters:
            self._dict_rasters.pop(raster_id)

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
            tuples.append((raster.id(), raster.extent().width() / raster.width(), raster))

        sorted_by_cell_size = sorted(tuples, key=lambda tup: tup[1])

        self._dict_rasters = {}

        for x in sorted_by_cell_size:
            self._dict_rasters[x[0]] = x[2]

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

    def save_to_file(self, file_path: str) -> typing.Tuple[bool, str]:
        """Saves configuration to XML file. Result is a tuple with success status and message."""

        path = pathlib.Path(file_path)
        if path.suffix.lower() != PluginConstants.rasters_xml_extension:
            file_path = path.with_suffix(PluginConstants.rasters_xml_extension).as_posix()

        doc = QDomDocument()

        root = doc.createElement("ListOfRasters")

        doc.appendChild(root)

        for raster in self.rasters:
            relative_path = pathlib.Path(raster.source()).relative_to(pathlib.Path(file_path).parent)

            raster_element = doc.createElement("raster")
            raster_element.setAttribute("dataProvider", raster.dataProvider().name())
            raster_element.setAttribute("name", raster.name())
            raster_element.setAttribute("path", relative_path)
            raster_element.setAttribute("crs", raster.crs().authid())
            raster_element.setAttribute("cellsWidth", raster.width())
            raster_element.setAttribute("cellsHeight", raster.height())
            raster_element.setAttribute("extentWidth", raster.extent().width())
            raster_element.setAttribute("extentHeight", raster.extent().height())

            root.appendChild(raster_element)

        file = QFile(file_path)
        if file.open(QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Text):
            bytes_written = file.write(doc.toByteArray())
            if bytes_written == -1:
                file.close()
                return False, f"Could not write to file `{file_path}`."
            file.close()

        return True, f"Configuration saved to `{file_path}`."

    def read_from_file(self, file_path: str) -> typing.Tuple[bool, str]:

        self._dict_rasters = {}

        file = QFile(file_path)
        if not file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
            return False, f"Could not open file `{file_path}`."

        doc = QDomDocument()
        if not doc.setContent(file):
            file.close()
            return False, f"Could not read content of file `{file_path}`."
        file.close()

        root = doc.documentElement()
        if root.tagName() != "ListOfRasters":
            return False, f"File `{file_path}` is not a valid {PluginConstants.rasters_xml_name} file."

        items = root.elementsByTagName("raster")

        load_messages = []
        for i in range(items.length()):
            item = items.item(i).toElement()

            raster_path = item.attribute("path")
            if not pathlib.Path(raster_path).exists():
                continue

            raster_path = pathlib.Path(file_path).parent / raster_path

            raster = QgsRasterLayer(raster_path.as_posix(), item.attribute("name"), item.attribute("dataProvider"))
            if not raster.isValid():
                continue

            if not (
                raster.crs().authid() == item.attribute("crs")
                and raster.width() == int(item.attribute("cellsWidth"))
                and raster.height() == int(item.attribute("cellsHeight"))
                and raster.extent().width() == float(item.attribute("extentWidth"))
                and raster.extent().height() == float(item.attribute("extentHeight"))
            ):
                load_messages.append(f"Raster `{raster.name()}` does not fit with definition in the file.")

            self._dict_rasters[raster.id()] = raster

        self.order_by_pixel_size()

        return True, ",".join(load_messages)
