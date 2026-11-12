#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""7881 自动报价 · 程序入口。"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config import APP_NAME
from app.theme import SANS, load_stylesheet, make_font
from app.ui.main_window import MainWindow


def main():
    QApplication.setApplicationName(APP_NAME)
    QApplication.setApplicationDisplayName(APP_NAME)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(make_font(SANS, 13))
    app.setStyleSheet(load_stylesheet())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
