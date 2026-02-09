# -*- coding: utf-8 -*-
"""Kalibrasyon sekmesi: isim, Genişlik, Yükseklik, Uzaklık, Kaydet, Yeni Kaydet."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLineEdit, QDoubleSpinBox,
    QPushButton, QLabel, QFormLayout, QMessageBox,
)
from PyQt5.QtCore import pyqtSignal
import database as db


class CalibrationTab(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        g = QGroupBox("Kalibrasyon")
        fl = QFormLayout(g)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Kalibrasyon adı")
        fl.addRow("İsim:", self.name_edit)
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0.1, 1000)
        self.width_spin.setValue(50)
        self.width_spin.setSuffix(" mm")
        fl.addRow("Genişlik:", self.width_spin)
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(0.1, 1000)
        self.height_spin.setValue(50)
        self.height_spin.setSuffix(" mm")
        fl.addRow("Yükseklik:", self.height_spin)
        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(1, 2000)
        self.distance_spin.setValue(300)
        self.distance_spin.setSuffix(" mm")
        fl.addRow("Uzaklık:", self.distance_spin)
        layout.addWidget(g)

        btn_layout = QVBoxLayout()
        self.btn_save = QPushButton("Kaydet")
        self.btn_new = QPushButton("Yeni Kaydet")
        self.btn_save.clicked.connect(self._save)
        self.btn_new.clicked.connect(self._new_save)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_new)
        layout.addLayout(btn_layout)
        layout.addStretch()

    def get_values(self):
        return {
            "name": self.name_edit.text().strip(),
            "width_mm": self.width_spin.value(),
            "height_mm": self.height_spin.value(),
            "distance_mm": self.distance_spin.value(),
        }

    def _save(self):
        v = self.get_values()
        if not v["name"]:
            QMessageBox.warning(self, "Uyarı", "İsim girin.")
            return
        db.calibration_save(v["name"], v["width_mm"], v["height_mm"], v["distance_mm"])
        QMessageBox.information(self, "Kaydedildi", f"'{v['name']}' kaydedildi.")
        self.settings_changed.emit(v)

    def _new_save(self):
        self.name_edit.clear()
        self.width_spin.setValue(50)
        self.height_spin.setValue(50)
        self.distance_spin.setValue(300)
        QMessageBox.information(self, "Yeni", "Alanlar temizlendi. İsim verip Kaydet ile kaydedin.")
