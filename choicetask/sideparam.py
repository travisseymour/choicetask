"""
SideParam
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

import os
from sys import maxsize
from typing import Any, Optional, List, Tuple, Dict, Union

from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QApplication, QLabel



from choicetask import log
from choicetask.app_utils import int_or_zero, float_or_zero
from choicetask.mboxes import mbox_warning

"""
QT based parameter form class.
Inspired by QtGuidata.
"""


# ------------------------------------
class DataType:
    def __init__(self, label: Optional[str], default: Any, tooltip: Optional[str]) -> None:
        self.label: Optional[str] = label
        self.default: Any = default
        self.tooltip: Optional[str] = tooltip
        self.widgets: Dict[str, Optional[QtWidgets.QWidget]] = {}

    def _fix_params(self) -> None:
        if not isinstance(self.tooltip, str):
            self.tooltip = str(self.default)

    def fix_params(self) -> None:
        pass

    def make_widget(self) -> Optional[QtWidgets.QWidget]:
        return None

    def value(self) -> Any:
        return None


class NoteItem(DataType):
    def __init__(self, label: Optional[str] = None, note_text: str = "") -> None:
        super().__init__(label, None, None)
        self.note: str = note_text
        self.fix_params()
        self.make_widgets()

    def fix_params(self) -> None:
        if self.label and not isinstance(self.label, str):
            self.label = str(self.label)
        if not isinstance(self.note, str):
            self.note = str(self.note)

    def make_widgets(self) -> None:
        label_widget: Optional[QtWidgets.QLabel] = QtWidgets.QLabel(self.label) if self.label else None
        widget: QtWidgets.QLabel = QtWidgets.QLabel(self.note)
        self.widgets["label"] = label_widget
        self.widgets["widget"] = widget

    def value(self) -> Tuple[None, None]:
        return None, None


class StringItem(DataType):
    def __init__(
        self,
        label: str = "",
        default: str = "",
        tooltip: str = "",
        notempty: bool = False,
        maxlength: int = 1000,
        good_list: Optional[List[Any]] = None,
        bad_list: Optional[List[Any]] = None,
        bad_list_msg: str = "\n(This value is forbidden.)",
        empty_msg: str = "\n(This field cannot be empty.)",
    ) -> None:
        super().__init__(label, default, tooltip)
        self.not_empty: bool = notempty
        self.max_length: int = maxlength
        self.fix_params()
        self.good_list: List[str] = list(map(str, good_list)) if good_list else []
        self.bad_list: List[Any] = list(bad_list) if bad_list else []
        self.bad_list_msg: str = bad_list_msg
        self.empty_msg: str = empty_msg
        self.make_widgets()

    def fix_params(self) -> None:
        if not isinstance(self.default, str):
            self.default = str(self.default)
        self.not_empty = bool(self.not_empty)
        if not isinstance(self.max_length, int):
            self.max_length = int(self.max_length)
        if not (1 < self.max_length < 1000):
            self.max_length = 1000

    def make_widgets(self) -> None:
        label_widget: Optional[QtWidgets.QLabel] = QtWidgets.QLabel(self.label) if self.label else None
        widget: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self.default)
        widget.setMaxLength(self.max_length)
        widget.setToolTip(self.tooltip)
        self.widgets["label"] = label_widget
        self.widgets["widget"] = widget
        # Connect validation without manually emitting a signal.
        widget.textChanged.connect(self.validate_line_edit)
        self.validate_line_edit(widget.text())

    def validate_line_edit(self, text: str, *args: Any, **kwargs: Any) -> None:
        """
        Validate the text in the QLineEdit.
        (Note: modifying the label text for errors mixes validation state with UI presentation;
         consider using a separate error display for a cleaner separation.)
        """
        white: str = "#ffffff"
        red: str = "#f6989d"
        widget: QtWidgets.QLineEdit = self.widgets["widget"]  # type: ignore
        label: QtWidgets.QLabel = self.widgets["label"]  # type: ignore
        entry: str = text
        label_text: str = label.text()

        # Clear out previous error messages.
        if self.empty_msg in label_text:
            label_text = label_text.replace(self.empty_msg, "")
        if self.bad_list_msg in label_text:
            label_text = label_text.replace(self.bad_list_msg, "")
        # Validate entry.
        if self.good_list and entry in self.good_list:
            color: str = white
        elif self.not_empty and entry.strip() == "":
            color = red
            label_text += self.empty_msg
        elif self.bad_list and entry in self.bad_list:
            color = red
            label_text += self.bad_list_msg
        else:
            color = white
        widget.setStyleSheet(f"QLineEdit {{ background-color: {color} }}")
        if label_text != label.text():
            label.setText(label_text)

    def value(self) -> Tuple[str, str]:
        label_widget: Optional[QtWidgets.QLabel] = self.widgets.get("label")
        label_val: str = label_widget.text() if label_widget else ""
        return label_val, self.widgets["widget"].text()  # type: ignore


class FileItem(DataType):
    def __init__(
        self,
        label: str = "",
        default: str = "",
        tooltip: str = "",
        notempty: bool = False,
        initialdir: str = ".",
        filespec: str = "All Files (*.*)",
    ) -> None:
        super().__init__(label, default, tooltip)
        self.initial_dir: str = initialdir
        self.filespec: str = filespec
        self.not_empty: bool = notempty
        self.f_edit: Optional[QtWidgets.QPlainTextEdit] = None
        self.f_but: Optional[QtWidgets.QToolButton] = None
        self.fix_default()
        self.fix_params()
        self.make_widgets()

    def fix_default(self) -> None:
        if not isinstance(self.default, str) or not os.path.exists(self.default) or not os.path.isfile(self.default):
            self.default = ""

    def fix_params(self) -> None:
        if (
            not isinstance(self.initial_dir, str)
            or not os.path.exists(self.initial_dir)
            or not os.path.isdir(self.initial_dir)
        ):
            self.initial_dir = os.getcwd()
        if not isinstance(self.filespec, str):
            self.filespec = "*.*"
        self.not_empty = bool(self.not_empty)

    def get_the_file(self) -> None:
        f_name, _ = QtWidgets.QFileDialog().getOpenFileName(
            None, "Select File", self.initial_dir, self.filespec, options=QtWidgets.QFileDialog.Option.ReadOnly
        )
        if os.path.exists(f_name) and os.path.isfile(f_name):
            self.f_edit.setPlainText(f_name)

    def make_widgets(self) -> None:
        label_widget: Optional[QtWidgets.QLabel] = QtWidgets.QLabel(self.label) if self.label else None
        widget_set: QtWidgets.QWidget = QtWidgets.QWidget()
        widget_set.setWindowFlags(QtCore.Qt.WindowType.Widget)
        layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self.f_edit: QtWidgets.QPlainTextEdit = QtWidgets.QPlainTextEdit(self.default)
        self.f_edit.setToolTip(self.tooltip)
        self.f_edit.setMinimumHeight(54)
        self.f_edit.setFixedHeight(56)
        self.f_edit.setReadOnly(True)
        self.f_but: QtWidgets.QToolButton = QtWidgets.QToolButton(widget_set)
        self.f_but.setIcon(self.f_but.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon))
        self.f_but.setIconSize(QtCore.QSize(44, 44))
        self.f_but.clicked.connect(self.get_the_file)
        layout.addWidget(self.f_edit, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.f_but, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        widget_set.setLayout(layout)
        self.widgets["label"] = label_widget
        self.widgets["widget"] = widget_set

    def value(self) -> Tuple[str, str]:
        label_widget: Optional[QLabel] = self.widgets.get("label")
        label_val: str = label_widget.text() if label_widget else ""
        return label_val, self.f_edit.toPlainText()


class DirectoryItem(FileItem):
    def fix_default(self) -> None:
        if not isinstance(self.default, str) or not os.path.exists(self.default) or not os.path.isdir(self.default):
            self.default = ""

    def get_the_file(self) -> None:
        try:
            dirname: str = QtWidgets.QFileDialog().getExistingDirectory(
                None, "Select File", self.initial_dir, options=QtWidgets.QFileDialog.Option.ShowDirsOnly
            )
            if os.path.exists(dirname) and os.path.isdir(dirname):
                self.f_edit.setPlainText(dirname)
        except Exception as e:
            log.error(f"DirectoryItem Error: {e}")


class TextItem(StringItem):
    def make_widgets(self) -> None:
        # self.word_wrap: bool = True
        label_widget: Optional[QtWidgets.QLabel] = QtWidgets.QLabel(self.label) if self.label else None
        widget: QtWidgets.QPlainTextEdit = QtWidgets.QPlainTextEdit(self.default)
        widget.setMinimumHeight(54)
        widget.setToolTip(self.tooltip)
        self.widgets["label"] = label_widget
        self.widgets["widget"] = widget

    def value(self) -> Tuple[str, str]:
        label_widget: Optional[QtWidgets.QLabel] = self.widgets.get("label")
        label_val: str = label_widget.text() if label_widget else ""
        return label_val, self.widgets["widget"].toPlainText()  # type: ignore


class ChoiceItem(DataType):
    def __init__(
        self,
        label: str = "",
        default: Union[int, str] = 0,
        tooltip: str = "",
        choices: Optional[Union[List[Any], Tuple[Any, ...]]] = None,
    ) -> None:
        super().__init__(label, default, tooltip)
        self.choices: Optional[Union[List[Any], Tuple[Any, ...]]] = choices
        if isinstance(self.choices, (list, tuple)):
            self.choices = list(map(str, self.choices))
        self.index: int = 0
        self.params_ok: bool = self.fix_params()
        if self.params_ok:
            self.make_widgets()

    def fix_params(self) -> bool:
        if not isinstance(self.choices, (list, tuple)):
            return False
        if isinstance(self.default, int) and (0 < self.default < (len(self.choices) - 1)):
            self.index = self.default
        elif isinstance(self.default, str) and (self.default in self.choices):  # type: ignore
            self.index = self.choices.index(self.default)  # type: ignore
        else:
            self.index = 0
        return True

    def make_widgets(self) -> None:
        if not isinstance(self.choices, (list, tuple)):
            self.widgets = {}
        else:
            label_widget: QtWidgets.QLabel = QtWidgets.QLabel(self.label)
            widget: QtWidgets.QComboBox = QtWidgets.QComboBox()
            widget.addItems(self.choices)  # type: ignore
            widget.setCurrentIndex(self.index)
            widget.setEditable(False)
            widget.setToolTip(self.tooltip)
            self.widgets["label"] = label_widget
            self.widgets["widget"] = widget

    def value(self) -> Tuple[str, str]:
        label_widget: Optional[QtWidgets.QLabel] = self.widgets.get("label")
        label_val: str = label_widget.text() if label_widget else ""
        return label_val, self.widgets["widget"].currentText()  # type: ignore


class IntItem(DataType):
    def __init__(
        self, label: str = "", default: Any = 0, tooltip: str = "", minimum: int = 0, maximum: int = maxsize
    ) -> None:
        super().__init__(label, default, tooltip)
        self.min_value: int = minimum
        self.max_value: int = maximum
        self.fix_params()
        self.make_widgets()

    def fix_params(self) -> None:
        self.default = int_or_zero(self.default)
        self.min_value = int_or_zero(self.min_value)
        self.max_value = int_or_zero(self.max_value)

    def make_widgets(self) -> None:
        label_widget: Optional[QtWidgets.QLabel] = QtWidgets.QLabel(self.label)
        widget: QtWidgets.QSpinBox = QtWidgets.QSpinBox()
        widget.setValue(self.default)
        widget.setRange(self.min_value, self.max_value)
        widget.setToolTip(self.tooltip)
        self.widgets["label"] = label_widget
        self.widgets["widget"] = widget

    def value(self) -> Tuple[str, int]:
        label_widget: Optional[QtWidgets.QLabel] = self.widgets.get("label")
        label_val: str = label_widget.text() if label_widget else ""
        return label_val, self.widgets["widget"].value()  # type: ignore


class FloatItem(IntItem):
    def fix_params(self) -> None:
        self.default = float_or_zero(self.default)
        self.min_value = float_or_zero(self.min_value)
        self.max_value = float_or_zero(self.max_value)

    def make_widgets(self) -> None:
        label_widget: Optional[QtWidgets.QLabel] = QtWidgets.QLabel(self.label)
        widget: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox()
        widget.setValue(self.default)
        widget.setRange(self.min_value, self.max_value)
        widget.setToolTip(self.tooltip)
        self.widgets["label"] = label_widget
        self.widgets["widget"] = widget


class BoolItem(DataType):
    def __init__(
        self, label: str = "", default: bool = True, tooltip: str = "", tag: Optional[str] = None, enabled: bool = True
    ) -> None:
        super().__init__(label, default, tooltip)
        self.tag: Optional[str] = tag
        self.enabled: bool = enabled
        self.fix_params()
        self.make_widgets()

    def fix_params(self) -> None:
        # Directly convert to bool without a try/except.
        self.default = bool(self.default)

    def make_widgets(self) -> None:
        label_widget: Optional[QtWidgets.QLabel] = QtWidgets.QLabel(self.label)
        widget: QtWidgets.QCheckBox = QtWidgets.QCheckBox()
        widget.setChecked(self.default)
        if self.tag:
            widget.setText(self.tag)
        widget.setToolTip(self.tooltip)
        widget.setEnabled(self.enabled)
        self.widgets["label"] = label_widget
        self.widgets["widget"] = widget

    def value(self) -> Tuple[str, bool]:
        label_widget: Optional[QtWidgets.QLabel] = self.widgets.get("label")
        label_val: str = label_widget.text() if label_widget else ""
        return label_val, self.widgets["widget"].isChecked()  # type: ignore


# ------------------------------------
def run_app(main_window: QtWidgets.QWidget, title: str, app: QApplication) -> None:
    """
    Sets the main window's title and runs the application.
    """
    main_window.setWindowTitle(title)
    main_window.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
    main_window.show()
    main_window.raise_()
    app.exec()


class ParamForm(QtWidgets.QDialog):
    def __init__(self, title: str, param_list: List[DataType]) -> None:
        super().__init__()
        self.title: str = title
        self.param_list: List[DataType] = param_list
        self.row: int = 0
        # Rename "ok" to "accepted" for clarity.
        self.ok: bool = True
        self.ok_button: QtWidgets.QPushButton = QtWidgets.QPushButton("OK", self)
        self.cancel_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Cancel", self)
        self.ok_button.clicked.connect(self.click_ok)
        self.cancel_button.clicked.connect(self.click_cancel)

        # Create layout.
        self.layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout()
        self.add_widgets()
        self.add_buttons()
        self.setLayout(self.layout)

    def add_widgets(self) -> None:
        if not self.param_list:
            return
        # Add widgets from param_list.
        for param in self.param_list:
            label: Optional[QtWidgets.QWidget] = param.widgets.get("label")
            widget: Optional[QtWidgets.QWidget] = param.widgets.get("widget")
            if label is not None and widget is not None:
                # For compound widgets (e.g., FileItem), span across columns.
                if isinstance(widget, QtWidgets.QWidget):
                    self.layout.addWidget(label, self.row, 0, 1, 2)
                    self.row += 1
                    self.layout.addWidget(widget, self.row, 0, 1, 2)
                else:
                    self.layout.addWidget(label, self.row, 0)
                    self.layout.addWidget(widget, self.row, 1)
                self.row += 1
            elif widget is not None:
                self.layout.addWidget(widget, self.row, 0, 1, 2)
                self.row += 1

    def add_buttons(self) -> None:
        """Manually add cancel and OK buttons as the last row of widgets."""
        button_layout_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        button_layout_widget.setWindowFlags(QtCore.Qt.WindowType.Widget)
        layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.cancel_button, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.ok_button, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        button_layout_widget.setLayout(layout)
        self.layout.addWidget(button_layout_widget, self.row, 1)

    def get_values(self) -> List[Any]:
        values: List[Any] = []
        for param in self.param_list:
            _, value = param.value()
            values.append(value)
        return values

    def verify(self, msg: str = "Are these correct?") -> bool:
        """
        Display a dialog to verify current values.
        """
        question: str = f"{msg}<br>----------------<br>"
        for param in self.param_list:
            label, value = param.value()
            if value is None:
                continue
            elif isinstance(param, StringItem):
                continue
            elif isinstance(param, BoolItem):
                tag: Optional[str] = param.tag
                tag_str: str = f"[{tag}]" if tag else ""
                question += f'<font color="#0000FF">{label}{tag_str}</font>: {value}<br>'
            else:
                question += f'<font color="#0000FF">{label}</font>: {value}<br>'
        buttons = QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        default_button = QtWidgets.QMessageBox.StandardButton.Yes
        msg_box = QtWidgets.QMessageBox()
        response = QtWidgets.QMessageBox.question(msg_box, "Question", question, buttons, default_button)
        return response == QtWidgets.QMessageBox.StandardButton.Yes

    def click_cancel(self) -> None:
        self.ok = False
        self.close()

    def click_ok(self) -> None:
        problem_fields: List[str] = []
        for param in self.param_list:
            if isinstance(param, (TextItem, StringItem)):
                label, _ = param.value()
                # Check if error messages are present in the label text.
                if param.bad_list_msg in label or param.empty_msg in label:
                    problem_fields.append(label)
        if problem_fields:
            p_str: str = "\n".join(problem_fields)
            p_msg: str = f"The following fields contain invalid entries:\n{p_str}"
            mbox_warning(p_msg, "")
        else:
            self.ok = True
            self.close()


if __name__ == "__main__":
    application: QApplication = QApplication([])

    note: NoteItem = NoteItem(
        None, note_text="<b>Select Session Parameters</b><p><em>You can hover over the fields for help.</em>"
    )
    participant_id: StringItem = StringItem(
        "Participant ID", default="P100", notempty=True, maxlength=20, bad_list=["P100"]
    )
    blocks: IntItem = IntItem("Blocks", minimum=1, maximum=10, default=2)
    trials: IntItem = IntItem("Trials Per Block", minimum=4, maximum=60, default=4)
    pi: FloatItem = FloatItem("What is PI?", minimum=0, tooltip="enter your guess for the value of PI")
    condition: ChoiceItem = ChoiceItem("Condition", choices=["Easy", "Hard"], default=0)
    session_type: ChoiceItem = ChoiceItem("Session Type", choices=["Practice", "Test"], default=0)
    resolution: ChoiceItem = ChoiceItem("Screen Resolution", choices=["(800 x 600)", "(1024 x 768)"], default=0)
    fullscreen: BoolItem = BoolItem("", tag="Run Fullscreen?", default=True)
    div1: NoteItem = NoteItem("---------")
    comments: TextItem = TextItem("Comments")
    thread_info_file: FileItem = FileItem(
        "Filename", "", initialdir="/home/user/python_files", filespec="Python Files(*.py)"
    )

    form: ParamForm = ParamForm(
        "Settings",
        [
            note,
            participant_id,
            blocks,
            trials,
            pi,
            condition,
            session_type,
            resolution,
            fullscreen,
            div1,
            comments,
            thread_info_file,
        ],
    )
    run_app(form, "Settings", application)
    if form.ok:
        log.info(f"values: {form.get_values()}")
        if form.verify():
            log.info("USER ACCEPTED SETTINGS!")
        else:
            log.warning("USER REJECTED SETTINGS")
    else:
        log.info("The Form Has Been Cancelled!")
