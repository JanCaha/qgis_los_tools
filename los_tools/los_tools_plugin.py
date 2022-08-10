import os
import sys
import inspect
from functools import partial

from qgis.core import QgsApplication
from qgis.gui import QgisInterface

from qgis.PyQt.QtGui import (QIcon)
from qgis.PyQt.QtWidgets import (QAction, QToolBar)

from .los_tools_provider import los_toolsProvider
from .gui.dialog_tool_set_camera import SetCameraTool
from .gui.dialog_los_settings import LoSSettings
from .gui.dialog_raster_validations import RasterValidations
from .constants.plugin import PluginConstants
from .utils import get_icon_path
from .gui.los_without_target import LosNoTargetMapTool
from .gui.optimize_points_location import OptimizePointsLocationTool

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class los_toolsPlugin():

    camera_tool: SetCameraTool = None

    los_notarget_action_name = "Visualize LoS No Target Tool"
    optimize_point_location_action_name = "Optimize Point Location Tool"

    def __init__(self, iface):

        self.iface: QgisInterface = iface
        self.provider = los_toolsProvider()

        self.actions = []
        self.menu = PluginConstants.plugin_name

        self.toolbar: QToolBar = self.iface.addToolBar(PluginConstants.plugin_toolbar_name)
        self.toolbar.setObjectName(PluginConstants.plugin_toolbar_name)

        self.raster_validations_dialog = RasterValidations(iface=self.iface)
        self.los_settings_dialog = LoSSettings(self.iface.mainWindow())

        self.los_notarget_tool = LosNoTargetMapTool(self.iface)
        self.los_notarget_tool.deactivated.connect(
            partial(self.deactivateTool, self.los_notarget_action_name))

        self.optimize_point_location_tool = OptimizePointsLocationTool(
            self.iface.mapCanvas(), self.iface)
        self.optimize_point_location_tool.deactivated.connect(
            partial(self.deactivateTool, self.optimize_point_location_action_name))

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
                        callback=self.open_dialog_los_settings,
                        add_to_toolbar=False,
                        add_to_specific_toolbar=self.toolbar)

        self.add_action(icon_path=get_icon_path("rasters_list.svg"),
                        text="Raster Validatations",
                        callback=self.open_dialog_raster_validations,
                        add_to_toolbar=False,
                        add_to_specific_toolbar=self.toolbar)

        self.add_action(icon_path=get_icon_path("los_no_target_tool.svg"),
                        text=self.los_notarget_action_name,
                        callback=self.run_visualize_los_notarget_tool,
                        add_to_toolbar=False,
                        add_to_specific_toolbar=self.toolbar,
                        checkable=True)

        self.add_action(icon_path=None,
                        text=self.optimize_point_location_action_name,
                        callback=self.run_optimize_point_location_tool,
                        add_to_toolbar=False,
                        add_to_specific_toolbar=self.toolbar,
                        checkable=True)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)

        for action in self.actions:
            self.iface.removePluginMenu(PluginConstants.plugin_name, action)
            self.iface.removeToolBarIcon(action)

        del self.toolbar

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
                   add_to_specific_toolbar: QToolBar = None,
                   checkable: bool = False):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        if checkable:
            action.setCheckable(True)

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

    def open_dialog_los_settings(self):
        self.los_settings_dialog.exec()

    def open_dialog_raster_validations(self):
        self.raster_validations_dialog.exec()

    def run_visualize_los_notarget_tool(self):
        self.get_action_by_text(self.los_notarget_action_name).setChecked(True)
        self.iface.mapCanvas().setMapTool(self.los_notarget_tool)

    def get_action_by_text(self, action_text: str) -> QAction:
        action: QAction
        for action in self.actions:
            if action.text() == action_text:
                return action

    def deactivateTool(self, action_name: str):
        self.get_action_by_text(action_name).setChecked(False)

    def run_optimize_point_location_tool(self):
        self.get_action_by_text(self.optimize_point_location_action_name).setChecked(True)
        self.iface.mapCanvas().setMapTool(self.optimize_point_location_tool)
