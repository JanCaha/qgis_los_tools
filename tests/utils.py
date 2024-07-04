from pathlib import Path


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
