import typing

from qgis.core import (
    QgsAbstractTerrainProvider,
    QgsCoordinateReferenceSystem,
    QgsPoint,
    QgsProject,
    QgsReadWriteContext,
)
from qgis.PyQt.QtXml import QDomDocument, QDomElement

from los_tools.classes.list_raster import ListOfRasters


class RastersTerrainProvider(QgsAbstractTerrainProvider):
    def __init__(self, raster_files: ListOfRasters):
        QgsAbstractTerrainProvider.__init__(self)
        self._list_of_rasters = raster_files

    def readCommonProperties(self, element: QDomElement, context: QgsReadWriteContext) -> None:
        pass

    def writeCommonProperties(self, element: QDomElement, context: QgsReadWriteContext) -> None:
        pass

    def setOffset(self, offset: float) -> None:
        pass

    def offset(self) -> float:
        return 0.0

    def setScale(self, scale: float) -> None:
        pass

    def scale(self) -> float:
        return 0.0

    def heightAt(self, x: float, y: float) -> float:
        interpolated_value = self._list_of_rasters.extract_interpolated_value(QgsPoint(x, y))
        if interpolated_value is None:
            return 0
        return interpolated_value

    def crs(self) -> QgsCoordinateReferenceSystem:
        return self._list_of_rasters.crs()

    def prepare(self) -> None:
        pass

    def clone(self) -> typing.Optional[QgsAbstractTerrainProvider]:
        return RastersTerrainProvider(self._list_of_rasters)

    def type(self) -> str:
        return "RastersTerrainProvider"

    def writeXml(self, document: QDomDocument, context: QgsReadWriteContext) -> QDomElement:
        pass

    def readXml(self, element: QDomElement, context: QgsReadWriteContext) -> bool:
        pass

    def resolveReferences(self, project: typing.Optional[QgsProject]) -> None:
        pass

    def equals(self, other: typing.Optional[QgsAbstractTerrainProvider]) -> bool:
        return False
