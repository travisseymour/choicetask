"""
ChoiceTask
Copyright (C) 2015-2025 Travis L. Seymour, PhD

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from importlib.resources import as_file, files
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication


def loading_cursor(normal_function):
    def decorated_function(*args, **kwargs):
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

        normal_function(*args, **kwargs)

        QApplication.restoreOverrideCursor()

    return decorated_function


def get_resource(*args: str) -> str:
    """
    Constructs and returns the full absolute path to a resource within 'choicetask/resources'.

    Args:
        *args: A sequence of strings representing the relative path components
               within 'choicetask/resources', e.g., ("images", "instructions.png").

    Returns:
        str: An absolute path to the requested resource.

    Raises:
        FileNotFoundError: If the resource does not exist.
        RuntimeError: If an error occurs while resolving the resource path.
    """
    try:
        # Base directory for resources in the package
        base = files("choicetask").joinpath("resources")

        # Construct the resource path relative to the base
        resource_path = base.joinpath(*args)

        # Ensure the resource path is accessible as a file
        with as_file(resource_path) as resolved_path:
            return str(Path(resolved_path).resolve())  # Ensure the path is absolute
    except FileNotFoundError:
        raise FileNotFoundError(f"Resource not found: {'/'.join(args)}")
    except Exception as e:
        raise RuntimeError(f"Error accessing resource: {e}")
