"""深色运行日志面板，负责时间戳、配色与自动滚动。"""

from __future__ import annotations

import html
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextOption
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)

LOG_COLORS = {
    "info": "#d8d3c6",
    "muted": "#9b968a",
    "ok": "#8cc79a",
    "warn": "#d9b271",
    "err": "#e08f84",
}


class LogPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logCard")
        self.setMinimumHeight(250)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(30, 25, 15, 42))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 13, 14, 13)
        layout.setSpacing(7)

        header = QHBoxLayout()
        header.setSpacing(8)
        title = QLabel("运行日志")
        title.setObjectName("logTitle")
        connected = QLabel("● 已连接")
        connected.setObjectName("logConn")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(connected)
        layout.addLayout(header)

        self.view = QPlainTextEdit()
        self.view.setObjectName("log")
        self.view.setReadOnly(True)
        self.view.setFrameShape(QFrame.Shape.NoFrame)
        self.view.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.view.document().setDocumentMargin(0)
        self.view.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setMaximumBlockCount(1000)
        self.view.setUndoRedoEnabled(False)
        layout.addWidget(self.view, 1)

    def append(self, message: str, kind: str = "info"):
        stamp = datetime.now().strftime("%H:%M:%S")
        color = LOG_COLORS.get(kind, LOG_COLORS["info"])
        safe = html.escape(message).replace("\n", "<br>")
        self.view.appendHtml(
            f'<span style="color:#77726a;">{stamp}</span>&nbsp;&nbsp;'
            f'<span style="color:{color};">{safe}</span>'
        )
        scrollbar = self.view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
