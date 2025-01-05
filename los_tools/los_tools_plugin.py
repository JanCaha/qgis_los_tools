import inspect
import os
import re
import sys
import typing
from functools import partial

from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsMemoryProviderUtils,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgisInterface
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolBar, QToolButton

from los_tools.classes.list_raster import ListOfRasters
from los_tools.processing.los_tools_provider import LoSToolsProvider

from .constants.fields import Fields
from .constants.plugin import PluginConstants
from .gui._3d.dialog_create_3d_view import Create3DView
from .gui._3d.dialog_tool_set_camera import SetCameraDialog
from .gui.create_los_tool.create_los_tool import CreateLoSMapTool
from .gui.dialog_los_settings import LoSSettings
from .gui.dialog_object_parameters import ObjectParameters
from .gui.dialog_raster_validations import RasterValidations
from .gui.los_without_target_visualization.los_without_target import LosNoTargetMapTool
from .gui.optimize_point_location_tool.optimize_points_location_tool import OptimizePointsLocationTool
from .utils import get_icon_path

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class LoSToolsPlugin:

    los_notarget_action_name = "Visualize LoS No Target Tool"
    optimize_point_location_action_name = "Optimize Point Location Tool"
    create_los_action_name = "Create LoS"

    rasters_for_los: ListOfRasters = None

    def __init__(self, iface: QgisInterface):
        self.add_los_layer_action: QAction = None
        self._layer_LoS: QgsVectorLayer = None

        self.iface: QgisInterface = iface
        self.provider = LoSToolsProvider()

        self.actions: typing.List[QAction] = []
        self.menu = PluginConstants.plugin_name

        if self.iface is not None:
            self.toolbar: QToolBar = self.iface.addToolBar(PluginConstants.plugin_toolbar_name)
            self.toolbar.setObjectName(PluginConstants.plugin_toolbar_name)

            self.iface.newProjectCreated.connect(self.project_updated)
            self.iface.projectRead.connect(self.project_updated)
            self.iface.projectRead.connect(self.reset_los_layer)

    def project_updated(self) -> None:
        self.current_project_visible_raster_layers()
        project = QgsProject.instance()
        project.layersRemoved.connect(self.update_list_of_rasters)

    def update_list_of_rasters(self, list_of_ids: typing.List[str]):
        selected_ids = []

        if self.rasters_for_los:
            selected_ids = self.rasters_for_los.raster_layer_ids()

        for id in list_of_ids:
            if id in selected_ids:
                self.rasters_for_los.remove_raster(id)

    def initProcessing(self):
        QgsApplication.processingRegistry().addProvider(self.provider)

    def current_project_visible_raster_layers(self) -> None:
        layers = []
        all_layers = QgsProject.instance().mapLayers(True)
        layer_tree_root = QgsProject.instance().layerTreeRoot()
        for layer_id in all_layers.keys():
            layer = QgsProject.instance().mapLayer(layer_id)
            if isinstance(layer, QgsRasterLayer):
                tree_layer = layer_tree_root.findLayer(layer_id)
                if tree_layer.isVisible():
                    layers.append(layer)

        self.rasters_for_los = ListOfRasters(layers)

    def initGui(self):
        self.initProcessing()

        if self.iface is not None:
            self.los_settings_dialog = LoSSettings(self.iface.mainWindow())
            self.object_parameters_dialog = ObjectParameters(self.iface.mainWindow())

            self.current_project_visible_raster_layers()

            self.add_los_layer_action = self.add_action(
                icon_path=get_icon_path("add_los_layer.svg"),
                text="Add Plugin Layer To Project",
                callback=self.add_plugin_los_layer_to_project,
                add_to_toolbar=False,
            )
            self.add_los_layer_action.setEnabled(True)

            self.empty_los_layer_action = self.add_action(
                icon_path=get_icon_path("remove_los_layer.svg"),
                text="Empty LoS Layer Features",
                callback=self.reset_los_layer,
                add_to_toolbar=False,
            )

            toolButton = QToolButton()
            toolButton.setText("LoS Layer")
            toolButton.setIcon(QIcon(get_icon_path("los_layer_menu.svg")))
            menu = QMenu()
            toolButton.setMenu(menu)
            toolButton.setPopupMode(QToolButton.MenuButtonPopup)
            menu.addAction(self.add_los_layer_action)
            menu.addAction(self.empty_los_layer_action)
            self.toolbar.addWidget(toolButton)

            self.add_action(
                icon_path=get_icon_path("los_tools_icon.svg"),
                text=self.create_los_action_name,
                callback=self.run_create_los_tool,
                add_to_toolbar=False,
                add_to_specific_toolbar=self.toolbar,
                checkable=True,
            )

            self.toolbar.addSeparator()

            self.add_action(
                icon_path=get_icon_path("calculator.svg"),
                text="Object Visibility Parameters",
                callback=self.open_dialog_object_visibility_parameters,
                add_to_toolbar=False,
                add_to_specific_toolbar=self.toolbar,
                checkable=True,
            )

            self.add_action(
                icon_path=get_icon_path("los_settings.svg"),
                text="Calculate Notarget Los Settings",
                callback=self.open_dialog_los_settings,
                add_to_toolbar=False,
                add_to_specific_toolbar=self.toolbar,
            )

            self.add_action(
                icon_path=get_icon_path("rasters_list.svg"),
                text="Raster Validations",
                callback=self.dialog_raster_selection,
                add_to_toolbar=False,
                add_to_specific_toolbar=self.toolbar,
            )

            self.add_action(
                icon_path=get_icon_path("camera.svg"),
                text="Create 3D View with Camera Setup",
                callback=self.dialog_create_3d_view,
                add_to_toolbar=False,
                add_to_specific_toolbar=self.toolbar,
                checkable=False,
            )

            self.toolbar.addSeparator()

            self.add_action(
                icon_path=get_icon_path("los_no_target_tool.svg"),
                text=self.los_notarget_action_name,
                callback=self.run_visualize_los_notarget_tool,
                add_to_toolbar=False,
                add_to_specific_toolbar=self.toolbar,
                checkable=True,
            )

            self.add_action(
                icon_path=get_icon_path("optimize_point.svg"),
                text=self.optimize_point_location_action_name,
                callback=self.run_optimize_point_location_tool,
                add_to_toolbar=False,
                add_to_specific_toolbar=self.toolbar,
                checkable=True,
            )

            self.toolbar.addSeparator()

            self.add_action(
                icon_path=get_icon_path("camera_layout_item.svg"),
                text="Set Camera to Layout 3D Map",
                callback=self.run_tool_set_camera,
                add_to_toolbar=False,
                add_to_specific_toolbar=self.toolbar,
            )

            self.los_notarget_tool = LosNoTargetMapTool(self.iface)
            self.los_notarget_tool.deactivated.connect(partial(self.deactivateTool, self.los_notarget_action_name))

            self.optimize_point_location_tool = OptimizePointsLocationTool(self.iface.mapCanvas(), self.iface)
            self.optimize_point_location_tool.deactivated.connect(
                partial(self.deactivateTool, self.optimize_point_location_action_name)
            )

            self.create_los_tool = CreateLoSMapTool(
                self.iface,
                self.rasters_for_los,
                self.los_settings_dialog,
                self._layer_LoS,
            )

            self.create_los_tool.deactivated.connect(partial(self.deactivateTool, self.create_los_action_name))
            self.create_los_tool.featuresAdded.connect(self.update_actions_layer_text)

            self.reset_los_layer()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)

        if self.iface is not None:
            for action in self.actions:
                self.iface.removePluginMenu(PluginConstants.plugin_name, action)
                self.iface.removeToolBarIcon(action)

            del self.toolbar

            self._layer_LoS = None

    def add_action(
        self,
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
        checkable: bool = False,
    ):
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
        dialog = SetCameraDialog(self.iface, self.iface.mainWindow())
        dialog.exec()

    def open_dialog_los_settings(self):
        self.los_settings_dialog.exec()

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

    def run_create_los_tool(self):
        self.get_action_by_text(self.create_los_action_name).setChecked(True)
        self.create_los_tool.set_list_of_rasters(self.rasters_for_los)
        self.iface.mapCanvas().setMapTool(self.create_los_tool)

    def _plugin_los_layer(self) -> QgsVectorLayer:
        if self._layer_LoS is None:
            selected_crs: QgsCoordinateReferenceSystem = self.iface.mapCanvas().mapSettings().destinationCrs()

            if selected_crs.isGeographic():
                selected_crs = QgsCoordinateReferenceSystem.fromEpsgId(3857)

            return QgsMemoryProviderUtils.createMemoryLayer(
                "Manually Created LoS",
                Fields.los_plugin_layer_fields,
                QgsWkbTypes.LineString25D,
                selected_crs,
            )

        return self._layer_LoS

    def reset_los_layer(self) -> None:
        self._layer_LoS = None
        self._layer_LoS = self._plugin_los_layer()
        self.create_los_tool.set_los_layer(self._layer_LoS)
        self.update_actions_layer_text()

    def add_plugin_los_layer_to_project(self) -> None:
        if self._layer_LoS:
            QgsProject.instance().addMapLayer(self._layer_LoS)
            self.reset_los_layer()
            self.create_los_tool.set_los_layer(self._layer_LoS)

    def update_actions_layer_text(self) -> None:
        self.update_action_number_features_text(self.empty_los_layer_action)
        self.update_action_number_features_text(self.add_los_layer_action)

    def update_action_number_features_text(self, action: QAction) -> None:
        text = action.text()
        pattern = r"\([0-9]+ feature/s\)"
        text_part = f"({self._layer_LoS.dataProvider().featureCount()} feature/s)"
        match = re.search(pattern, text)
        if match:
            text = re.sub(pattern, text_part, text)
        else:
            text = f"{text} {text_part}"
        action.setText(text)

    def open_dialog_object_visibility_parameters(self) -> None:
        self.object_parameters_dialog.exec()

    def dialog_create_3d_view(self):
        dialog = Create3DView(self.iface, self.iface.mainWindow())
        dialog.exec()

    def dialog_raster_selection(self):
        raster_validations = RasterValidations(iface=self.iface)
        raster_validations.selectedRastersChanged.connect(partial(self.get_rasters_for_los, raster_validations))
        if self.rasters_for_los:
            raster_validations.setup_used_rasters(self.rasters_for_los)
        raster_validations.selectedRastersChanged.connect(self.list_of_rasters_for_los_updated)
        raster_validations.exec()

    def get_rasters_for_los(self, raster_validations: RasterValidations) -> None:
        if raster_validations:
            self.rasters_for_los = raster_validations.listOfRasters

    def list_of_rasters_for_los_updated(self):
        self.create_los_tool.set_list_of_rasters(self.rasters_for_los)
        self.create_los_tool.reactivate()
