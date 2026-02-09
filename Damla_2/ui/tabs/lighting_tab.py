# -*- coding: utf-8 -*-
"""Aydınlatma sekmesi: LED test, parlaklık, lokasyon, 8 LED checkbox, preset CRUD."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QSlider,
    QLabel, QComboBox, QCheckBox, QListWidget, QLineEdit, QMessageBox,
    QGridLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal

from config import LED_LOCATIONS, LED_COUNT
import database as db


class LightingTab(QWidget):
    settings_changed = pyqtSignal(dict)
    led_test_requested = pyqtSignal()
    led_test_confirm = pyqtSignal(str)  # 'R', 'G', 'B'

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Led Test
        test_group = QGroupBox("LED Test")
        test_layout = QVBoxLayout(test_group)
        self.btn_led_test = QPushButton("Led_Test")
        self.btn_led_test.clicked.connect(self._on_led_test)
        test_layout.addWidget(self.btn_led_test)
        layout.addWidget(test_group)

        # Parlaklık
        bright_group = QGroupBox("Parlaklık")
        bright_layout = QVBoxLayout(bright_group)
        self.slider_r = QSlider(Qt.Horizontal)
        self.slider_g = QSlider(Qt.Horizontal)
        self.slider_b = QSlider(Qt.Horizontal)
        for s, name in [(self.slider_r, "R"), (self.slider_g, "G"), (self.slider_b, "B")]:
            s.setRange(0, 255)
            s.setValue(128)
            s.valueChanged.connect(self._emit_settings)
            bright_layout.addWidget(QLabel(f"{name}:"))
            bright_layout.addWidget(s)
        layout.addWidget(bright_group)

        # Lokasyon
        loc_group = QGroupBox("Lokasyon")
        loc_layout = QHBoxLayout(loc_group)
        self.location_combo = QComboBox()
        self.location_combo.addItems(LED_LOCATIONS)
        self.location_combo.setCurrentText("Yok")
        self.location_combo.currentIndexChanged.connect(self._on_location_changed)
        loc_layout.addWidget(QLabel("Lokasyon:"))
        loc_layout.addWidget(self.location_combo)
        layout.addWidget(loc_group)

        # 8 LED checkbox
        leds_group = QGroupBox("LED'ler (tek tek)")
        leds_layout = QGridLayout(leds_group)
        self.led_checks = []
        for i in range(LED_COUNT):
            ch = QCheckBox(f"LED {i+1}")
            ch.stateChanged.connect(self._on_led_check_changed)
            self.led_checks.append(ch)
            leds_layout.addWidget(ch, i // 4, i % 4)
        layout.addWidget(leds_group)

        # Preset
        preset_group = QGroupBox("Preset")
        preset_layout = QVBoxLayout(preset_group)
        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setPlaceholderText("Preset adı")
        preset_layout.addWidget(self.preset_name_edit)
        self.preset_list = QListWidget()
        self.preset_list.currentItemChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_list)
        btn_layout = QHBoxLayout()
        for label, slot in [
            ("Kaydet", self._preset_save),
            ("Düzenle", self._preset_edit),
            ("Sil", self._preset_delete),
            ("Uygula", self._preset_apply),
            ("Başlangıç", self._preset_startup),
        ]:
            b = QPushButton(label)
            b.clicked.connect(slot)
            btn_layout.addWidget(b)
        preset_layout.addLayout(btn_layout)
        layout.addWidget(preset_group)

        layout.addStretch()

        self._leds_mask = 0
        self._refresh_preset_list()

    def _emit_settings(self):
        self.settings_changed.emit(self.get_settings())

    def get_settings(self):
        mask = 0
        for i, ch in enumerate(self.led_checks):
            if ch.isChecked():
                mask |= 1 << i
        self._leds_mask = mask
        return {
            "brightness_r": self.slider_r.value(),
            "brightness_g": self.slider_g.value(),
            "brightness_b": self.slider_b.value(),
            "location": self.location_combo.currentText(),
            "leds_mask": mask,
        }

    def apply_settings(self, s):
        if s is None:
            return
        self.slider_r.setValue(s.get("brightness_r", 128))
        self.slider_g.setValue(s.get("brightness_g", 128))
        self.slider_b.setValue(s.get("brightness_b", 128))
        self.location_combo.setCurrentText(s.get("location", "Yok"))
        mask = s.get("leds_mask", 0)
        for i, ch in enumerate(self.led_checks):
            ch.blockSignals(True)
            ch.setChecked(bool((mask >> i) & 1))
            ch.blockSignals(False)
        self._leds_mask = mask
        self._emit_settings()

    def _on_location_changed(self):
        loc = self.location_combo.currentText()
        if loc == "Yok":
            pass
        elif loc == "Tumu":
            for ch in self.led_checks:
                ch.blockSignals(True)
                ch.setChecked(True)
                ch.blockSignals(False)
        elif loc == "Sag_Dis":
            for i, ch in enumerate(self.led_checks):
                ch.blockSignals(True)
                ch.setChecked(4 <= i <= 7)
                ch.blockSignals(False)
        elif loc == "Sol_Dis":
            for i, ch in enumerate(self.led_checks):
                ch.blockSignals(True)
                ch.setChecked(0 <= i <= 3)
                ch.blockSignals(False)
        elif loc == "Orta":
            for i, ch in enumerate(self.led_checks):
                ch.blockSignals(True)
                ch.setChecked(2 <= i <= 5)
                ch.blockSignals(False)
        self._emit_settings()

    def _on_led_check_changed(self):
        self._emit_settings()

    def _on_led_test(self):
        self.led_test_requested.emit()

    def set_led_test_ok(self, ok=True):
        self.btn_led_test.setText("Test_OK" if ok else "Led_Test")

    def _refresh_preset_list(self):
        self.preset_list.clear()
        for name in db.lighting_list():
            self.preset_list.addItem(name)

    def _on_preset_selected(self, cur, prev):
        if cur:
            data = db.lighting_load(cur.text())
            if data:
                self.apply_settings(data)

    def _preset_save(self):
        name = self.preset_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Preset adı girin.")
            return
        db.lighting_save(name, self.get_settings())
        self._refresh_preset_list()
        self.preset_name_edit.clear()
        QMessageBox.information(self, "Kaydedildi", f"'{name}' kaydedildi.")

    def _preset_edit(self):
        cur = self.preset_list.currentItem()
        if not cur:
            QMessageBox.warning(self, "Uyarı", "Düzenlenecek preset seçin.")
            return
        name = cur.text()
        self.preset_name_edit.setText(name)
        db.lighting_save(name, self.get_settings())
        QMessageBox.information(self, "Güncellendi", f"'{name}' güncellendi.")

    def _preset_delete(self):
        cur = self.preset_list.currentItem()
        if not cur:
            QMessageBox.warning(self, "Uyarı", "Silinecek preset seçin.")
            return
        db.lighting_delete(cur.text())
        self._refresh_preset_list()

    def _preset_apply(self):
        cur = self.preset_list.currentItem()
        if not cur:
            QMessageBox.warning(self, "Uyarı", "Uygulanacak preset seçin.")
            return
        data = db.lighting_load(cur.text())
        if data:
            self.apply_settings(data)

    def _preset_startup(self):
        cur = self.preset_list.currentItem()
        if not cur:
            QMessageBox.warning(self, "Uyarı", "Başlangıç preset'i seçin.")
            return
        db.startup_set("lighting", cur.text())
        QMessageBox.information(self, "Başlangıç", f"Başlangıç aydınlatma preset'i: {cur.text()}")
