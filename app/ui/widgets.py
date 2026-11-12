"""可复用的基础控件、卡片布局与表单辅助函数。"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.theme import SERIF, make_font


def prepare_card(card: QFrame) -> QVBoxLayout:
    """给 QFrame 套上白底圆角卡片样式，并返回内容布局。"""
    card.setObjectName("card")
    shadow = QGraphicsDropShadowEffect(card)
    shadow.setBlurRadius(26)
    shadow.setOffset(0, 6)
    shadow.setColor(QColor(70, 58, 32, 22))
    card.setGraphicsEffect(shadow)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(15, 13, 15, 14)
    layout.setSpacing(8)
    return layout


def serif_label(text: str, size: int = 18) -> QLabel:
    label = QLabel(text)
    label.setFont(make_font(SERIF, size, QFont.Weight.DemiBold))
    return label


def small_label(text: str, object_name: str = "hint") -> QLabel:
    label = QLabel(text)
    label.setObjectName(object_name)
    return label


def add_card_header(
    layout: QVBoxLayout, kicker: str, title: str, trailing: QWidget | None = None
):
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
            self.subtitle_label.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents
            )
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
