from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsProcessingProvider

from .create_points.tool_points_around import CreatePointsAroundAlgorithm
from .create_points.tool_points_in_direction import CreatePointsInDirectionAlgorithm
from .create_los.tool_create_local_los import CreateLocalLosAlgorithm
from .create_los.tool_create_global_los import CreateGlobalLosAlgorithm
from .create_los.tool_create_notarget_los import CreateNoTargetLosAlgorithm
from .create_los.tool_create_notarget_los_v2 import CreateNoTargetLosAlgorithmV2
from .analyse_los.tool_analyse_los import AnalyseLosAlgorithm
from .horizons.tool_extract_horizons import ExtractHorizonsAlgorithm
from .horizons.tool_extract_horizon_lines import ExtractHorizonLinesAlgorithm
from .tools.tool_replace_raster_values_by_constant import ReplaceRasterValuesByConstantValueAlgorithm
from .tools.tool_replace_raster_values_by_field import ReplaceRasterValuesByFieldValuesAlgorithm
from .to_table.tool_export_los import ExportLoSAlgorithm
from .to_table.tool_export_horizon_lines import ExportHorizonLinesAlgorithm
from .analyse_los.tool_extract_points_los import ExtractPointsLoSAlgorithm
from .azimuths.tool_limit_angles_vector import LimitAnglesAlgorithm
from .create_points.tool_optimize_point_location import OptimizePointLocationAlgorithm
from .azimuths.tool_azimuth import AzimuthPointPolygonAlgorithm
from .analyse_los.tool_extract_los_visibility_parts import ExtractLoSVisibilityPartsAlgorithm
from .parameter_settings.tool_sizes_at_distances import ObjectSizesAlgorithm
from .parameter_settings.tool_distances_for_sizes import ObjectDistancesAlgorithm
from .analyse_los.tool_extract_los_visibility_polygons import ExtractLoSVisibilityPolygonsAlgorithm
from .parameter_settings.tool_angle_at_distance_for_size import ObjectDetectionAngleAlgorithm
from .create_points.tool_points_by_azimuths import CreatePointsInAzimuthsAlgorithm

from los_tools.constants.plugin import PluginConstants
from los_tools.utils import get_icon_path, get_plugin_version


class los_toolsProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()

    def versionInfo(self):
        return get_plugin_version()

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
        self.addAlgorithm(CreateNoTargetLosAlgorithmV2())
        self.addAlgorithm(ExtractLoSVisibilityPolygonsAlgorithm())
        self.addAlgorithm(ObjectDetectionAngleAlgorithm())
        self.addAlgorithm(CreatePointsInAzimuthsAlgorithm())

    def id(self):
        return PluginConstants.provider_id

    def name(self):
        return PluginConstants.provider_name

    def icon(self):
        path = get_icon_path("los_tools_icon.svg")
        return QIcon(path)

    def longName(self):
        return self.name()
