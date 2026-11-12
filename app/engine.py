"""报价运行引擎：轮询、模拟报价、统计与日志信号。"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QObject, QTimer, Signal

from app.config import clamp_int, format_multiplier


@dataclass(frozen=True)
class RuntimeSettings:
    multiplier: float
    quote_interval: int
    detect_interval: int
    auto_submit: bool
    scripts: tuple[str, ...]
    exclusions: tuple[str, ...]


class QuoteEngine(QObject):
    log_message = Signal(str, str)
    stats_changed = Signal(dict)
    running_changed = Signal(bool)

    def __init__(self, settings_provider: Callable[[], RuntimeSettings], parent=None):
        super().__init__(parent)
        self._settings_provider = settings_provider
        self._rng = random.Random()
        self._stats = {"报价": 0, "略过": 0, "追求": 0, "排除": 0, "同意": 0}
        self._running = False
        self._session_start: float | None = None
        self._last_quote_ts = 0.0
        self._timer_interval = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)

    @property
    def running(self) -> bool:
        return self._running

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    def toggle(self):
        if self._running:
            self.stop()
        else:
            self.start()

    def start(self):
        if self._running:
            return

        settings = self._settings_provider()
        self._running = True
        self._session_start = time.monotonic()
        self._last_quote_ts = 0.0
        self._timer_interval = max(1, int(settings.detect_interval)) * 1000
        self._timer.start(self._timer_interval)
        self.running_changed.emit(True)

        self.log_message.emit(
            f"开始运行 · 倍数 ×{format_multiplier(settings.multiplier)} · "
            f"报价间隔 {settings.quote_interval} 秒 · "
            f"检测间隔 {settings.detect_interval} 秒",
            "ok",
        )
        if not settings.auto_submit:
            self.log_message.emit("自动提交已关闭，当前只检测不报价", "warn")
        elif not settings.scripts:
            self.log_message.emit("话术库为空，报价后不会发送话术", "warn")

        self._poll()

    def stop(self):
        if not self._running:
            return

        self._running = False
        self._timer.stop()
        self.running_changed.emit(False)

        elapsed = 0
        if self._session_start is not None:
            elapsed = int(time.monotonic() - self._session_start)
        minutes, seconds = divmod(elapsed, 60)
        self.log_message.emit(
            f"已停止运行 · 本次运行 {minutes:02d}:{seconds:02d}", "muted"
        )

    def set_detect_interval(self, seconds: int):
        interval = max(1, clamp_int(seconds, 20, 1, 3600)) * 1000
        if self._running and interval != self._timer_interval:
            self._timer_interval = interval
            self._timer.setInterval(interval)

    # ------------------------------------------------------------ loop
    def _poll(self):
        if not self._running:
            return

        settings = self._settings_provider()
        interval = max(1, int(settings.detect_interval)) * 1000
        if interval != self._timer_interval:
            self._timer_interval = interval
            self._timer.setInterval(interval)

        self._bump("追求", self._rng.randint(1, 5))

        if settings.exclusions and self._rng.random() < 0.30:
            rule = self._rng.choice(settings.exclusions)
            self._bump("排除", 1)
            self.log_message.emit(f"已排除：命中规则「{rule}」", "warn")
            return

        if not settings.auto_submit:
            self._bump("略过", 1)
            self.log_message.emit("自动提交已关闭 · 本轮仅检测", "muted")
            return

        if self._rng.random() < 0.55:
            self.log_message.emit(
                f"轮询完成 · 扫描到 {self._rng.randint(8, 60)} 条在售报价", "muted"
            )

        now = time.monotonic()
        if (
            self._last_quote_ts == 0.0
            or now - self._last_quote_ts >= settings.quote_interval
        ):
            self._quote(settings, now)

    def _quote(self, settings: RuntimeSettings, now: float):
        base = self._rng.randint(60, 5200)
        final = max(1, round(base * settings.multiplier))

        if self._rng.random() < 0.16:
            self._bump("略过", 1)
            self.log_message.emit(
                f"已略过：底价 ¥{final} 高于当前成交区间", "warn"
            )
        else:
            self._bump("报价", 1)
            self.log_message.emit(
                f"已报价 ¥{final}（底价 ¥{base} × "
                f"{format_multiplier(settings.multiplier)}）",
                "ok",
            )
            if settings.scripts:
                self.log_message.emit(
                    f"话术已发送 {len(settings.scripts)}/{len(settings.scripts)}",
                    "muted",
                )

            if self._rng.random() < 0.12:
                self._bump("同意", 1)
                deal = final + self._rng.randint(0, 60)
                self.log_message.emit(f"买家已同意 · 成交价 ¥{deal}", "ok")

        self._last_quote_ts = now

    def _bump(self, key: str, amount: int = 1):
        self._stats[key] += amount
        self.stats_changed.emit(dict(self._stats))
