#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""7881 自动报价 · 桌面控制台（PySide6 GUI）

按参考截图复刻的界面：运行控制、速度设置、话术管理与运行日志。
报价流程为本地模拟数据，未接入任何真实接口。
"""

from __future__ import annotations

import copy
import html
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QDoubleValidator,
    QFont,
    QIcon,
    QIntValidator,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QTextOption,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

SANS = ["Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", "Segoe UI"]
SERIF = ["Source Han Serif SC", "Noto Serif SC", "Songti SC", "SimSun"]
MONO = ["Cascadia Mono", "Consolas", "Courier New"]

DEFAULT_SCRIPTS = [
    "出的价直接签同意就报价就可以了，手续费都是我这边的，给您的就是您到手的一个价",
    "或者对价格不满意你和我说下，我这边可以申请的，这边尽量给到您一个满意的价格",
]

DEFAULT_CONFIG = {
    "scripts": list(DEFAULT_SCRIPTS),
    "multiplier": 1.1,
    "quote_interval": 30,
    "detect_interval": 20,
    "auto_submit": True,
    "exclusions": [],
}

LOG_COLORS = {
    "info": "#d8d3c6",
    "muted": "#9b968a",
    "ok": "#8cc79a",
    "warn": "#d9b271",
    "err": "#e08f84",
}

QSS = """
#mainWindow { background: #f2efe7; }
#root { background: #f2efe7; }

#card {
    background: #fffdf8;
    border: 1px solid #e7e1d4;
    border-radius: 14px;
}
#stat {
    background: #f8f5ed;
    border: 1px solid #e9e2d5;
    border-radius: 10px;
}
QLabel#statValue { font-size: 23px; font-weight: 700; color: #2c2c24; }
QLabel#statCaption { font-size: 11px; color: #9a9381; }
QLabel#kicker { font-size: 11px; color: #9c9583; }
QLabel#hint { font-size: 11px; color: #9d9684; }
QLabel#fieldLabel { font-size: 12px; color: #6e695b; }
QLabel#checkTitle { font-size: 13px; color: #2c2c25; }
QLabel#checkSub { font-size: 11px; color: #9c9583; }
QLabel#savedToast { font-size: 11px; color: #377456; }
QLabel#serviceTag { color: #3d7a5c; }
QLabel#logTitle { color: #98937f; font-size: 12px; }
QLabel#logConn { color: #8cc09a; font-size: 11px; }
QPushButton { border: 0; }
QPushButton#stopBtn {
    background: #b64b41; color: #fff9f4; border-radius: 8px;
    padding: 9px 10px; font-size: 14px; font-weight: 600;
}
QPushButton#stopBtn:hover { background: #ad453b; }
QPushButton#stopBtn:pressed { background: #a03d34; }
QPushButton#startBtn {
    background: #1e4a39; color: #f5fbf7; border-radius: 8px;
    padding: 9px 10px; font-size: 14px; font-weight: 600;
}
QPushButton#startBtn:hover { background: #194131; }
QPushButton#startBtn:pressed { background: #143a2a; }
QPushButton#ghostBtn {
    background: #fffdf8; color: #4d493d; border: 1px solid #ddd6c6;
    border-radius: 8px; padding: 7px 12px; font-size: 12px;
}
QPushButton#ghostBtn:hover { background: #f7f3e9; border-color: #cfc7b4; }
QPushButton#ghostBtn:pressed { background: #f1ece0; }
QPushButton#primaryBtn {
    background: #1e4a39; color: #f5fbf7; border-radius: 8px;
    padding: 9px 22px; font-size: 13px; font-weight: 600;
}
QPushButton#primaryBtn:hover { background: #194131; }
QPushButton#primaryBtn:pressed { background: #143a2a; }
QPushButton#linkBtn {
    background: transparent; color: #78715f; padding: 9px 12px; font-size: 13px;
}
QPushButton#linkBtn:hover { color: #403c31; }

QLineEdit#field {
    background: #fbf8f1; border: 1px solid #e4ddcc; border-radius: 8px;
    padding: 7px 10px; color: #2d2d26; font-size: 14px;
    selection-background-color: #cfe0d5;
}
QLineEdit#field:focus { border: 1px solid #a8bead; background: #fffdf8; }
QLineEdit#field:disabled { color: #a9a294; background: #f5f2ea; border-color: #e9e3d7; }

#scriptRow {
    background: #fbf8f1;
    border: 1px solid #e5decf;
    border-radius: 9px;
}
QPlainTextEdit#scriptEdit {
    background: transparent; border: 0; padding: 2px;
    color: #34342c; font-size: 13px; selection-background-color: #d5e3d8;
}
QToolButton#closeBtn {
    border: 0; background: transparent; color: #97917f;
    font-size: 15px; border-radius: 9px;
}
QToolButton#closeBtn:hover { background: #eee8db; color: #585345; }

#logCard { background: #2b2b25; border-radius: 14px; }
QPlainTextEdit#log {
    background: transparent; border: 0; color: #d8d3c6;
    font-family: "Cascadia Mono", "Consolas", "Microsoft YaHei UI";
    font-size: 12px;
    selection-background-color: #46584a;
}
QPlainTextEdit#log QScrollBar:vertical {
    background: transparent; width: 7px; margin: 2px;
}
QPlainTextEdit#log QScrollBar::handle:vertical {
    background: #4c4c42; border-radius: 3px; min-height: 24px;
}
QPlainTextEdit#log QScrollBar::handle:vertical:hover { background: #5d5d52; }
QPlainTextEdit#log QScrollBar::add-line:vertical,
QPlainTextEdit#log QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:vertical { background: transparent; width: 8px; margin: 2px 1px; }
QScrollBar::handle:vertical {
    background: #d9d2c3; border-radius: 4px; min-height: 32px;
}
QScrollBar::handle:vertical:hover { background: #cbc3b2; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

#dialog { background: #f6f2ea; }
QPlainTextEdit#dialogEdit {
    background: #fffdf8; border: 1px solid #e3dccd; border-radius: 9px;
    padding: 9px; color: #2f2f28; font-size: 13px;
    selection-background-color: #d5e3d8;
}
QPlainTextEdit#dialogEdit:focus { border: 1px solid #a8bead; }

QToolTip {
    background: #2b2b25; color: #e9e4d7;
    border: 1px solid #45453b; padding: 5px 8px;
}
"""


# ---------------------------------------------------------------- helpers
def make_font(families, size, weight=QFont.Weight.Normal, spacing: float = 0.0) -> QFont:
    font = QFont()
    font.setFamilies(families)
    font.setPixelSize(size)
    font.setWeight(weight)
    if spacing:
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    return font


def clamp_float(value, default: float, lo: float, hi: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number:  # NaN
        return default
    return max(lo, min(hi, number))


def clamp_int(value, default: int, lo: int, hi: int) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, number))


def format_multiplier(value: float) -> str:
    return f"{value:g}"


def load_config() -> dict:
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return cfg
    if not isinstance(raw, dict):
        return cfg

    scripts = raw.get("scripts")
    if isinstance(scripts, list):
        cfg["scripts"] = [str(item).strip() for item in scripts if str(item).strip()]

    exclusions = raw.get("exclusions")
    if isinstance(exclusions, list):
        cfg["exclusions"] = [str(item).strip() for item in exclusions if str(item).strip()]

    cfg["multiplier"] = clamp_float(raw.get("multiplier"), 1.1, 0.1, 10.0)
    cfg["quote_interval"] = clamp_int(raw.get("quote_interval"), 30, 1, 3600)
    cfg["detect_interval"] = clamp_int(raw.get("detect_interval"), 20, 1, 3600)
    cfg["auto_submit"] = bool(raw.get("auto_submit", True))
    return cfg


def make_card() -> tuple[QFrame, QVBoxLayout]:
    card = QFrame()
    card.setObjectName("card")
    shadow = QGraphicsDropShadowEffect(card)
    shadow.setBlurRadius(26)
    shadow.setOffset(0, 6)
    shadow.setColor(QColor(70, 58, 32, 22))
    card.setGraphicsEffect(shadow)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(15, 13, 15, 14)
    layout.setSpacing(8)
    return card, layout


def serif_label(text: str, size: int = 18) -> QLabel:
    label = QLabel(text)
    label.setFont(make_font(SERIF, size, QFont.Weight.DemiBold))
    return label


def small_label(text: str, object_name: str = "hint") -> QLabel:
    label = QLabel(text)
    label.setObjectName(object_name)
    return label


def add_card_header(layout: QVBoxLayout, kicker: str, title: str, trailing: QWidget | None = None):
    row = QHBoxLayout()
    row.setSpacing(10)
    title_box = QVBoxLayout()
    title_box.setSpacing(1)
    title_box.addWidget(small_label(kicker, "kicker"))
    title_box.addWidget(serif_label(title))
    row.addLayout(title_box)
    row.addStretch(1)
    if trailing is not None:
        row.addWidget(trailing, 0, Qt.AlignmentFlag.AlignTop)
    layout.addLayout(row)


def add_field_label(layout: QVBoxLayout, text: str):
    layout.addWidget(small_label(text, "fieldLabel"))


def numeric_field(value: str, validator) -> QLineEdit:
    field = QLineEdit(value)
    field.setObjectName("field")
    field.setMinimumHeight(33)
    field.setValidator(validator)
    return field


# ---------------------------------------------------------------- widgets
class LogoWidget(QWidget):
    """44px 圆角品牌标：深绿底 + 米白价签。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 44)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#15382a"))
        painter.drawRoundedRect(QRectF(0, 0, 44, 44), 12, 12)

        painter.setBrush(QColor("#f7f2e6"))
        painter.drawRoundedRect(QRectF(10.5, 10, 23, 18), 5.5, 5.5)
        tail = QPainterPath()
        tail.moveTo(15, 26)
        tail.lineTo(15, 33)
        tail.lineTo(22, 26)
        tail.closeSubpath()
        painter.drawPath(tail)

        painter.setPen(QColor("#15382a"))
        painter.setFont(make_font(["Segoe UI", "Arial"], 11, QFont.Weight.Bold))
        painter.drawText(QRectF(10.5, 9, 23, 19), Qt.AlignmentFlag.AlignCenter, "¥")


class Indicator(QWidget):
    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(16, 16)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0.8, 0.8, self.width() - 1.6, self.height() - 1.6)
        box = QPainterPath()
        box.addRoundedRect(rect, 4.5, 4.5)

        if self._checked:
            painter.fillPath(box, QColor("#1d4838"))
            pen = QPen(QColor("#fffdf7"), 1.7)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            check = QPainterPath()
            check.moveTo(4.2, 8.2)
            check.lineTo(6.9, 10.8)
            check.lineTo(11.8, 5.6)
            painter.drawPath(check)
        else:
            painter.setPen(QPen(QColor("#c6bfae"), 1.2))
            painter.setBrush(QColor("#fffdf8"))
            painter.drawPath(box)


class CheckLine(QWidget):
    """自绘勾选行：主标题 + 灰色说明，整行可点击。"""

    toggled = Signal(bool)

    def __init__(self, title: str, subtitle: str = "", checked: bool = True, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(32)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 2, 0, 2)
        row.setSpacing(9)
        self.indicator = Indicator(checked)
        row.addWidget(self.indicator, 0, Qt.AlignmentFlag.AlignTop)

        texts = QVBoxLayout()
        texts.setContentsMargins(0, 0, 0, 0)
        texts.setSpacing(1)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("checkTitle")
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        texts.addWidget(self.title_label)
        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setObjectName("checkSub")
            self.subtitle_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            texts.addWidget(self.subtitle_label)
        row.addLayout(texts, 1)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        checked = bool(checked)
        if self._checked == checked:
            return
        self._checked = checked
        self.indicator.setChecked(checked)
        self.toggled.emit(checked)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(
            event.position().toPoint()
        ):
            self.setChecked(not self._checked)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.setChecked(not self._checked)
            event.accept()
            return
        super().keyPressEvent(event)


class StatBox(QFrame):
    def __init__(self, caption: str, value: int = 0, parent=None):
        super().__init__(parent)
        self.setObjectName("stat")
        self.setMinimumHeight(48)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 5, 6, 6)
        layout.setSpacing(0)
        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("statValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caption_label = QLabel(caption)
        caption_label.setObjectName("statCaption")
        caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)
        layout.addWidget(caption_label)

    def set_value(self, value: int):
        self.value_label.setText(str(value))


class ScriptRow(QFrame):
    removed = Signal(object)

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("scriptRow")
        self.setMinimumHeight(52)

        row = QHBoxLayout(self)
        row.setContentsMargins(9, 6, 5, 6)
        row.setSpacing(2)

        self.edit = QPlainTextEdit()
        self.edit.setObjectName("scriptEdit")
        self.edit.setPlainText(text)
        self.edit.setPlaceholderText("输入自动发送的话术…")
        self.edit.setFixedHeight(40)
        self.edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.edit.setTabChangesFocus(True)
        self.edit.document().setDocumentMargin(0)
        row.addWidget(self.edit, 1)

        close_btn = QToolButton()
        close_btn.setObjectName("closeBtn")
        close_btn.setText("×")
        close_btn.setFixedSize(18, 18)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setToolTip("移除这条话术")
        close_btn.clicked.connect(lambda: self.removed.emit(self))
        row.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignTop)


class ExclusionDialog(QDialog):
    def __init__(self, rules: list[str], parent=None):
        super().__init__(parent)
        self.setObjectName("dialog")
        self.setWindowTitle("设置排除规则")
        self.setModal(True)
        self.resize(430, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(11)

        layout.addWidget(serif_label("设置排除规则", 17))
        desc = small_label("每行一个关键字，命中后自动略过该报价。")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.editor = QPlainTextEdit()
        self.editor.setObjectName("dialogEdit")
        self.editor.setPlaceholderText("例如：\n黑卡\n无库存\n面议")
        self.editor.setPlainText("\n".join(rules))
        layout.addWidget(self.editor, 1)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        footer.addStretch(1)
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("ghostBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("保存规则")
        save_btn.setObjectName("primaryBtn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        footer.addWidget(cancel_btn)
        footer.addWidget(save_btn)
        layout.addLayout(footer)

    def rules(self) -> list[str]:
        result = []
        for line in self.editor.toPlainText().splitlines():
            keyword = line.strip()
            if keyword and keyword not in result:
                result.append(keyword)
        return result


# ---------------------------------------------------------------- main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("7881 自动报价")
        self.setWindowIcon(make_app_icon())
        self.setMinimumSize(800, 714)

        self._rng = random.Random()
        self._saved_config = load_config()
        self._exclusions: list[str] = list(self._saved_config["exclusions"])
        self._script_rows: list[ScriptRow] = []
        self._stat_boxes: dict[str, StatBox] = {}
        self._stats = {"报价": 0, "略过": 0, "追求": 0, "排除": 0, "同意": 0}
        self._running = False
        self._session_start: float | None = None
        self._last_quote_ts = 0.0

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll)
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._hide_toast)

        self._build_ui()
        self._apply_config(self._saved_config)
        self._center_on_screen()
        self._write_initial_log()
        QTimer.singleShot(0, self._ensure_height_fits)

    # ------------------------------------------------------------ ui
    def _build_ui(self):
        root = QFrame()
        root.setObjectName("root")
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(26, 16, 26, 20)
        root_layout.setSpacing(14)
        root_layout.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._build_left_column(), 0)
        body.addWidget(self._build_right_column(), 1)
        root_layout.addLayout(body, 1)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setMinimumHeight(50)
        row = QHBoxLayout(header)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(11)

        row.addWidget(LogoWidget())

        titles = QVBoxLayout()
        titles.setContentsMargins(0, 0, 0, 0)
        titles.setSpacing(1)
        title = QLabel("7881 自动报价")
        title.setFont(make_font(SANS, 22, QFont.Weight.Bold))
        subtitle = QLabel("SERVICE AUTO-QUOTE")
        subtitle.setObjectName("serviceTag")
        subtitle.setFont(make_font(SANS, 9, QFont.Weight.DemiBold, spacing=2.0))
        titles.addWidget(title)
        titles.addWidget(subtitle)
        row.addLayout(titles)
        row.addStretch(1)
        return header

    def _build_left_column(self) -> QWidget:
        left = QWidget()
        left.setFixedWidth(268)
        layout = QVBoxLayout(left)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_run_card())
        layout.addWidget(self._build_speed_card())
        layout.addStretch(1)
        return left

    def _build_run_card(self) -> QWidget:
        card, layout = make_card()
        add_card_header(layout, "运行控制", "开始 / 停止")

        self._run_btn = QPushButton("开始运行")
        self._run_btn.setObjectName("startBtn")
        self._run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._run_btn.setMinimumHeight(36)
        self._run_btn.clicked.connect(self._toggle_running)
        layout.addWidget(self._run_btn)

        self._auto_check = CheckLine(
            "自动提交报价并发送话术", "先提交最优价，再发一条招呼", checked=True
        )
        layout.addWidget(self._auto_check)

        self._exclude_btn = QPushButton("不想要规则 · 设置排除")
        self._exclude_btn.setObjectName("ghostBtn")
        self._exclude_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._exclude_btn.setMinimumHeight(32)
        self._exclude_btn.clicked.connect(self._open_exclusion_dialog)
        layout.addWidget(self._exclude_btn)

        self._stat_boxes["报价"] = StatBox("已报价")
        self._stat_boxes["略过"] = StatBox("已略过")
        self._stat_boxes["追求"] = StatBox("追求")
        self._stat_boxes["排除"] = StatBox("已排除")
        self._stat_boxes["同意"] = StatBox("被同意")

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid.addWidget(self._stat_boxes["报价"], 0, 0)
        grid.addWidget(self._stat_boxes["略过"], 0, 1)
        grid.addWidget(self._stat_boxes["追求"], 1, 0)
        grid.addWidget(self._stat_boxes["排除"], 1, 1)
        grid.addWidget(self._stat_boxes["同意"], 2, 0, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        return card

    def _build_speed_card(self) -> QWidget:
        card, layout = make_card()
        add_card_header(layout, "节奏与倍数", "速度设置")

        add_field_label(layout, "报价倍数")
        self._mult_field = numeric_field(
            "1.1", QDoubleValidator(0.1, 10.0, 2, self)
        )
        layout.addWidget(self._mult_field)
        layout.addWidget(small_label("最终报价 = 底价 × 倍数，实时生效"))

        self._quote_field = numeric_field("30", QIntValidator(1, 3600, self))
        self._detect_field = numeric_field("20", QIntValidator(1, 3600, self))
        self._detect_field.editingFinished.connect(self._sync_poll_interval)

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
        return card

    def _build_right_column(self) -> QWidget:
        right = QWidget()
        layout = QVBoxLayout(right)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self._build_scripts_card(), 0)
        layout.addWidget(self._build_log_card(), 1)
        return right

    def _build_scripts_card(self) -> QWidget:
        card, layout = make_card()

        add_btn = QPushButton("+ 添加一条")
        add_btn.setObjectName("ghostBtn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda: self._add_script_row())
        add_card_header(layout, "报价成功后自动发送", "话术", trailing=add_btn)

        self._rows_host = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_host)
        self._rows_layout.setContentsMargins(0, 2, 0, 0)
        self._rows_layout.setSpacing(8)
        layout.addWidget(self._rows_host)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 4, 0, 0)
        footer.setSpacing(4)
        save_btn = QPushButton("保存配置")
        save_btn.setObjectName("primaryBtn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_config)
        restore_btn = QPushButton("还原")
        restore_btn.setObjectName("linkBtn")
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_btn.clicked.connect(self._restore_config)
        self._toast = QLabel("已保存")
        self._toast.setObjectName("savedToast")
        self._toast.hide()
        footer.addWidget(save_btn)
        footer.addWidget(restore_btn)
        footer.addStretch(1)
        footer.addWidget(self._toast)
        layout.addLayout(footer)
        return card

    def _build_log_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("logCard")
        card.setMinimumHeight(250)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(30, 25, 15, 42))
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 13, 14, 13)
        layout.setSpacing(7)

        header = QHBoxLayout()
        header.setSpacing(8)
        title = QLabel("运行日志")
        title.setObjectName("logTitle")
        connected = QLabel('● 已连接')
        connected.setObjectName("logConn")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(connected)
        layout.addLayout(header)

        self._log_view = QPlainTextEdit()
        self._log_view.setObjectName("log")
        self._log_view.setReadOnly(True)
        self._log_view.setFrameShape(QFrame.Shape.NoFrame)
        self._log_view.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self._log_view.document().setDocumentMargin(0)
        self._log_view.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self._log_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._log_view.setMaximumBlockCount(1000)
        self._log_view.setUndoRedoEnabled(False)
        layout.addWidget(self._log_view, 1)
        return card

    # ------------------------------------------------------------ config <-> ui
    def _apply_config(self, cfg: dict):
        self._auto_check.setChecked(bool(cfg["auto_submit"]))
        self._mult_field.setText(format_multiplier(cfg["multiplier"]))
        self._quote_field.setText(str(cfg["quote_interval"]))
        self._detect_field.setText(str(cfg["detect_interval"]))
        self._exclusions = list(cfg.get("exclusions", []))
        self._refresh_exclude_button()
        self._rebuild_script_rows(cfg.get("scripts", []))

    def _collect_config(self) -> dict:
        multiplier = clamp_float(self._mult_field.text(), 1.1, 0.1, 10.0)
        multiplier = round(multiplier, 2)
        quote_interval = clamp_int(self._quote_field.text(), 30, 1, 3600)
        detect_interval = clamp_int(self._detect_field.text(), 20, 1, 3600)

        self._mult_field.setText(format_multiplier(multiplier))
        self._quote_field.setText(str(quote_interval))
        self._detect_field.setText(str(detect_interval))

        return {
            "scripts": self._script_texts(),
            "multiplier": multiplier,
            "quote_interval": quote_interval,
            "detect_interval": detect_interval,
            "auto_submit": self._auto_check.isChecked(),
            "exclusions": list(self._exclusions),
        }

    def _save_config(self):
        cfg = self._collect_config()
        try:
            CONFIG_PATH.write_text(
                json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            self._show_toast("保存失败", ok=False)
            self._log(f"配置保存失败：{exc}", "err")
            return

        self._saved_config = cfg
        self._show_toast("已保存")
        self._log(
            f"配置已保存 · 倍数 ×{format_multiplier(cfg['multiplier'])} · "
            f"话术 {len(cfg['scripts'])} 条",
            "muted",
        )
        if not cfg["scripts"]:
            self._log("话术库为空，报价时不会发送任何话术", "warn")
        self._sync_poll_interval()

    def _restore_config(self):
        self._apply_config(self._saved_config)
        self._show_toast("已还原")

    def _show_toast(self, text: str, ok: bool = True):
        self._toast.setText(text)
        self._toast.setStyleSheet("color: #377456;" if ok else "color: #a2544a;")
        self._toast.show()
        self._toast_timer.start(2200)

    def _hide_toast(self):
        self._toast.hide()

    # ------------------------------------------------------------ scripts
    def _rebuild_script_rows(self, texts: list[str]):
        for row in self._script_rows:
            self._rows_layout.removeWidget(row)
            row.deleteLater()
        self._script_rows.clear()

        for text in texts:
            self._add_script_row(text, focus=False)

    def _add_script_row(self, text: str = "", focus: bool = True) -> ScriptRow | None:
        row = ScriptRow(text)
        row.removed.connect(self._remove_script_row)
        self._rows_layout.addWidget(row)
        self._script_rows.append(row)
        if focus:
            QTimer.singleShot(0, row.edit.setFocus)
            QTimer.singleShot(0, self._ensure_height_fits)
        return row

    def _remove_script_row(self, row: ScriptRow):
        if row in self._script_rows:
            self._script_rows.remove(row)
        self._rows_layout.removeWidget(row)
        row.deleteLater()

    def _script_texts(self) -> list[str]:
        texts = []
        for row in self._script_rows:
            text = row.edit.toPlainText().strip()
            if text:
                texts.append(text)
        return texts

    # ------------------------------------------------------------ exclusions
    def _open_exclusion_dialog(self):
        dialog = ExclusionDialog(self._exclusions, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._exclusions = dialog.rules()
            self._refresh_exclude_button()
            self._log(f"排除规则已更新 · 共 {len(self._exclusions)} 条", "muted")

    def _refresh_exclude_button(self):
        count = len(self._exclusions)
        self._exclude_btn.setText(
            "不想要规则 · 设置排除" + (f"（{count}）" if count else "")
        )
        self._exclude_btn.setToolTip(
            "；".join(self._exclusions) if self._exclusions else "尚未设置排除规则"
        )

    # ------------------------------------------------------------ run control
    def _toggle_running(self):
        if self._running:
            self._stop_run()
        else:
            self._start_run()

    def _start_run(self):
        cfg = self._collect_config()
        self._running = True
        self._session_start = time.monotonic()
        self._last_quote_ts = 0.0
        self._set_run_button(running=True)

        self._log(
            f"开始运行 · 倍数 ×{format_multiplier(cfg['multiplier'])} · "
            f"报价间隔 {cfg['quote_interval']} 秒 · 检测间隔 {cfg['detect_interval']} 秒",
            "ok",
        )
        if not cfg["auto_submit"]:
            self._log("自动提交已关闭，当前只检测不报价", "warn")
        elif not cfg["scripts"]:
            self._log("话术库为空，报价后不会发送话术", "warn")

        self._poll_timer.start(cfg["detect_interval"] * 1000)
        self._poll()

    def _stop_run(self):
        self._running = False
        self._poll_timer.stop()
        self._set_run_button(running=False)
        elapsed = 0
        if self._session_start is not None:
            elapsed = int(time.monotonic() - self._session_start)
        minutes, seconds = divmod(elapsed, 60)
        self._log(f"已停止运行 · 本次运行 {minutes:02d}:{seconds:02d}", "muted")

    def _set_run_button(self, running: bool):
        self._run_btn.setObjectName("stopBtn" if running else "startBtn")
        self._run_btn.setText("停止" if running else "开始运行")
        style = self._run_btn.style()
        style.unpolish(self._run_btn)
        style.polish(self._run_btn)

    def _sync_poll_interval(self):
        if self._running:
            detect = clamp_int(self._detect_field.text(), 20, 1, 3600)
            self._poll_timer.setInterval(detect * 1000)

    # ------------------------------------------------------------ simulation
    def _poll(self):
        if not self._running:
            return

        self._bump("追求", self._rng.randint(1, 5))

        if self._exclusions and self._rng.random() < 0.30:
            rule = self._rng.choice(self._exclusions)
            self._bump("排除", 1)
            self._log(f"已排除：命中规则「{rule}」", "warn")
            return

        if not self._auto_check.isChecked():
            self._bump("略过", 1)
            self._log("自动提交已关闭 · 本轮仅检测", "muted")
            return

        if self._rng.random() < 0.55:
            self._log(
                f"轮询完成 · 扫描到 {self._rng.randint(8, 60)} 条在售报价", "muted"
            )

        now = time.monotonic()
        quote_interval = clamp_int(self._quote_field.text(), 30, 1, 3600)
        if self._last_quote_ts == 0.0 or now - self._last_quote_ts >= quote_interval:
            self._quote(now)

    def _quote(self, now: float):
        base = self._rng.randint(60, 5200)
        multiplier = clamp_float(self._mult_field.text(), 1.1, 0.1, 10.0)
        final = max(1, round(base * multiplier))

        if self._rng.random() < 0.16:
            self._bump("略过", 1)
            self._log(f"已略过：底价 ¥{final} 高于当前成交区间", "warn")
        else:
            self._bump("报价", 1)
            self._log(
                f"已报价 ¥{final}（底价 ¥{base} × {format_multiplier(multiplier)}）",
                "ok",
            )
            scripts = self._script_texts()
            if scripts:
                self._log(f"话术已发送 {len(scripts)}/{len(scripts)}", "muted")

            if self._rng.random() < 0.12:
                self._bump("同意", 1)
                deal = final + self._rng.randint(0, 60)
                self._log(f"买家已同意 · 成交价 ¥{deal}", "ok")

        self._last_quote_ts = now

    def _bump(self, key: str, amount: int = 1):
        self._stats[key] += amount
        self._stat_boxes[key].set_value(self._stats[key])

    # ------------------------------------------------------------ log
    def _log(self, message: str, kind: str = "info"):
        stamp = datetime.now().strftime("%H:%M:%S")
        color = LOG_COLORS.get(kind, LOG_COLORS["info"])
        safe = html.escape(message).replace("\n", "<br>")
        self._log_view.appendHtml(
            f'<span style="color:#77726a;">{stamp}</span>&nbsp;&nbsp;'
            f'<span style="color:{color};">{safe}</span>'
        )
        scrollbar = self._log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _write_initial_log(self):
        cfg = self._saved_config
        self._log("客户端已连接 · 报价通道就绪", "ok")
        self._log(
            f"配置已载入 · 倍数 ×{format_multiplier(cfg['multiplier'])} · "
            f"话术 {len(cfg['scripts'])} 条",
            "muted",
        )
        self._log("等待开始运行", "muted")

    # ------------------------------------------------------------ layout
    def _center_on_screen(self):
        width, height = 800, 730
        self.resize(width, height)
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        self.move(
            available.x() + (available.width() - width) // 2,
            available.y() + (available.height() - height) // 2,
        )

    def _ensure_height_fits(self):
        """新增话术后让窗口自动长高，避免内容被裁切。"""
        layout = self.centralWidget().layout()
        if layout is not None:
            layout.activate()
        needed = max(714, self.minimumSizeHint().height())
        screen = QApplication.primaryScreen()
        if screen is not None:
            needed = min(needed, screen.availableGeometry().height() - 60)
        if needed > self.minimumHeight():
            self.setMinimumHeight(needed)
        if self.height() < needed:
            self.resize(self.width(), needed)


def make_app_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#15382a"))
    painter.drawRoundedRect(QRectF(2, 2, 60, 60), 16, 16)

    painter.setBrush(QColor("#f7f2e6"))
    painter.drawRoundedRect(QRectF(15, 14, 34, 27), 8, 8)
    tail = QPainterPath()
    tail.moveTo(22, 38)
    tail.lineTo(22, 49)
    tail.lineTo(33, 38)
    tail.closeSubpath()
    painter.drawPath(tail)

    painter.setPen(QColor("#15382a"))
    painter.setFont(make_font(["Segoe UI", "Arial"], 16, QFont.Weight.Bold))
    painter.drawText(QRectF(15, 13, 34, 28), Qt.AlignmentFlag.AlignCenter, "¥")
    painter.end()
    return QIcon(pixmap)


def main():
    QApplication.setApplicationName("7881 自动报价")
    QApplication.setApplicationDisplayName("7881 自动报价")
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(make_font(SANS, 13))
    app.setStyleSheet(QSS)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
