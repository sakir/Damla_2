#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Damla_2 - Su damlası ölçüm programı. Raspberry Pi 5, Arducam 64MP, WS2812."""

import sys
from pathlib import Path

# Proje kökünü path'e ekle
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Damla_2")
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
