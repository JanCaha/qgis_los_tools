from processing.core.ProcessingConfig import ProcessingConfig, Setting
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from los_tools.constants.plugin import PluginConstants
from los_tools.constants.settings import Settings
from los_tools.processing.analyse_los.tool_analyse_los import AnalyseLosAlgorithm
from los_tools.processing.analyse_los.tool_extract_los_visibility_parts import ExtractLoSVisibilityPartsAlgorithm
from los_tools.processing.analyse_los.tool_extract_los_visibility_polygons import ExtractLoSVisibilityPolygonsAlgorithm
from los_tools.processing.analyse_los.tool_extract_points_los import ExtractPointsLoSAlgorithm
from los_tools.processing.azimuths.tool_azimuth import AzimuthPointPolygonAlgorithm
from los_tools.processing.azimuths.tool_limit_angles_vector import LimitAnglesAlgorithm
from los_tools.processing.create_los.tool_create_global_los import CreateGlobalLosAlgorithm
from los_tools.processing.create_los.tool_create_local_los import CreateLocalLosAlgorithm
from los_tools.processing.create_los.tool_create_notarget_los import CreateNoTargetLosAlgorithm
from los_tools.processing.create_points.tool_optimize_point_location import OptimizePointLocationAlgorithm
from los_tools.processing.create_points.tool_points_around import CreatePointsAroundAlgorithm
from los_tools.processing.create_points.tool_points_by_azimuths import CreatePointsInAzimuthsAlgorithm
from los_tools.processing.create_points.tool_points_in_direction import CreatePointsInDirectionAlgorithm
from los_tools.processing.horizons.tool_extract_horizon_lines import ExtractHorizonLinesAlgorithm
from los_tools.processing.horizons.tool_extract_horizon_lines_by_distances import ExtractHorizonLinesByDistanceAlgorithm
from los_tools.processing.horizons.tool_extract_horizons import ExtractHorizonsAlgorithm
from los_tools.processing.parameter_settings.tool_angle_at_distance_for_size import ObjectDetectionAngleAlgorithm
from los_tools.processing.parameter_settings.tool_distances_for_sizes import ObjectDistancesAlgorithm
from los_tools.processing.parameter_settings.tool_sizes_at_distances import ObjectSizesAlgorithm
from los_tools.processing.to_table.tool_export_horizon_lines import ExportHorizonLinesAlgorithm
from los_tools.processing.to_table.tool_export_los import ExportLoSAlgorithm
from los_tools.processing.tools.tool_replace_raster_values_by_constant import (
    ReplaceRasterValuesByConstantValueAlgorithm,
)
from los_tools.processing.tools.tool_replace_raster_values_by_field import ReplaceRasterValuesByFieldValuesAlgorithm
from los_tools.utils import get_icon_path, get_plugin_version


class LoSToolsProvider(QgsProcessingProvider):
    def __init__(self):
        super(LoSToolsProvider, self).__init__()

    def versionInfo(self):
        return get_plugin_version()

    def load(self) -> bool:
        ProcessingConfig.settingIcons[PluginConstants.provider_name_short] = self.icon()

        ProcessingConfig.addSetting(
            Setting(
                PluginConstants.provider_name_short,
                Settings.name_sample_z,
                "Use sampler in the Python code? If unchecked (set to `False`) "
                "the Z value is not extracted in tools that create LoS.",
                True,
            )
        )

        ProcessingConfig.readSettings()

        return super().load()

    def loadAlgorithms(self):
        self.addAlgorithm(CreatePointsAroundAlgorithm())
        self.addAlgorithm(CreatePointsInDirectionAlgorithm())
        self.addAlgorithm(CreateLocalLosAlgorithm())
        self.addAlgorithm(CreateGlobalLosAlgorithm())
        self.addAlgorithm(CreateNoTargetLosAlgorithm())
        self.addAlgorithm(AnalyseLosAlgorithm())
        self.addAlgorithm(ExtractHorizonsAlgorithm())
        self.addAlgorithm(ExtractHorizonLinesAlgorithm())
        self.addAlgorithm(ReplaceRasterValuesByConstantValueAlgorithm())
        self.addAlgorithm(ReplaceRasterValuesByFieldValuesAlgorithm())
        self.addAlgorithm(ExportLoSAlgorithm())
        self.addAlgorithm(ExportHorizonLinesAlgorithm())
        self.addAlgorithm(ExtractPointsLoSAlgorithm())
        self.addAlgorithm(LimitAnglesAlgorithm())
        self.addAlgorithm(OptimizePointLocationAlgorithm())
        self.addAlgorithm(AzimuthPointPolygonAlgorithm())
        self.addAlgorithm(ExtractLoSVisibilityPartsAlgorithm())
        self.addAlgorithm(ObjectSizesAlgorithm())
        self.addAlgorithm(ObjectDistancesAlgorithm())
        self.addAlgorithm(ExtractLoSVisibilityPolygonsAlgorithm())
        self.addAlgorithm(ObjectDetectionAngleAlgorithm())
        self.addAlgorithm(CreatePointsInAzimuthsAlgorithm())
        self.addAlgorithm(ExtractHorizonLinesByDistanceAlgorithm())

    def id(self):
        return PluginConstants.provider_id

    def name(self):
        return PluginConstants.provider_name

    def icon(self):
        path = get_icon_path("los_tools_icon.svg")
        return QIcon(path)

    def longName(self):
        return self.name()
