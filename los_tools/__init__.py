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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = "Jan Caha"
__date__ = "2020-03-05"
__copyright__ = "(C) 2020 by Jan Caha"

from los_tools.los_tools_plugin import LoSToolsPlugin


# noinspection PyPep8Naming
def classFactory(iface):
    """Load los_tools class from file los_tools.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    return LoSToolsPlugin(iface)
