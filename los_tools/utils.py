from pathlib import Path
import configparser


def get_icon_path(icon_name: str) -> str:

    path = Path(__file__).parent / "icons" / icon_name

    return path.absolute().as_posix()


def get_plugin_version() -> str:

    path = Path(__file__).parent / 'metadata.txt'

    config = configparser.ConfigParser()
    config.read(path)

    return config['general']['version']
