import os
import sys
import inspect

from qgis.core import QgsApplication
from los_tools.los_tools_provider import los_toolsProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class los_toolsPlugin():

    def __init__(self):
        self.provider = los_toolsProvider()

    def initProcessing(self):
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
