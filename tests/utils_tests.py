# coding=utf-8
"""Common functionality used by regression tests."""

import sys
import logging
import os
import atexit

from qgis.core import QgsApplication, QgsProcessingAlgorithm
from qgis.analysis import QgsNativeAlgorithms
from qgis.utils import iface
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtWidgets import QWidget

from .qgis_interface import QgisInterface

LOGGER = logging.getLogger('QGIS')
QGIS_APP = None  # Static variable used to hold hand to running QGIS app
CANVAS = None
PARENT = None
IFACE = None


def get_qgis_app(cleanup=True, debug=False):
    """ Start one QGIS application to test against.

    :returns: Handle to QGIS app, canvas, iface and parent. If there are any
        errors the tuple members will be returned as None.
    :rtype: (QgsApplication, CANVAS, IFACE, PARENT)

    If QGIS is already running the handle to that app will be returned.
    """

    global QGIS_APP, PARENT, IFACE, CANVAS  # pylint: disable=W0603

    if iface:
        QGIS_APP = QgsApplication
        CANVAS = iface.mapCanvas()
        PARENT = iface.mainWindow()
        IFACE = iface
        return QGIS_APP, CANVAS, IFACE, PARENT

    global QGISAPP  # pylint: disable=global-variable-undefined

    try:
        QGISAPP
    except NameError:
        myGuiFlag = True  # All test will run qgis in gui mode

        # In python3 we need to convert to a bytes object (or should
        # QgsApplication accept a QString instead of const char* ?)
        try:
            argvb = list(map(os.fsencode, sys.argv))
        except AttributeError:
            argvb = sys.argv

        # Note: QGIS_PREFIX_PATH is evaluated in QgsApplication -
        # no need to mess with it here.
        QGISAPP = QgsApplication(argvb, myGuiFlag)

        QGISAPP.initQgis()
        s = QGISAPP.showSettings()
        LOGGER.debug(s)

        QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

        def debug_log_message(message, tag, level):
            """
            Prints a debug message to a log
            :param message: message to print
            :param tag: log tag
            :param level: log message level (severity)
            :return:
            """
            print('{}({}): {}'.format(tag, level, message))

        if debug:
            QgsApplication.instance().messageLog().messageReceived.connect(
                debug_log_message)

        if cleanup:
            @atexit.register
            def exitQgis():  # pylint: disable=unused-variable
                """
                Gracefully closes the QgsApplication instance
                """
                try:
                    QGISAPP.exitQgis()  # pylint: disable=used-before-assignment
                    QGISAPP = None  # pylint: disable=redefined-outer-name
                except NameError:
                    pass

    if PARENT is None:
        # noinspection PyPep8Naming
        PARENT = QWidget()

    if CANVAS is None:
        # noinspection PyPep8Naming
        CANVAS = QgsMapCanvas(PARENT)
        CANVAS.resize(QSize(400, 400))

    if IFACE is None:
        # QgisInterface is a stub implementation of the QGIS plugin interface
        # noinspection PyPep8Naming
        IFACE = QgisInterface(CANVAS)

    return QGISAPP, CANVAS, IFACE, PARENT


def print_alg_params(alg: QgsProcessingAlgorithm) -> None:

    params = alg.parameterDefinitions()

    for p in params:
        print("{} - {} \n\t {} \t{}".format(p.name(),
                                            p.type(),
                                            p.description(),
                                            p.asScriptCode()))


def print_alg_outputs(alg: QgsProcessingAlgorithm) -> None:

    outputs = alg.outputDefinitions()

    for o in outputs:
        print("{} - {} \n\t {}".format(o.name(),
                                       o.type(),
                                       o.description()))


def get_data_path(file: str = None) -> str:
    path = ""
    if file is None:
        path = os.path.join(os.path.dirname(__file__), "test_data")
    else:
        path = os.path.join(os.path.dirname(__file__), "test_data", file)

    return path


def get_data_path_results(file: str = None) -> str:
    path = ""
    if file is None:
        path = os.path.join(get_data_path(), "results")
    else:
        path = os.path.join(get_data_path(), "results", file)

    return path
