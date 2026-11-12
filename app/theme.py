"""字体、样式表与品牌图标。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPixmap

SANS = ["Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", "Segoe UI"]
SERIF = ["Source Han Serif SC", "Noto Serif SC", "Songti SC", "SimSun"]
MONO = ["Cascadia Mono", "Consolas", "Courier New"]

RESOURCE_DIR = Path(__file__).resolve().parent / "resources"


def load_stylesheet() -> str:
    return (RESOURCE_DIR / "style.qss").read_text(encoding="utf-8")


def make_font(
    families, size, weight=QFont.Weight.Normal, spacing: float = 0.0
) -> QFont:
    font = QFont()
    font.setFamilies(families)
    font.setPixelSize(size)
    font.setWeight(weight)
    if spacing:
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    return font


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
