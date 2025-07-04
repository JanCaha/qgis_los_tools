import pathlib
import typing

from qgis.core import QgsDataItem, QgsDataItemProvider, QgsDataProvider, QgsMimeDataUtils, QgsProject
from qgis.gui import QgsCustomDropHandler
from qgis.PyQt.QtCore import QDir
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox

from los_tools.classes.list_raster import ListOfRasters
from los_tools.constants.plugin import PluginConstants
from los_tools.utils import get_icon_path


def is_path_rasters_xml_json(path: typing.Union[str, pathlib.Path]) -> bool:
    """Check if a path is a RastersXML file"""
    path = pathlib.Path(path)
    if path.suffix.lower() == PluginConstants.rasters_xml_extension:
        return True
    return False


def load_raster_xml(path: str, plugin) -> bool:
    list_of_rasters = ListOfRasters([])
    list_of_rasters.read_from_file(path)

    if len(list_of_rasters) > 0:
        message_box_load = QMessageBox()
        message_box_load.setIcon(QMessageBox.Question)
        message_box_load.setWindowTitle("Load Rasters from file?")
        message_box_load.setText(f"Would you like to load {len(list_of_rasters)} the rasters from the file `{path}`?")
        message_box_load.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        message_box_load.setDefaultButton(QMessageBox.No)
        res = message_box_load.exec()
        if res == QMessageBox.Yes:
            project = QgsProject.instance()
            rasters = list_of_rasters.rasters
            for raster in reversed(rasters):
                project.addMapLayer(raster)
        else:
            return False
    else:
        QMessageBox.information(None, "No Valid Raster in File", f"There are no valid rasters in the file `{path}`.")
        return False

    plugin._list_of_rasters_for_los = list_of_rasters

    return True


class RastersXMLDropHandler(QgsCustomDropHandler):
    """
    Rasters XML file drop handler
    """

    def __init__(self, plugin) -> None:
        super().__init__()
        self.plugin = plugin

    def handleFileDrop(self, file: str | None):  # pylint: disable=missing-docstring
        if file:
            if not is_path_rasters_xml_json(file):
                return False
            return True
        return False

    def handleCustomUriDrop(self, uri: QgsMimeDataUtils.Uri) -> None:
        if uri.uri:
            load_raster_xml(uri.uri, self.plugin)

        return super().handleCustomUriDrop(uri)

    def customUriProviderKey(self) -> str:
        return PluginConstants.rasters_xml_providerkey


class RastersXMLItemProvider(QgsDataItemProvider):
    """
    Data item provider for Rasters XML files
    """

    def __init__(self, plugin):
        super().__init__()
        self.plugin = plugin

    def name(self):  # pylint: disable=missing-docstring
        return PluginConstants.rasters_xml_name

    def capabilities(self):  # pylint: disable=missing-docstring
        return QgsDataProvider.File

    def createDataItem(self, path: str | None, parentItem):  # pylint: disable=missing-docstring

        if path:
            if is_path_rasters_xml_json(path):
                return RastersXMLItem(parentItem, pathlib.Path(path).name, path, self.plugin)

        return None


class RastersXMLItem(QgsDataItem):
    """
    Data item for RastersXML file
    """

    def __init__(self, parent, name, path, plugin):
        self.plugin = plugin
        super().__init__(QgsDataItem.Custom, parent, name, path)
        self.setState(QgsDataItem.Populated)  # no children
        self.setToolTip(QDir.toNativeSeparators(path))

    def hasDragEnabled(self):  # pylint: disable=missing-docstring
        return True

    def handleDoubleClick(self):  # pylint: disable=missing-docstring
        self._open_file()
        return True

    def mimeUri(self):  # pylint: disable=missing-docstring
        u = QgsMimeDataUtils.Uri()
        u.layerType = "custom"
        u.providerKey = PluginConstants.rasters_xml_providerkey
        u.name = self.name()
        u.uri = self.path()
        return u

    def mimeUris(self):  # pylint: disable=missing-docstring
        return [self.mimeUri()]

    def _open_file(self):
        """Handles opening Rasters XML file"""
        return load_raster_xml(self.path(), self.plugin)

    def actions(self, parent):  # pylint: disable=missing-docstring
        open_action = QAction(f"&Open {PluginConstants.rasters_xml_name}…", parent)
        open_action.triggered.connect(self._open_file)
        return [open_action]

    def icon(self) -> QIcon:
        return QIcon(get_icon_path("rasters_list.svg"))
