"""主窗口：组装面板、连接引擎与抓取服务。"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_NAME, format_multiplier, load_config, save_config
from app.engine import QuoteEngine, RuntimeSettings
from app.hall import HallService
from app.theme import SANS, make_app_icon, make_font
from app.ui.dialogs import ExclusionDialog, HallBrowserDialog
from app.ui.log_panel import LogPanel
from app.ui.run_panel import RunPanel
from app.ui.scripts_panel import ScriptsPanel
from app.ui.speed_panel import SpeedPanel
from app.ui.widgets import LogoWidget
from app.valuation import ValuationService


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(make_app_icon())
        self.setMinimumSize(800, 714)

        self._saved_config = load_config()
        self._exclusions = list(self._saved_config["exclusions"])

        self._build_ui()

        self._engine = QuoteEngine(self._live_settings, self)
        self._hall = HallService(self)
        self._valuation = ValuationService(self)
        self._awaiting_hall = False
        self._wire_signals()

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
        title = QLabel(APP_NAME)
        title.setFont(make_font(SANS, 22, QFont.Weight.Bold))
        subtitle = QLabel("SERVICE AUTO-QUOTE")
        subtitle.setObjectName("serviceTag")
        subtitle.setFont(make_font(SANS, 9, QFont.Weight.DemiBold, spacing=2.0))
        titles.addWidget(title)
        titles.addWidget(subtitle)
        row.addLayout(titles)
        row.addStretch(1)

        self._login_btn = QPushButton("登录 7881")
        self._login_btn.setObjectName("ghostBtn")
        self._login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._login_btn.setToolTip("打开 7881 官方登录页，登录后自动进入回收报价大厅")

        self._estimate_btn = QPushButton("估价")
        self._estimate_btn.setObjectName("headerPrimary")
        self._estimate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._estimate_btn.setToolTip(
            "读取回收报价大厅前 10 条，调用估值接口并把价格输出到运行日志"
        )

        row.addWidget(self._login_btn)
        row.addWidget(self._estimate_btn)
        return header

    def _build_left_column(self) -> QWidget:
        left = QWidget()
        left.setFixedWidth(268)
        layout = QVBoxLayout(left)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self._run_panel = RunPanel()
        self._speed_panel = SpeedPanel()
        layout.addWidget(self._run_panel)
        layout.addWidget(self._speed_panel)
        layout.addStretch(1)
        return left

    def _build_right_column(self) -> QWidget:
        right = QWidget()
        layout = QVBoxLayout(right)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self._scripts_panel = ScriptsPanel()
        self._log_panel = LogPanel()
        layout.addWidget(self._scripts_panel, 0)
        layout.addWidget(self._log_panel, 1)
        return right

    def _wire_signals(self):
        self._run_panel.run_clicked.connect(self._engine.toggle)
        self._run_panel.exclude_clicked.connect(self._open_exclusion_dialog)
        self._engine.log_message.connect(self._log)
        self._engine.stats_changed.connect(self._run_panel.set_stats)
        self._engine.running_changed.connect(self._run_panel.set_running)
        self._speed_panel.detect_interval_edited.connect(
            self._engine.set_detect_interval
        )

        self._scripts_panel.save_requested.connect(self._save_config)
        self._scripts_panel.restore_requested.connect(self._restore_config)
        self._scripts_panel.rows_changed.connect(
            lambda: QTimer.singleShot(0, self._ensure_height_fits)
        )

        self._hall.log_message.connect(self._log)
        self._hall.fetching_changed.connect(self._on_hall_fetching)
        self._hall.session_changed.connect(self._on_session_changed)
        self._hall.data_ready.connect(self._on_hall_data)
        self._valuation.log_message.connect(self._log)
        self._valuation.busy_changed.connect(self._on_valuation_busy)
        self._login_btn.clicked.connect(self._open_hall_window)
        self._estimate_btn.clicked.connect(self._start_estimate)

    # ------------------------------------------------------------ config
    def _apply_config(self, cfg: dict):
        self._run_panel.set_auto_submit(cfg["auto_submit"])
        self._speed_panel.set_values(
            cfg["multiplier"], cfg["quote_interval"], cfg["detect_interval"]
        )
        self._exclusions = list(cfg.get("exclusions", []))
        self._run_panel.set_exclusion_rules(self._exclusions)
        self._scripts_panel.set_texts(cfg.get("scripts", []))

    def _collect_config(self) -> dict:
        multiplier, quote_interval, detect_interval = self._speed_panel.collect()
        return {
            "scripts": self._scripts_panel.texts(),
            "multiplier": multiplier,
            "quote_interval": quote_interval,
            "detect_interval": detect_interval,
            "auto_submit": self._run_panel.auto_submit(),
            "exclusions": list(self._exclusions),
        }

    def _live_settings(self) -> RuntimeSettings:
        return RuntimeSettings(
            multiplier=self._speed_panel.multiplier(),
            quote_interval=self._speed_panel.quote_interval(),
            detect_interval=self._speed_panel.detect_interval(),
            auto_submit=self._run_panel.auto_submit(),
            scripts=tuple(self._scripts_panel.texts()),
            exclusions=tuple(self._exclusions),
        )

    def _save_config(self):
        cfg = self._collect_config()
        try:
            save_config(cfg)
        except OSError as exc:
            self._scripts_panel.show_toast("保存失败", ok=False)
            self._log(f"配置保存失败：{exc}", "err")
            return

        self._saved_config = cfg
        self._scripts_panel.show_toast("已保存")
        self._log(
            f"配置已保存 · 倍数 ×{format_multiplier(cfg['multiplier'])} · "
            f"话术 {len(cfg['scripts'])} 条",
            "muted",
        )
        if not cfg["scripts"]:
            self._log("话术库为空，报价时不会发送任何话术", "warn")
        self._engine.set_detect_interval(cfg["detect_interval"])

    def _restore_config(self):
        self._apply_config(self._saved_config)
        self._scripts_panel.show_toast("已还原")
        self._engine.set_detect_interval(self._speed_panel.detect_interval())

    # ------------------------------------------------------------ exclusions
    def _open_exclusion_dialog(self):
        dialog = ExclusionDialog(self._exclusions, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._exclusions = dialog.rules()
            self._run_panel.set_exclusion_rules(self._exclusions)
            self._log(
                f"排除规则已更新 · 共 {len(self._exclusions)} 条", "muted"
            )

    # ------------------------------------------------------------ 7881 & valuation
    def _open_hall_window(self):
        dialog = HallBrowserDialog(self._hall.web_profile(), self)
        dialog.logged_in.connect(self._on_login_completed)
        dialog.exec()

    def _on_login_completed(self):
        self._login_btn.setText("账号已登录")
        self._log("登录成功 · 点击「估价」读取大厅前 10 条并计算估值", "muted")

    def _on_session_changed(self, state: str):
        self._login_btn.setText(
            "账号已登录" if state == "logged_in" else "登录 7881"
        )

    def _start_estimate(self):
        if self._awaiting_hall or self._valuation.busy or self._hall.busy:
            return
        self._awaiting_hall = True
        self._estimate_btn.setEnabled(False)
        self._estimate_btn.setText("估价中…")
        self._hall.fetch()

    def _on_hall_fetching(self, fetching: bool):
        if not fetching and self._awaiting_hall:
            # 大厅抓取失败/超时，没有数据可用于估价
            self._awaiting_hall = False
            self._finish_estimate()

    def _on_hall_data(self, result: dict):
        self._awaiting_hall = False

        items = result.get("list") or []
        total = result.get("total")
        total = int(total) if isinstance(total, (int, float)) else len(items)
        self._log(f"回收报价大厅 · 共 {total} 单 · 本页 {len(items)} 单", "ok")

        targets = [item for item in items[:10] if isinstance(item, dict)]
        if not targets:
            self._log("大厅当前没有可估价的订单", "muted")
            self._finish_estimate()
            return

        self._log(f"开始估价前 {len(targets)} 条…", "muted")
        self._valuation.estimate(targets)
        if not self._valuation.busy:
            self._finish_estimate()

    def _on_valuation_busy(self, busy: bool):
        if busy:
            self._estimate_btn.setEnabled(False)
            self._estimate_btn.setText("估价中…")
        else:
            self._finish_estimate()

    def _finish_estimate(self):
        self._awaiting_hall = False
        self._estimate_btn.setEnabled(True)
        self._estimate_btn.setText("估价")

    # ------------------------------------------------------------ log & layout
    def _log(self, message: str, kind: str = "info"):
        self._log_panel.append(message, kind)

    def _write_initial_log(self):
        cfg = self._saved_config
        self._log("客户端已连接 · 报价通道就绪", "ok")
        self._log(
            f"配置已载入 · 倍数 ×{format_multiplier(cfg['multiplier'])} · "
            f"话术 {len(cfg['scripts'])} 条",
            "muted",
        )
        self._log("等待开始运行", "muted")

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
