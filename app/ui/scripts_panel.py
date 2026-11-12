"""话术管理卡片：增删、保存与还原入口。"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets import ScriptRow, add_card_header, prepare_card


class ScriptsPanel(QFrame):
    save_requested = Signal()
    restore_requested = Signal()
    rows_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = prepare_card(self)

        add_btn = QPushButton("+ 添加一条")
        add_btn.setObjectName("ghostBtn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda: self.add_empty_row())
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
        save_btn.clicked.connect(lambda: self.save_requested.emit())
        restore_btn = QPushButton("还原")
        restore_btn.setObjectName("linkBtn")
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_btn.clicked.connect(lambda: self.restore_requested.emit())
        self._toast = QLabel("已保存")
        self._toast.setObjectName("savedToast")
        self._toast.hide()

        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._toast.hide)

        footer.addWidget(save_btn)
        footer.addWidget(restore_btn)
        footer.addStretch(1)
        footer.addWidget(self._toast)
        layout.addLayout(footer)

        self._rows: list[ScriptRow] = []

    def texts(self) -> list[str]:
        texts = []
        for row in self._rows:
            text = row.edit.toPlainText().strip()
            if text:
                texts.append(text)
        return texts

    def set_texts(self, texts: list[str]):
        for row in self._rows:
            self._rows_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()
        for text in texts:
            self._add_row(text)

    def add_empty_row(self):
        self._add_row("", user=True)

    def show_toast(self, text: str, ok: bool = True):
        self._toast.setText(text)
        self._toast.setStyleSheet("color: #377456;" if ok else "color: #a2544a;")
        self._toast.show()
        self._toast_timer.start(2200)

    def _add_row(self, text: str = "", user: bool = False):
        row = ScriptRow(text)
        row.removed.connect(self._remove_row)
        self._rows_layout.addWidget(row)
        self._rows.append(row)
        if user:
            QTimer.singleShot(0, row.edit.setFocus)
            self.rows_changed.emit()

    def _remove_row(self, row: ScriptRow):
        if row in self._rows:
            self._rows.remove(row)
        self._rows_layout.removeWidget(row)
        row.deleteLater()
