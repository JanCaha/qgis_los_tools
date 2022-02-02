from pathlib import Path
import configparser

from PyQt5.QtGui import QIcon

from qgis.core import QgsProcessingProvider
from los_tools.create_points.tool_points_around import CreatePointsAroundAlgorithm
from los_tools.create_points.tool_points_in_direction import CreatePointsInDirectionAlgorithm
from los_tools.create_los.tool_create_local_los import CreateLocalLosAlgorithm
from los_tools.create_los.tool_create_global_los import CreateGlobalLosAlgorithm
from los_tools.create_los.tool_create_notarget_los import CreateNoTargetLosAlgorithm
from los_tools.create_los.tool_create_notarget_los_v2 import CreateNoTargetLosAlgorithmV2
from los_tools.analyse_los.tool_analyse_los import AnalyseLosAlgorithm
from los_tools.horizons.tool_extract_horizons import ExtractHorizonsAlgorithm
from los_tools.horizons.tool_extract_horizon_lines import ExtractHorizonLinesAlgorithm
from los_tools.tools.tool_replace_raster_values import ReplaceRasterValuesAlgorithm
from los_tools.to_table.tool_export_los import ExportLoSAlgorithm
from los_tools.to_table.tool_export_horizon_lines import ExportHorizonLinesAlgorithm
from los_tools.analyse_los.tool_extract_points_los import ExtractPointsLoSAlgorithm
from los_tools.azimuths.tool_limit_angles_vector import LimitAnglesAlgorithm
from los_tools.create_points.tool_optimize_point_location import OptimizePointLocationAlgorithm
from los_tools.azimuths.tool_azimuth import AzimuthPointPolygonAlgorithm
from los_tools.analyse_los.tool_extract_los_visibility_parts import ExtractLoSVisibilityPartsAlgorithm
from los_tools.parameter_settings.tool_sizes_at_distances import ObjectSizesAlgorithm
from los_tools.parameter_settings.tool_distances_for_sizes import ObjectDistancesAlgorithm
from los_tools.analyse_los.tool_extract_los_visibility_polygons import ExtractLoSVisibilityPolygonsAlgorithm
from los_tools.parameter_settings.tool_angle_at_distance_for_size import ObjectDetectionAngleAlgorithm
from los_tools.create_points.tool_points_by_azimuths import CreatePointsInAzimuthsAlgorithm


class los_toolsProvider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        super().__init__()

        path = Path(__file__).parent / 'metadata.txt'

        config = configparser.ConfigParser()
        config.read(path)

        self.version = config['general']['version']

    def versionInfo(self):
        """
        Provider plugin version
        """
        return self.version

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(CreatePointsAroundAlgorithm())
        self.addAlgorithm(CreatePointsInDirectionAlgorithm())
        self.addAlgorithm(CreateLocalLosAlgorithm())
        self.addAlgorithm(CreateGlobalLosAlgorithm())
        self.addAlgorithm(CreateNoTargetLosAlgorithm())
        self.addAlgorithm(AnalyseLosAlgorithm())
        self.addAlgorithm(ExtractHorizonsAlgorithm())
        self.addAlgorithm(ExtractHorizonLinesAlgorithm())
        self.addAlgorithm(ReplaceRasterValuesAlgorithm())
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
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'lostools'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return "LoS Tools"

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        path = Path(__file__).parent / "icons" / "los_tools_icon.svg"
        return QIcon(str(path))

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
