import os
import sys
import inspect

from qgis.core import QgsApplication
from qgis.gui import QgisInterface

from qgis.PyQt.QtGui import (QIcon)
from qgis.PyQt.QtWidgets import (QAction)

from .los_tools_provider import los_toolsProvider
from .gui.dialog_tool_set_camera import SetCameraTool
from .gui.dialog_los_settings import LoSSettings
from .gui.dialog_raster_validations import RasterValidations
from .constants.plugin import PluginConstants
from .utils import get_icon_path

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class los_toolsPlugin():

    camera_tool: SetCameraTool = None

    def __init__(self, iface):

        self.iface: QgisInterface = iface
        self.provider = los_toolsProvider()

        self.actions = []
        self.menu = PluginConstants.plugin_name

        self.toolbar = self.iface.addToolBar(PluginConstants.plugin_toolbar_name)
        self.toolbar.setObjectName(PluginConstants.plugin_toolbar_name)

        self.rasterValidationsTool = RasterValidations(iface=self.iface)

    def initProcessing(self):
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

        self.add_action(icon_path=get_icon_path("camera.svg"),
                        text="Set Camera",
                        callback=self.run_tool_set_camera,
                        add_to_toolbar=False,
                        add_to_specific_toolbar=self.toolbar)

        self.add_action(icon_path=get_icon_path("los_tools_icon.svg"),
                        text="Calculate Notarget Los Settings",
                        callback=self.run_tool_los_settings,
                        add_to_toolbar=False,
                        add_to_specific_toolbar=self.toolbar)

        self.add_action(icon_path=None,
                        text="Raster Validatations",
                        callback=self.run_raster_validations,
                        add_to_toolbar=False,
                        add_to_specific_toolbar=self.toolbar)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)

        for action in self.actions:
            self.iface.removePluginMenu(PluginConstants.plugin_name, action)
            self.iface.removeToolBarIcon(action)

    def add_action(self,
                   icon_path,
                   text,
                   callback,
                   enabled_flag=True,
                   add_to_menu=True,
                   add_to_toolbar=True,
                   status_tip=None,
                   whats_this=None,
                   parent=None,
                   add_to_specific_toolbar=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        if add_to_specific_toolbar:
            add_to_specific_toolbar.addAction(action)

        self.actions.append(action)

        return action

    def run_tool_set_camera(self):
        if self.camera_tool is None:
            self.camera_tool = SetCameraTool(parent=self.iface.mainWindow(),
                                             canvas=self.iface.mapCanvas(),
                                             iface=self.iface)

        self.camera_tool.show()
        result = self.camera_tool.exec()

        if result == 1:
            self.camera_tool.update_camera_position()
        else:
            self.camera_tool.restore_canvas_tools()

    def run_tool_los_settings(self):
        tool = LoSSettings(self.iface.mainWindow())
        tool.exec()

    def run_raster_validations(self):
        self.rasterValidationsTool.exec()
