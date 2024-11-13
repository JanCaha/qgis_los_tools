from pathlib import Path

from qgis.core import QgsPointXY
from qgis.gui import QgsMapCanvas, QgsMapMouseEvent
from qgis.PyQt.QtCore import QEvent, Qt
from qgis.PyQt.QtGui import QMouseEvent


def data_path() -> Path:
    """Path to folder with test data."""
    return Path(__file__).parent / "_data"


def data_result_path() -> Path:
    """Path to folder with test results data."""
    return data_path() / "results"


def data_file_path(filename: str) -> Path:
    """Path to file in test data folder."""
    path = data_path() / filename
    return path


def result_file_data_path(filename: str) -> Path:
    """Path to file in test results data folder."""
    path = data_result_path() / filename
    return path


def data_filename(filename: str) -> str:
    """File path to file in test data folder."""
    return data_file_path(filename).as_posix()


def result_filename(filename: str) -> str:
    """File path to file in test results data folder."""
    path = data_result_path() / filename
    return path.as_posix()


def create_mouse_event(
    qgis_canvas: QgsMapCanvas,
    point_in_canvas_crs_coordinates: QgsPointXY,
    event: QEvent.Type = QEvent.Type.MouseButtonRelease,
    mouse_button: Qt.MouseButton = Qt.MouseButton.LeftButton,
    key_modifier: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
):
    point_in_canvas_coords = qgis_canvas.getCoordinateTransform().toMapCoordinatesF(
        point_in_canvas_crs_coordinates.x(), point_in_canvas_crs_coordinates.y()
    )

    event = QMouseEvent(
        event,
        point_in_canvas_coords.toQPointF(),
        mouse_button,
        mouse_button,
        key_modifier,
    )

    return QgsMapMouseEvent(
        qgis_canvas,
        event,
    )
