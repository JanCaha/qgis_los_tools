# -*- coding: utf-8 -*-

"""
/***************************************************************************
 los_tools
                                 A QGIS plugin
 This plugin creates and analyzes lines of sight and also provides supporting tools.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-03-05
        copyright            : (C) 2020 by Jan Caha
        email                : jan.caha@outlook.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Jan Caha'
__date__ = '2020-03-05'
__copyright__ = '(C) 2020 by Jan Caha'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import QgsProcessingProvider
from los_tools.create_points.tool_points_around import CreatePointsAroundAlgorithm
from los_tools.create_points.tool_points_in_direction import CreatePointsInDirectionAlgorithm
from los_tools.create_los.tool_create_local_los import CreateLocalLosAlgorithm
from los_tools.create_los.tool_create_global_los import CreateGlobalLosAlgorithm
from los_tools.create_los.tool_create_notarget_los import CreateNoTargetLosAlgorithm
from los_tools.analyse_los.tool_analyse_los import AnalyseLosAlgorithm
from los_tools.horizons.tool_extract_horizons import ExtractHorizonsAlgorithm
from los_tools.horizons.tool_extract_horizon_lines import ExtractHorizonLinesAlgorithm
from los_tools.tools.tool_replace_raster_values import ReplaceRasterValuesAlgorithm
from los_tools.to_table.tool_export_los import ExportLoSAlgorithm
from los_tools.to_table.tool_export_horizon_lines import ExportHorizonLinesAlgorithm
from los_tools.tools.tool_extract_points_los import ExtractPointsLoSAlgorithm
from los_tools.tools.tool_limit_angles_vector import LimitAnglesAlgorithm
from los_tools.create_points.tool_optimize_point_location import OptimizePointLocationAlgorithm
from los_tools.tools.tool_azimuth import AzimuthPointPolygonAlgorithm


class los_toolsProvider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

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
        return QgsProcessingProvider.icon(self)

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()