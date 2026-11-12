"""弹窗：排除规则设置与 7881 官方登录页。"""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from app.hall import HALL_URL
from app.ui.widgets import serif_label, small_label


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


class HallBrowserDialog(QDialog):
    """内嵌 7881 官方登录页，登录后自动进入回收报价大厅。"""

    logged_in = Signal()

    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(parent)
        self.setObjectName("dialog")
        self.setWindowTitle("7881 登录 · 回收报价大厅")
        self.resize(1160, 840)
        self.setMinimumSize(900, 680)

        self._login_notified = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.view = QWebEngineView(self)
        self.view.setPage(QWebEnginePage(profile, self.view))
        self.view.setZoomFactor(0.85)
        layout.addWidget(self.view, 1)

        bar = QFrame()
        bar.setObjectName("browserBar")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(14, 9, 14, 9)
        bar_layout.setSpacing(8)

        self.status = QLabel("正在打开 7881 登录页…")
        self.status.setObjectName("browserStatus")
        self.status.setWordWrap(False)
        bar_layout.addWidget(self.status, 1)

        reload_btn = QPushButton("刷新页面")
        reload_btn.setObjectName("ghostBtn")
        reload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reload_btn.clicked.connect(self.view.reload)
        bar_layout.addWidget(reload_btn)

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("ghostBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        bar_layout.addWidget(close_btn)

        layout.addWidget(bar)

        self.view.urlChanged.connect(self._on_url_changed)
        self.view.loadFinished.connect(self._on_load_finished)
        self.view.load(QUrl(HALL_URL))

    def _on_url_changed(self, url: QUrl):
        host = url.host().lower()
        path = url.path().lower()
        if "passport" in host or "touristlogin" in path or "login" in path:
            self.status.setText(
                "请在页面中完成登录（扫码 / 短信 / 密码均可），本应用不保存账号密码"
            )
        elif host.endswith("i.7881.com"):
            self.status.setText("正在加载 7881 商家中心…")
        else:
            self.status.setText("正在加载 7881 …")

    def _on_load_finished(self, ok: bool):
        if not ok:
            if not self._login_notified:
                self.status.setText("页面加载失败，请检查网络后点击「刷新页面」")
            return

        url = self.view.url()
        host = url.host().lower()
        path = url.path().lower()
        if host.endswith("i.7881.com"):
            self.status.setText(
                "登录成功 · 已开始读取回收报价大厅，数据会显示在运行日志"
            )
            if not self._login_notified:
                self._login_notified = True
                self.logged_in.emit()
        elif "passport" in host or "touristlogin" in path or "login" in path:
            self.status.setText(
                "请在页面中完成登录（扫码 / 短信 / 密码均可），本应用不保存账号密码"
            )
