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

from PySide6 import QtWidgets, QtCore

from choicetask import log


def mbox_critical(msg, title="Critical Error"):
    """
    Show the critical message
    https://doc.qt.io/qt-5/qmessagebox.html
    """
    msgbox = QtWidgets.QMessageBox()
    _ = QtWidgets.QMessageBox.critical(
        msgbox, title, msg, QtWidgets.QMessageBox.StandardButton.Ok, QtWidgets.QMessageBox.StandardButton.Ok
    )


def mbox_warning(msg, title="Warning"):
    """
    Show the warning message
    """
    msgbox = QtWidgets.QMessageBox()
    _ = QtWidgets.QMessageBox.warning(
        msgbox, title, msg, QtWidgets.QMessageBox.StandardButton.Ok, QtWidgets.QMessageBox.StandardButton.Ok
    )


def mbox_yes_no(msg, title="What is Your Answer?"):
    """
    Show y/n choice
    """
    buttons = QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
    default_button = QtWidgets.QMessageBox.StandardButton.Yes
    msgbox = QtWidgets.QMessageBox()
    response = QtWidgets.QMessageBox.warning(msgbox, title, msg, buttons, default_button)
    return response == QtWidgets.QMessageBox.StandardButton.Yes


def mbox_input(msg, title="Enter Your Response"):
    """
    allows for user input
    https://doc.qt.io/qt-5/qinputdialog.html
    """
    input_box = QtWidgets.QInputDialog(flags=QtCore.Qt.WindowType.Dialog)
    text, ok = QtWidgets.QInputDialog.getText(
        input_box, title, msg, QtWidgets.QLineEdit.EchoMode.Normal, "", flags=QtCore.Qt.WindowType.Dialog
    )
    return text


if __name__ == "__main__":
    _application = QtWidgets.QApplication([])

    if mbox_yes_no("Test Dialog Boxes?"):
        mbox_warning(msg="You may have skipped a step...no worries", title="Warning")
        mbox_critical(msg="Something bad just happened", title="Critical Error")
        log.info(f"NAME[{mbox_input('What is your name?')}]")
        log.info("FUN={mbox_yes_no('Are We Having Fun Yet??!!')}")
