"""Project path utils"""
from pathlib import Path


def get_project_root() -> Path:
    """Returns project root directory as pathlib.Path"""
    return Path(__file__).parent.parent
