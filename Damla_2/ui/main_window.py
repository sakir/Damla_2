# -*- coding: utf-8 -*-
"""Ana pencere: üstte tablar (Kamera, Aydinlatma, Kalibrasyon, Analiz, Log), sağda menü, solda kamera."""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget,
    QApplication, QMessageBox, QScrollArea,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

# Proje kökü
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DEFAULT_ANALYSIS_MODEL
from database import init_db, camera_load, lighting_load, startup_get
from camera_service import CameraService
from led_service import LedService
from ui.camera_widget import CameraWidget
from ui.tabs.camera_tab import CameraTab
from ui.tabs.lighting_tab import LightingTab
from ui.tabs.calibration_tab import CalibrationTab
from ui.tabs.analysis_tab import AnalysisTab
from ui.tabs.log_tab import LogTab

# Analiz modülleri
from analysis.circle_fitting import circle_fitting_contact_angle
from analysis.young_laplace import young_laplace_fit
from analysis.wenzel import wenzel_angle
from analysis.cassie_baxter import cassie_baxter_angle
from analysis.polynomial_fitting import polynomial_fitting_contact_angle
import cv2
import numpy as np


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        self.setWindowTitle("Damla_2 - Su Damlası Ölçüm")
        self.setMinimumSize(1000, 700)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Sol: Kamera görüntüsü (kalan alan)
        self.camera_widget = CameraWidget()
        main_layout.addWidget(self.camera_widget, stretch=1)

        # Sağ: Tab menüleri (Kamera, Aydinlatma, Kalibrasyon, Analiz, Log)
        self.camera_tab = CameraTab()
        self.lighting_tab = LightingTab()
        self.calibration_tab = CalibrationTab()
        self.analysis_tab = AnalysisTab()
        self.log_tab = LogTab()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.camera_tab, "Kamera")
        self.tabs.addTab(self.lighting_tab, "Aydinlatma")
        self.tabs.addTab(self.calibration_tab, "Kalibrasyon")
        self.tabs.addTab(self.analysis_tab, "Analiz")
        self.tabs.addTab(self.log_tab, "Log")
        self.tabs.setMaximumWidth(400)
        self.tabs.setMinimumWidth(300)
        main_layout.addWidget(self.tabs, stretch=0)

        # Kamera servisi
        self.camera_service = CameraService(
            on_frame=self._on_camera_frame,
            on_fps=self._on_fps,
        )
        self.camera_tab.settings_changed.connect(self._apply_camera_settings)
        self.camera_tab.btn_autofocus.clicked.connect(self.camera_service.trigger_autofocus)

        # LED servisi
        self.led_service = LedService()
        self.lighting_tab.settings_changed.connect(self._apply_lighting_settings)
        self.lighting_tab.led_test_requested.connect(self._on_led_test)
        self.lighting_tab.set_led_test_ok(False)

        # Kalibrasyon (gösterilecek alan)
        self.calibration_tab.settings_changed.connect(self._apply_calibration_settings)

        # Analiz
        self.camera_widget.roi_changed.connect(self._on_roi_changed)
        self.analysis_tab.roi_clear_requested.connect(self.camera_widget.roi_clear)
        self.analysis_tab.calculate_requested.connect(self._on_analyze)

        # Başlangıç preset'leri
        start_cam = startup_get("camera")
        if start_cam:
            data = camera_load(start_cam)
            if data:
                self.camera_tab.apply_settings(data)
        start_light = startup_get("lighting")
        if start_light:
            data = lighting_load(start_light)
            if data:
                self.lighting_tab.apply_settings(data)

        self._apply_camera_settings(self.camera_tab.get_settings())
        self._apply_lighting_settings(self.lighting_tab.get_settings())
        self.camera_service.start()
        self.log_tab.append("Damla_2 başlatıldı.")

    def _on_camera_frame(self, frame):
        if frame is None:
            return
        self.camera_widget.set_frame(frame)

    def _on_fps(self, fps):
        if fps:
            self.camera_tab.set_real_fps(fps)

    def _apply_camera_settings(self, s):
        self.camera_service.set_resolution(s.get("resolution", (9152, 6944)))
        self.camera_service.set_fps(s.get("fps", 10))
        self.camera_service.set_image_mode(s.get("image_mode", "Renkli"))
        self.camera_service.set_light_filter(
            s.get("light_filter", "Gamma"),
            gamma=s.get("gamma"),
            clahe_clip=s.get("clahe_clip"),
        )
        self.camera_service.set_zoom(s.get("zoom", 1))
        self.camera_service.set_focus(
            mode=s.get("focus_mode"),
            value=s.get("focus_value"),
        )
        self.camera_service.set_pan(x=s.get("pan_x"), y=s.get("pan_y"))

    def _apply_lighting_settings(self, s):
        self.led_service.set_brightness_rgb(
            s.get("brightness_r", 128),
            s.get("brightness_g", 128),
            s.get("brightness_b", 128),
        )
        self.led_service.set_location_and_mask(
            s.get("location", "Yok"),
            s.get("leds_mask", 0),
        )

    def _apply_calibration_settings(self, s):
        self.camera_service.set_crop_params(
            width_mm=s.get("width_mm"),
            height_mm=s.get("height_mm"),
            distance_mm=s.get("distance_mm"),
        )
        try:
            self.log_tab.append(
                "Kalibrasyon: %.1f x %.1f mm, %.1f mm" % (
                    s.get("width_mm", 0),
                    s.get("height_mm", 0),
                    s.get("distance_mm", 0),
                )
            )
        except Exception:
            pass

    def _on_led_test(self):
        def confirm(color):
            self.log_tab.append(f"LED renk onayı: {color}")
        try:
            self.led_service.test_sequence(3, on_confirm=confirm)
            self.lighting_tab.set_led_test_ok(True)
        except Exception as e:
            self.log_tab.append(f"LED test hata: {e}")
            self.lighting_tab.set_led_test_ok(False)

    def _on_roi_changed(self, roi):
        pass

    def _on_analyze(self, payload):
        model = payload.get("model", DEFAULT_ANALYSIS_MODEL)
        params = payload.get("params", {})
        roi = self.camera_widget.get_roi_in_image_coords()
        if roi is None or roi.isEmpty():
            self.analysis_tab.set_result("ROI seçin (sürükleyerek çizin).")
            return
        frame = self.camera_widget.get_current_frame()
        if frame is None:
            self.analysis_tab.set_result("Görüntü yok.")
            return
        if len(frame.shape) == 3:
            img_bw = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            img_bw = frame
        x, y, w, h = roi.x(), roi.y(), roi.width(), roi.height()
        roi_img = img_bw[y : y + h, x : x + w]
        roi_mask = (255 * np.ones((h, w), dtype=np.uint8))
        px_per_mm = 1.0

        result = None
        err = None
        if model == "Circle_Fitting":
            result, err = circle_fitting_contact_angle(
                roi_img, roi_mask,
                edge_threshold=params.get("edge_threshold", 50),
                min_radius_px=params.get("min_radius_px", 20),
                px_per_mm=px_per_mm,
            )
        elif model == "Young_Laplace":
            result, err = young_laplace_fit(
                roi_img, roi_mask,
                surface_tension=params.get("surface_tension", 72.8),
                bond_number=params.get("bond_number", 0.5),
                px_per_mm=px_per_mm,
            )
        elif model == "Wenzel":
            result, err = wenzel_angle(
                roi_img, roi_mask,
                roughness_factor=params.get("roughness_factor", 1.2),
                px_per_mm=px_per_mm,
            )
        elif model == "Cassie_Baxter":
            result, err = cassie_baxter_angle(
                roi_img, roi_mask,
                f1=params.get("f1", 0.5),
                theta1_deg=params.get("theta1_deg", 110),
                px_per_mm=px_per_mm,
            )
        elif model == "Polynominal_Fitting":
            result, err = polynomial_fitting_contact_angle(
                roi_img, roi_mask,
                degree=params.get("degree", 4),
                px_per_mm=px_per_mm,
            )
        if err:
            self.analysis_tab.set_result(err)
            self.log_tab.append(f"Analiz: {err}")
        elif result is not None:
            txt = f"Temas açısı: {result:.2f}°"
            self.analysis_tab.set_result(txt)
            self.log_tab.append(txt)
            self.camera_widget.add_overlay_text(x, y + h + 15, txt)
        else:
            self.analysis_tab.set_result("Hesaplanamadı.")

    def closeEvent(self, event):
        self.camera_service.stop()
        self.led_service.all_off()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Damla_2")
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
