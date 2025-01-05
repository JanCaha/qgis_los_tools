from pathlib import Path

from qgis.core import Qgis, QgsLayout, QgsLayoutExporter, QgsPointXY
from qgis.gui import QgsMapCanvas, QgsMapMouseEvent
from qgis.PyQt.QtCore import QEvent, QPoint, QSize, Qt


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
    point_in_canvas_crs: QgsPointXY,
    event: QEvent.Type = QEvent.Type.MouseButtonRelease,
    mouse_button: Qt.MouseButton = Qt.MouseButton.LeftButton,
    key_modifier: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
):
    mouse_event = QgsMapMouseEvent(
        qgis_canvas,
        event,
        QPoint(0, 0),
        mouse_button,
        mouse_button,
        key_modifier,
    )
    mouse_event.setMapPoint(point_in_canvas_crs)

    return mouse_event


def export_layout(path: Path, layout: QgsLayout, page: int = 0) -> None:
    """Export layout to image."""

    dpi = 300

    layoutSize = layout.pageCollection().page(page - 1).sizeWithUnits()

    width = layout.convertFromLayoutUnits(layoutSize.width(), Qgis.LayoutUnit.Millimeters)
    height = layout.convertFromLayoutUnits(layoutSize.height(), Qgis.LayoutUnit.Millimeters)
    imageSize = QSize(int(width.length() * dpi / 25.4), int(height.length() * dpi / 25.4))

    image_settings = QgsLayoutExporter.ImageExportSettings()
    image_settings.dpi = dpi
    image_settings.imageSize = imageSize
    image_settings.pages = [page]

    exporter = QgsLayoutExporter(layout)
    exporter.exportToImage(path.as_posix(), image_settings)
