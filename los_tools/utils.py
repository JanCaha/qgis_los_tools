from pathlib import Path
import configparser
import json


def get_icon_path(icon_name: str) -> str:

    path = Path(__file__).parent / "icons" / icon_name

    return path.absolute().as_posix()


def get_plugin_version() -> str:

    path = Path(__file__).parent / 'metadata.txt'

    config = configparser.ConfigParser()
    config.read(path)

    return config['general']['version']


def get_doc_file(file_path: str):

    path = Path(file_path)

    file = "{}.help".format(path.stem)

    help_file = path.parent.parent / "doc" / file

    if help_file.exists():
        with open(help_file) as f:
            descriptions = json.load(f)

        return descriptions

    return ""
