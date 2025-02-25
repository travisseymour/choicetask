from typing import Literal

from PySide6.QtGui import QFont

from choicetask import quicknumbers


def int_or_zero(value):
    return quicknumbers.try_int(value, default=0)


def float_or_zero(value):
    return quicknumbers.try_float(value, default=0)


def get_default_font(family: Literal["sans-serif", "serif", "monospace"] = "monospace", size: int = 14) -> QFont:
    """Returns a cross-platform QFont object with fallbacks."""
    font_families = {
        "sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "Sans-serif"],
        "serif": ["Times New Roman", "Times", "Liberation Serif", "Serif"],
        "monospace": ["Courier New", "Courier", "DejaVu Sans Mono", "Monospace"],
    }

    font = QFont()
    for fam in font_families[family]:  # family is guaranteed to be a valid key
        font.setFamily(fam)
        if QFont(fam).exactMatch():  # Ensures the font exists on the system
            break

    font.setPointSize(size)
    return font
