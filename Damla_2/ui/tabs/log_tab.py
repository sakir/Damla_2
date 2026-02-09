# -*- coding: utf-8 -*-
"""Log sekmesi: metin log görüntüleyici."""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton
from PyQt5.QtCore import pyqtSignal


class LogTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)
        self.btn_clear = QPushButton("Log temizle")
        self.btn_clear.clicked.connect(self.text.clear)
        layout.addWidget(self.btn_clear)

    def append(self, msg):
        self.text.append(msg)
