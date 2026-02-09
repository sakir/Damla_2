# -*- coding: utf-8 -*-
"""Kamera sekmesi: çözünürlük, FPS, mod, filtre, zoom, focus, pan, preset CRUD."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QSlider, QLabel,
    QGroupBox, QPushButton, QSpinBox, QDoubleSpinBox, QListWidget,
    QLineEdit, QMessageBox, QGridLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal

from config import (
    RESOLUTIONS, DEFAULT_RESOLUTION, IMAGE_MODES, LIGHT_FILTERS,
    DEFAULT_LIGHT_FILTER, ZOOM_MIN, ZOOM_MAX, ZOOM_DEFAULT,
    FOCUS_DEFAULT, PAN_DEFAULT,
)
import database as db


class CameraTab(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Çözünürlük
        res_group = QGroupBox("Çözünürlük")
        res_layout = QHBoxLayout(res_group)
        self.res_combo = QComboBox()
        for r in RESOLUTIONS:
            self.res_combo.addItem(f"{r[0]} x {r[1]}", r)
        idx = self.res_combo.findData(DEFAULT_RESOLUTION)
        if idx >= 0:
            self.res_combo.setCurrentIndex(idx)
        self.res_combo.currentIndexChanged.connect(self._emit_settings)
        res_layout.addWidget(QLabel("Çözünürlük:"))
        res_layout.addWidget(self.res_combo)
        layout.addWidget(res_group)

        # FPS
        fps_group = QGroupBox("FPS")
        fps_layout = QHBoxLayout(fps_group)
        self.fps_slider = QSlider(Qt.Horizontal)
        self.fps_slider.setRange(1, 30)
        self.fps_slider.setValue(10)
        self.fps_slider.valueChanged.connect(
            lambda v: (self.fps_value_label.setText(str(v)), self._emit_settings())
        )
        self.fps_value_label = QLabel("10")
        self.fps_real_label = QLabel("Gerçek: --")
        fps_layout.addWidget(QLabel("FPS:"))
        fps_layout.addWidget(self.fps_slider)
        fps_layout.addWidget(self.fps_value_label)
        fps_layout.addWidget(self.fps_real_label)
        layout.addWidget(fps_group)

        # Görüntü modu
        mode_group = QGroupBox("Görüntü modu")
        mode_layout = QHBoxLayout(mode_group)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(IMAGE_MODES)
        self.mode_combo.currentIndexChanged.connect(self._emit_settings)
        mode_layout.addWidget(self.mode_combo)
        layout.addWidget(mode_group)

        # Aydınlatma filtresi
        filter_group = QGroupBox("Aydınlatma filtresi")
        filter_layout = QVBoxLayout(filter_group)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(LIGHT_FILTERS)
        self.filter_combo.setCurrentText(DEFAULT_LIGHT_FILTER)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        self.gamma_label = QLabel("Gamma:")
        self.gamma_slider = QSlider(Qt.Horizontal)
        self.gamma_slider.setRange(10, 300)
        self.gamma_slider.setValue(100)
        self.gamma_slider.valueChanged.connect(lambda v: self._emit_settings() or self.gamma_value_label.setText(f"{v/100:.2f}"))
        self.gamma_value_label = QLabel("1.00")
        filter_layout.addWidget(self.gamma_label)
        filter_layout.addWidget(self.gamma_slider)
        filter_layout.addWidget(self.gamma_value_label)
        self.clahe_label = QLabel("CLAHE clip:")
        self.clahe_slider = QSlider(Qt.Horizontal)
        self.clahe_slider.setRange(10, 50)
        self.clahe_slider.setValue(20)
        self.clahe_slider.valueChanged.connect(lambda v: self._emit_settings() or self.clahe_value_label.setText(f"{v/10:.1f}"))
        self.clahe_value_label = QLabel("2.0")
        filter_layout.addWidget(self.clahe_label)
        filter_layout.addWidget(self.clahe_slider)
        filter_layout.addWidget(self.clahe_value_label)
        layout.addWidget(filter_group)

        # Zoom
        zoom_group = QGroupBox("Zoom")
        zoom_layout = QHBoxLayout(zoom_group)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self._zoom_scale = 10
        self.zoom_slider.setRange(int(ZOOM_MIN * self._zoom_scale), int(ZOOM_MAX * self._zoom_scale))
        self.zoom_slider.setValue(int(ZOOM_DEFAULT * self._zoom_scale))
        self.zoom_slider.valueChanged.connect(
            lambda v: self._emit_settings() or self.zoom_value_label.setText(f"{v / self._zoom_scale:.1f}x")
        )
        self.zoom_value_label = QLabel(f"{ZOOM_DEFAULT:.1f}x")
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_value_label)
        layout.addWidget(zoom_group)

        # Focus
        focus_group = QGroupBox("Focus")
        focus_layout = QGridLayout(focus_group)
        self.focus_mode_combo = QComboBox()
        self.focus_mode_combo.addItems(["Manual", "Otomatik"])
        self.focus_mode_combo.currentIndexChanged.connect(self._on_focus_mode_changed)
        focus_layout.addWidget(QLabel("Mod:"), 0, 0)
        focus_layout.addWidget(self.focus_mode_combo, 0, 1)
        self.focus_manual_widget = QWidget()
        fm_layout = QHBoxLayout(self.focus_manual_widget)
        self.focus_value_label = QLabel("Netlik:")
        self.focus_value_spin = QDoubleSpinBox()
        self.focus_value_spin.setRange(0.0, 255.0)
        self.focus_value_spin.setDecimals(1)
        self.focus_value_spin.setSingleStep(0.1)
        self.focus_value_spin.setValue(float(FOCUS_DEFAULT))
        self.focus_value_spin.valueChanged.connect(self._on_focus_value_changed)
        self.btn_f_minus = QPushButton("F-")
        self.btn_f_plus = QPushButton("F+")
        self.btn_f_minus.clicked.connect(self._focus_minus)
        self.btn_f_plus.clicked.connect(self._focus_plus)
        fm_layout.addWidget(self.btn_f_minus)
        fm_layout.addWidget(self.focus_value_label)
        fm_layout.addWidget(self.focus_value_spin)
        fm_layout.addWidget(self.btn_f_plus)
        focus_layout.addWidget(self.focus_manual_widget, 1, 0, 1, 2)
        self.btn_autofocus = QPushButton("Autofocus tekrarla")
        self.btn_autofocus.clicked.connect(self._on_autofocus)
        self.btn_autofocus.setVisible(False)
        focus_layout.addWidget(self.btn_autofocus, 2, 0, 1, 2)
        self._focus_value = float(FOCUS_DEFAULT)
        layout.addWidget(focus_group)

        # Pan
        pan_group = QGroupBox("Pan")
        pan_layout = QGridLayout(pan_group)
        self.pan_x_label = QLabel("X: 0")
        self.pan_y_label = QLabel("Y: 0")
        pan_layout.addWidget(QLabel("Değer:"), 0, 0)
        pan_layout.addWidget(self.pan_x_label, 0, 1)
        pan_layout.addWidget(self.pan_y_label, 0, 2)
        self.btn_pan_up = QPushButton("Yukarı")
        self.btn_pan_down = QPushButton("Aşağı")
        self.btn_pan_left = QPushButton("Sol")
        self.btn_pan_right = QPushButton("Sağ")
        self.btn_pan_center = QPushButton("Merkeze")
        step = 20
        self.btn_pan_up.clicked.connect(lambda: self._pan(0, -step))
        self.btn_pan_down.clicked.connect(lambda: self._pan(0, step))
        self.btn_pan_left.clicked.connect(lambda: self._pan(-step, 0))
        self.btn_pan_right.clicked.connect(lambda: self._pan(step, 0))
        self.btn_pan_center.clicked.connect(self._pan_center)
        pan_layout.addWidget(self.btn_pan_up, 1, 1)
        pan_layout.addWidget(self.btn_pan_left, 2, 0)
        pan_layout.addWidget(self.btn_pan_center, 2, 1)
        pan_layout.addWidget(self.btn_pan_right, 2, 2)
        pan_layout.addWidget(self.btn_pan_down, 3, 1)
        self._pan_x, self._pan_y = PAN_DEFAULT[0], PAN_DEFAULT[1]
        layout.addWidget(pan_group)

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
        self._refresh_preset_list()
        self._on_filter_changed()

    def _emit_settings(self):
        self.settings_changed.emit(self.get_settings())

    def get_settings(self):
        res = self.res_combo.currentData()
        if res is None:
            res = DEFAULT_RESOLUTION
        return {
            "resolution": res,
            "fps": self.fps_slider.value(),
            "image_mode": self.mode_combo.currentText(),
            "light_filter": self.filter_combo.currentText(),
            "gamma": self.gamma_slider.value() / 100.0,
            "clahe_clip": self.clahe_slider.value() / 10.0,
            "zoom": self.zoom_slider.value() / self._zoom_scale,
            "focus_mode": self.focus_mode_combo.currentText(),
            "focus_value": self._focus_value,
            "pan_x": self._pan_x,
            "pan_y": self._pan_y,
        }

    def apply_settings(self, s):
        if s is None:
            return
        idx = self.res_combo.findData(tuple(s.get("resolution", DEFAULT_RESOLUTION)))
        if idx >= 0:
            self.res_combo.setCurrentIndex(idx)
        self.fps_slider.setValue(s.get("fps", 10))
        self.mode_combo.setCurrentText(s.get("image_mode", "Renkli"))
        self.filter_combo.setCurrentText(s.get("light_filter", DEFAULT_LIGHT_FILTER))
        self.gamma_slider.setValue(int((s.get("gamma", 1.0) or 1.0) * 100))
        self.clahe_slider.setValue(int((s.get("clahe_clip", 2.0) or 2.0) * 10))
        self.zoom_slider.setValue(int(float(s.get("zoom", ZOOM_DEFAULT)) * self._zoom_scale))
        self.focus_mode_combo.setCurrentText(s.get("focus_mode", "Manual"))
        self._focus_value = float(s.get("focus_value", FOCUS_DEFAULT))
        self.focus_value_spin.setValue(self._focus_value)
        self._pan_x = s.get("pan_x", 0)
        self._pan_y = s.get("pan_y", 0)
        self.pan_x_label.setText(f"X: {self._pan_x}")
        self.pan_y_label.setText(f"Y: {self._pan_y}")
        self._emit_settings()

    def _on_filter_changed(self):
        f = self.filter_combo.currentText()
        gamma_visible = f == "Gamma"
        clahe_visible = f == "CLAHE"
        self.gamma_label.setVisible(gamma_visible)
        self.gamma_slider.setVisible(gamma_visible)
        self.gamma_value_label.setVisible(gamma_visible)
        self.clahe_label.setVisible(clahe_visible)
        self.clahe_slider.setVisible(clahe_visible)
        self.clahe_value_label.setVisible(clahe_visible)
        self._emit_settings()

    def _on_focus_mode_changed(self):
        is_auto = self.focus_mode_combo.currentText() == "Otomatik"
        self.focus_manual_widget.setVisible(not is_auto)
        self.btn_autofocus.setVisible(is_auto)
        self._emit_settings()

    def _focus_minus(self):
        self.focus_value_spin.setValue(self.focus_value_spin.value() - self.focus_value_spin.singleStep())

    def _focus_plus(self):
        self.focus_value_spin.setValue(self.focus_value_spin.value() + self.focus_value_spin.singleStep())

    def _on_focus_value_changed(self, value):
        self._focus_value = float(value)
        self._emit_settings()

    def autofocus_clicked(self):
        return self.btn_autofocus  # dışarıdan bağlamak için

    def _on_autofocus(self):
        self._emit_settings()

    def _pan(self, dx, dy):
        self._pan_x += dx
        self._pan_y += dy
        self.pan_x_label.setText(f"X: {self._pan_x}")
        self.pan_y_label.setText(f"Y: {self._pan_y}")
        self._emit_settings()

    def _pan_center(self):
        self._pan_x = 0
        self._pan_y = 0
        self.pan_x_label.setText("X: 0")
        self.pan_y_label.setText("Y: 0")
        self._emit_settings()

    def set_real_fps(self, fps):
        self.fps_real_label.setText(f"Gerçek: {fps:.1f}" if fps else "Gerçek: --")

    def _refresh_preset_list(self):
        self.preset_list.clear()
        for name in db.camera_list():
            self.preset_list.addItem(name)

    def _on_preset_selected(self, cur, prev):
        if cur:
            data = db.camera_load(cur.text())
            if data:
                self.apply_settings(data)

    def _preset_save(self):
        name = self.preset_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Preset adı girin.")
            return
        db.camera_save(name, self.get_settings())
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
        db.camera_save(name, self.get_settings())
        QMessageBox.information(self, "Güncellendi", f"'{name}' güncellendi.")

    def _preset_delete(self):
        cur = self.preset_list.currentItem()
        if not cur:
            QMessageBox.warning(self, "Uyarı", "Silinecek preset seçin.")
            return
        db.camera_delete(cur.text())
        self._refresh_preset_list()

    def _preset_apply(self):
        cur = self.preset_list.currentItem()
        if not cur:
            QMessageBox.warning(self, "Uyarı", "Uygulanacak preset seçin.")
            return
        data = db.camera_load(cur.text())
        if data:
            self.apply_settings(data)

    def _preset_startup(self):
        cur = self.preset_list.currentItem()
        if not cur:
            QMessageBox.warning(self, "Uyarı", "Başlangıç preset'i seçin.")
            return
        db.startup_set("camera", cur.text())
        QMessageBox.information(self, "Başlangıç", f"Başlangıç kamera preset'i: {cur.text()}")
