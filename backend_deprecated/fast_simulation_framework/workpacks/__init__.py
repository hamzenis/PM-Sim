"""
Init file for workpacks module

Contains imports for all workpacks available
"""

from .wp_original import USERPARAMETERS_OG
from .wp_only_do_tasks import USERPARAMETERS_ONLY_TASKS
from .wp_example import USERPARAMETERS_EXAMPLE

__all__ = [
    "USERPARAMETERS_OG",
    "USERPARAMETERS_ONLY_TASKS",
    "USERPARAMETERS_EXAMPLE",
]