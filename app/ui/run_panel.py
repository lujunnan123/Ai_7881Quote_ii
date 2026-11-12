"""运行控制卡片：开始/停止、自动提交、排除规则与统计。"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QPushButton

from app.ui.widgets import CheckLine, StatBox, add_card_header, prepare_card


class RunPanel(QFrame):
    run_clicked = Signal()
    exclude_clicked = Signal()

    STAT_ITEMS = (
        ("报价", "已报价"),
        ("略过", "已略过"),
        ("追求", "追求"),
        ("排除", "已排除"),
        ("同意", "被同意"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = prepare_card(self)
        add_card_header(layout, "运行控制", "开始 / 停止")

        self.run_btn = QPushButton("开始运行")
        self.run_btn.setObjectName("startBtn")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.setMinimumHeight(36)
        self.run_btn.clicked.connect(lambda: self.run_clicked.emit())
        layout.addWidget(self.run_btn)

        self.auto_check = CheckLine(
            "自动提交报价并发送话术", "先提交最优价，再发一条招呼", checked=True
        )
        layout.addWidget(self.auto_check)

        self.exclude_btn = QPushButton("不想要规则 · 设置排除")
        self.exclude_btn.setObjectName("ghostBtn")
        self.exclude_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exclude_btn.setMinimumHeight(32)
        self.exclude_btn.clicked.connect(lambda: self.exclude_clicked.emit())
        layout.addWidget(self.exclude_btn)

        self.stat_boxes: dict[str, StatBox] = {}
        for key, caption in self.STAT_ITEMS:
            self.stat_boxes[key] = StatBox(caption)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid.addWidget(self.stat_boxes["报价"], 0, 0)
        grid.addWidget(self.stat_boxes["略过"], 0, 1)
        grid.addWidget(self.stat_boxes["追求"], 1, 0)
        grid.addWidget(self.stat_boxes["排除"], 1, 1)
        grid.addWidget(self.stat_boxes["同意"], 2, 0, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

    def set_running(self, running: bool):
        self.run_btn.setObjectName("stopBtn" if running else "startBtn")
        self.run_btn.setText("停止" if running else "开始运行")
        style = self.run_btn.style()
        style.unpolish(self.run_btn)
        style.polish(self.run_btn)

    def set_stats(self, stats: dict):
        for key, box in self.stat_boxes.items():
            box.set_value(stats.get(key, 0))

    def auto_submit(self) -> bool:
        return self.auto_check.isChecked()

    def set_auto_submit(self, enabled: bool):
        self.auto_check.setChecked(bool(enabled))

    def set_exclusion_rules(self, rules: list[str]):
        count = len(rules)
        self.exclude_btn.setText(
            "不想要规则 · 设置排除" + (f"（{count}）" if count else "")
        )
        self.exclude_btn.setToolTip(
            "；".join(rules) if rules else "尚未设置排除规则"
        )
