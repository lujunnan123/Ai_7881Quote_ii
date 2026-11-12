"""7881 回收报价大厅：持久会话与后台抓取服务。"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QTimer, QUrl, Signal
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView

from app.config import WEB_PROFILE_DIR

HALL_URL = "https://i.7881.com/merchant/recycle-hall"
HALL_JS = (
    Path(__file__).resolve().parent / "resources" / "hall_extract.js"
).read_text(encoding="utf-8")


class HallService(QObject):
    """管理 7881 登录 Cookie，并在隐藏页面中读取回收报价大厅列表。"""

    log_message = Signal(str, str)
    fetching_changed = Signal(bool)
    session_changed = Signal(str)  # "logged_in" / "expired"
    data_ready = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._profile: QWebEngineProfile | None = None
        self._view: QWebEngineView | None = None
        self._page: QWebEnginePage | None = None
        self._attempt = 0
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(self._on_timeout)

    # ------------------------------------------------------------ session
    def web_profile(self) -> QWebEngineProfile:
        if self._profile is None:
            WEB_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
            profile = QWebEngineProfile("7881_auto_quote", self)
            profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
            )
            profile.setPersistentStoragePath(str(WEB_PROFILE_DIR))
            profile.setCachePath(str(WEB_PROFILE_DIR / "cache"))
            self._profile = profile
        return self._profile

    # ------------------------------------------------------------ fetch
    @property
    def busy(self) -> bool:
        return self._page is not None

    def fetch(self):
        if self._page is not None:
            self.log_message.emit("正在抓取回收报价大厅，请稍候…", "muted")
            return

        self.fetching_changed.emit(True)
        self.log_message.emit("正在连接 7881 · 回收报价大厅…", "muted")

        view = QWebEngineView()
        view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        page = QWebEnginePage(self.web_profile(), view)
        view.setPage(page)
        view.resize(1280, 900)
        view.show()  # 只给页面真实视口，不显示窗口

        self._view = view
        self._page = page
        self._attempt = 0
        self._timeout.start(25000)

        page.loadFinished.connect(self._on_load_finished)
        page.load(QUrl(HALL_URL))

    def _on_load_finished(self, ok: bool):
        page = self._page
        if page is None:
            return

        url = page.url()
        host = url.host().lower()
        path = url.path().lower()

        if not ok:
            self.log_message.emit("回收报价大厅页面加载失败，请检查网络", "err")
            self.session_changed.emit("expired")
            self._finish()
            return

        if "passport" in host or "touristlogin" in path or "login" in path:
            self._warn_login_expired()
            self._finish()
            return

        QTimer.singleShot(1600, lambda: self._extract(page))

    def _extract(self, page: QWebEnginePage):
        if page is not self._page:
            return
        page.runJavaScript(HALL_JS, lambda result: self._on_result(page, result))

    def _on_result(self, page: QWebEnginePage, result):
        if page is not self._page:
            return

        if isinstance(result, str):
            try:
                result = json.loads(result) if result else {}
            except ValueError:
                result = {}
        if not isinstance(result, dict):
            result = {}

        self._attempt += 1
        if result.get("ok") or result.get("list"):
            self._handle_result(result)
            self._finish()
            return

        if self._attempt < 7:
            QTimer.singleShot(1500, lambda: self._extract(page))
            return

        self._handle_result(result)
        self._finish()

    def _handle_result(self, result: dict):
        url = str(result.get("url") or "")
        if "passport.7881.com" in url or "touristlogin" in url:
            self._warn_login_expired()
            return

        if not result.get("ok"):
            notice = str(result.get("notice") or "").strip()
            title = str(result.get("title") or "").strip()
            if notice:
                self.log_message.emit(f"回收报价大厅：{notice}", "warn")
            else:
                detail = f"（{title}）" if title else ""
                self.log_message.emit(f"回收报价大厅数据读取失败{detail}", "err")
            return

        self.session_changed.emit("logged_in")
        self.data_ready.emit(result)

    def _warn_login_expired(self):
        self.log_message.emit(
            "回收报价大厅：登录状态已失效，请点击右上角「登录 7881」重新登录",
            "warn",
        )
        self.session_changed.emit("expired")

    def _on_timeout(self):
        if self._page is None:
            return
        self.log_message.emit("回收报价大厅读取超时，请稍后重试", "warn")
        self._finish()

    def _finish(self):
        view = self._view
        page = self._page
        self._view = None
        self._page = None
        self._timeout.stop()
        self.fetching_changed.emit(False)

        if view is not None:
            view.close()
            view.deleteLater()
        if page is not None:
            page.deleteLater()
