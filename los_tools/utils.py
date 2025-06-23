import configparser
import json
from pathlib import Path


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
