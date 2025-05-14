import configparser
import json
import typing
from pathlib import Path

from qgis.core import Qgis
from qgis.PyQt.QtCore import QMetaType, QVariant


def get_icon_path(icon_name: str) -> str:
    path = Path(__file__).parent / "icons" / icon_name

    return path.absolute().as_posix()


def get_plugin_version() -> str:
    path = Path(__file__).parent / "metadata.txt"

    config = configparser.ConfigParser()
    config.read(path)

    return config["general"]["version"]


def get_doc_file(file_path: str) -> dict[str, str]:
    """Get the help file for a given file path."""

    path = Path(file_path)

    file = f"{path.stem}.help"

    help_file = path.parent.parent / "doc" / file

    if help_file.exists():
        with open(help_file, encoding="utf-8") as f:
            descriptions = json.load(f)

        return descriptions

    return {}


def _column_type_class():
    """Select clas for types based on version of QGIS."""
    if Qgis.versionInt() >= 33800:
        source_type = QMetaType.Type
    else:
        source_type = QVariant.Type
    return source_type


def _colum_type_string() -> typing.Union[QVariant.Type, QMetaType.Type]:
    """Return string representation of column type based on version of QGIS."""
    source_type = _column_type_class()
    if Qgis.versionInt() >= 33800:
        source_type_string = source_type.QString
    else:
        source_type_string = source_type.String
    return source_type_string


COLUMN_TYPE: type[typing.Union[QMetaType.Type, QVariant.Type]] = _column_type_class()
COLUMN_TYPE_STRING: type[typing.Union[QMetaType.Type, QVariant.Type]] = _colum_type_string()
