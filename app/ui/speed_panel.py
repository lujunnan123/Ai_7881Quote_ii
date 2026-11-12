"""速度设置卡片：报价倍数、报价间隔与检测间隔。"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from app.config import clamp_float, clamp_int, format_multiplier
from app.ui.widgets import (
    add_card_header,
    add_field_label,
    numeric_field,
    prepare_card,
    small_label,
)


class SpeedPanel(QFrame):
    detect_interval_edited = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = prepare_card(self)
        add_card_header(layout, "节奏与倍数", "速度设置")

        add_field_label(layout, "报价倍数")
        self._mult_field = numeric_field(
            "1.1", QDoubleValidator(0.1, 10.0, 2, self)
        )
        layout.addWidget(self._mult_field)
        layout.addWidget(small_label("最终报价 = 底价 × 倍数，实时生效"))

        self._quote_field = numeric_field("30", QIntValidator(1, 3600, self))
        self._detect_field = numeric_field("20", QIntValidator(1, 3600, self))
        self._detect_field.editingFinished.connect(self._emit_detect_interval)

        pair = QHBoxLayout()
        pair.setSpacing(9)
        for label_text, field, suffix in (
            ("报价间隔（秒）", self._quote_field, "每车之间"),
            ("检测间隔（秒）", self._detect_field, "轮询之后"),
        ):
            group = QVBoxLayout()
            group.setSpacing(4)
            group.addWidget(small_label(label_text, "fieldLabel"))
            group.addWidget(field)
            group.addWidget(small_label(suffix))
            pair.addLayout(group, 1)
        layout.addLayout(pair)

    def multiplier(self) -> float:
        return round(clamp_float(self._mult_field.text(), 1.1, 0.1, 10.0), 2)

    def quote_interval(self) -> int:
        return clamp_int(self._quote_field.text(), 30, 1, 3600)

    def detect_interval(self) -> int:
        return clamp_int(self._detect_field.text(), 20, 1, 3600)

    def collect(self) -> tuple[float, int, int]:
        """读取并规范化输入框，保存时使用。"""
        multiplier = self.multiplier()
        quote_interval = self.quote_interval()
        detect_interval = self.detect_interval()
        self.set_values(multiplier, quote_interval, detect_interval)
        return multiplier, quote_interval, detect_interval

    def set_values(self, multiplier, quote_interval, detect_interval):
        self._mult_field.setText(format_multiplier(float(multiplier)))
        self._quote_field.setText(str(int(quote_interval)))
        self._detect_field.setText(str(int(detect_interval)))

    def _emit_detect_interval(self):
        self.detect_interval_edited.emit(self.detect_interval())
