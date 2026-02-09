# -*- coding: utf-8 -*-
"""Kamera servisi: Picamera2 (RPi) veya OpenCV fallback."""

import threading
import time
from collections import deque

try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    Picamera2 = None

import cv2
import numpy as np

from config import (
    RESOLUTIONS,
    DEFAULT_RESOLUTION,
    MAX_DISTANCE_MM,
    OBJECT_WIDTH_MM,
    OBJECT_HEIGHT_MM,
    CROP_ENABLED,
    CROP_MARGIN,
)


class CameraService:
    """Arducam 64MP / Picamera2 veya test için OpenCV kamera."""

    def __init__(self, on_frame=None, on_fps=None):
        self.on_frame = on_frame
        self.on_fps = on_fps
        self._resolution = DEFAULT_RESOLUTION
        self._fps = 10
        self._image_mode = "Renkli"
        self._light_filter = "Gamma"
        self._gamma = 1.0
        self._clahe_clip = 2.0
        self._zoom = 1.0
        self._focus_mode = "Manual"
        self._focus_value = 9
        self._pan = (0, 0)
        self._crop_enabled = CROP_ENABLED
        self._crop_width_mm = OBJECT_WIDTH_MM
        self._crop_height_mm = OBJECT_HEIGHT_MM
        self._crop_distance_mm = MAX_DISTANCE_MM
        self._crop_margin = CROP_MARGIN
        self._hardware_crop_active = False
        self._gamma_lut = None
        self._gamma_lut_gamma = None
        self._running = False
        self._thread = None
        self._picam2 = None
        self._cap = None
        self._fps_deque = deque(maxlen=30)
        self._last_fps_time = None

    def _get_crop_ratios(self):
        if not self._crop_enabled:
            return 1.0, 1.0
        distance = max(1.0, float(self._crop_distance_mm))
        ratio_w = (float(self._crop_width_mm) / distance) * float(self._crop_margin)
        ratio_h = (float(self._crop_height_mm) / distance) * float(self._crop_margin)
        ratio_w = max(0.01, min(1.0, ratio_w))
        ratio_h = max(0.01, min(1.0, ratio_h))
        return ratio_w, ratio_h

    def _build_crop_region(self, w, h):
        """Performans: sadece hedeflenen nesne alanını göster (merkez crop)."""
        ratio_w, ratio_h = self._get_crop_ratios()
        cw = max(64, int(w * ratio_w))
        ch = max(64, int(h * ratio_h))
        cw = min(cw, w)
        ch = min(ch, h)
        x0 = (w - cw) // 2
        y0 = (h - ch) // 2
        return (x0, y0, cw, ch)

    def _apply_filter(self, frame):
        if self._light_filter == "Yok":
            return frame
        is_color = len(frame.shape) == 3
        if self._light_filter == "Gamma":
            gamma = max(0.1, float(self._gamma))
            if self._gamma_lut is None or self._gamma_lut_gamma != gamma:
                inv_g = 1.0 / gamma
                self._gamma_lut = np.array(
                    [int(min(255, (i / 255.0) ** inv_g * 255.0)) for i in range(256)],
                    dtype=np.uint8,
                )
                self._gamma_lut_gamma = gamma
            frame = cv2.LUT(frame, self._gamma_lut)
        elif self._light_filter == "CLAHE":
            if is_color:
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                clahe = cv2.createCLAHE(clipLimit=float(self._clahe_clip), tileGridSize=(8, 8))
                lab[..., 0] = clahe.apply(lab[..., 0])
                frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            else:
                clahe = cv2.createCLAHE(clipLimit=float(self._clahe_clip), tileGridSize=(8, 8))
                frame = clahe.apply(frame)
        return frame

    def _apply_zoom_pan(self, frame, pan_x, pan_y, zoom):
        h, w = frame.shape[:2]
        if zoom <= 1.0 and pan_x == 0 and pan_y == 0:
            return frame
        scale = min(float(zoom), min(w, h) / 64)
        nw, nh = int(w / scale), int(h / scale)
        x0 = (w - nw) // 2 - pan_x
        y0 = (h - nh) // 2 - pan_y
        x0 = max(0, min(x0, w - nw))
        y0 = max(0, min(y0, h - nh))
        cropped = frame[y0 : y0 + nh, x0 : x0 + nw]
        return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

    def set_resolution(self, resolution):
        resolution = tuple(resolution)
        if resolution == self._resolution:
            return
        self._resolution = resolution
        if self._running:
            if self._picam2 and PICAMERA_AVAILABLE:
                self._restart_picamera2()
            elif self._cap and self._cap.isOpened():
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, min(1920, self._resolution[0]))
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, min(1080, self._resolution[1]))

    def set_fps(self, fps):
        self._fps = max(1, min(30, int(fps)))
        if self._picam2 and PICAMERA_AVAILABLE:
            frame_us = int(1_000_000 / self._fps)
            try:
                self._picam2.set_controls({"FrameDurationLimits": (frame_us, frame_us)})
            except Exception:
                pass
        elif self._cap and self._cap.isOpened():
            try:
                self._cap.set(cv2.CAP_PROP_FPS, float(self._fps))
            except Exception:
                pass

    def set_image_mode(self, mode):
        self._image_mode = mode

    def set_light_filter(self, name, gamma=None, clahe_clip=None):
        self._light_filter = name
        if gamma is not None:
            self._gamma = gamma
            self._gamma_lut = None
            self._gamma_lut_gamma = None
        if clahe_clip is not None:
            self._clahe_clip = clahe_clip

    def set_crop_params(self, width_mm=None, height_mm=None, distance_mm=None):
        updated = False
        if width_mm is not None and width_mm > 0:
            self._crop_width_mm = float(width_mm)
            updated = True
        if height_mm is not None and height_mm > 0:
            self._crop_height_mm = float(height_mm)
            updated = True
        if distance_mm is not None and distance_mm > 0:
            self._crop_distance_mm = float(distance_mm)
            updated = True
        if updated and self._picam2 and PICAMERA_AVAILABLE:
            self._apply_hardware_crop()

    def set_zoom(self, zoom):
        self._zoom = max(1.0, min(15.0, float(zoom)))

    def set_focus(self, mode=None, value=None):
        if mode is not None:
            self._focus_mode = mode
        if value is not None:
            self._focus_value = int(value)
        if self._picam2 and PICAMERA_AVAILABLE:
            try:
                if self._focus_mode == "Manual":
                    self._picam2.set_controls({"LensPosition": self._focus_value})
                elif self._focus_mode == "Otomatik":
                    self._picam2.set_controls({"AfMode": 1, "AfTrigger": 0})
            except Exception:
                pass

    def set_pan(self, x=None, y=None, center=False):
        if center:
            self._pan = (0, 0)
        else:
            px, py = self._pan
            if x is not None:
                px = x
            if y is not None:
                py = y
            self._pan = (px, py)

    def get_pan(self):
        return self._pan

    def _grab_loop_picamera2(self):
        try:
            self._picam2.start()
        except Exception:
            if self.on_fps:
                self.on_fps(0)
            return
        while self._running and self._picam2:
            try:
                arr = self._picam2.capture_array()
                if arr is None:
                    continue
                frame = self._process_frame(arr)
                if frame is not None and self.on_frame:
                    self.on_frame(frame)
                t = time.perf_counter()
                self._fps_deque.append(t)
                if len(self._fps_deque) >= 2 and self.on_fps:
                    self.on_fps(len(self._fps_deque) / (self._fps_deque[-1] - self._fps_deque[0]))
            except Exception:
                break
        try:
            self._picam2.stop()
        except Exception:
            pass

    def _grab_loop_opencv(self):
        while self._running and self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if not ret or frame is None:
                continue
            frame = self._process_frame(frame)
            if frame is not None and self.on_frame:
                self.on_frame(frame)
            t = time.perf_counter()
            self._fps_deque.append(t)
            if len(self._fps_deque) >= 2 and self.on_fps:
                self.on_fps(len(self._fps_deque) / (self._fps_deque[-1] - self._fps_deque[0]))

    def _process_frame(self, frame):
        if frame is None:
            return None
        if self._image_mode == "Gri":
            if len(frame.shape) == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self._hardware_crop_active:
            frame = self._apply_filter(frame)
            if self._zoom > 1.0 or self._pan != (0, 0):
                frame = self._apply_zoom_pan(frame, self._pan[0], self._pan[1], self._zoom)
            return frame
        if self._zoom <= 1.0 and self._pan == (0, 0):
            x0, y0, cw, ch = self._build_crop_region(frame.shape[1], frame.shape[0])
            frame = frame[y0 : y0 + ch, x0 : x0 + cw]
            return self._apply_filter(frame)
        frame = self._apply_filter(frame)
        frame = self._apply_zoom_pan(frame, self._pan[0], self._pan[1], self._zoom)
        x0, y0, cw, ch = self._build_crop_region(frame.shape[1], frame.shape[0])
        return frame[y0 : y0 + ch, x0 : x0 + cw]

    def start(self):
        if self._running:
            return
        self._running = True
        self._fps_deque.clear()
        self._hardware_crop_active = False
        if PICAMERA_AVAILABLE and Picamera2:
            try:
                self._picam2 = Picamera2()
                config = self._picam2.create_preview_configuration(
                    main={"size": self._resolution, "format": "RGB888"}
                )
                self._picam2.configure(config)
                frame_us = int(1_000_000 / self._fps)
                try:
                    self._picam2.set_controls({"FrameDurationLimits": (frame_us, frame_us)})
                except Exception:
                    pass
                self._apply_hardware_crop()
                self._thread = threading.Thread(target=self._grab_loop_picamera2, daemon=True)
            except Exception:
                self._picam2 = None
                self._cap = cv2.VideoCapture(0)
                if self._cap.isOpened():
                    self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, min(1920, self._resolution[0]))
                    self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, min(1080, self._resolution[1]))
                self._thread = threading.Thread(target=self._grab_loop_opencv, daemon=True)
        else:
            self._cap = cv2.VideoCapture(0)
            if self._cap.isOpened():
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, min(1920, self._resolution[0]))
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, min(1080, self._resolution[1]))
            self._thread = threading.Thread(target=self._grab_loop_opencv, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._picam2:
            try:
                self._picam2.close()
            except Exception:
                pass
            self._picam2 = None
        if self._cap:
            self._cap.release()
            self._cap = None

    def _restart_picamera2(self):
        self.stop()
        self.start()

    def _apply_hardware_crop(self):
        if not (self._picam2 and PICAMERA_AVAILABLE):
            self._hardware_crop_active = False
            return
        crop_max = self._picam2.camera_properties.get("ScalerCropMaximum")
        if not crop_max:
            self._hardware_crop_active = False
            return
        x, y, w, h = crop_max
        ratio_w, ratio_h = self._get_crop_ratios()
        cw = max(64, int(w * ratio_w))
        ch = max(64, int(h * ratio_h))
        cw = min(cw, w)
        ch = min(ch, h)
        x0 = x + (w - cw) // 2
        y0 = y + (h - ch) // 2
        # libcamera crop values should be even
        x0 &= ~1
        y0 &= ~1
        cw &= ~1
        ch &= ~1
        try:
            self._picam2.set_controls({"ScalerCrop": (x0, y0, cw, ch)})
            self._hardware_crop_active = True
        except Exception:
            self._hardware_crop_active = False

    def trigger_autofocus(self):
        if self._focus_mode != "Otomatik":
            return
        if self._picam2 and PICAMERA_AVAILABLE:
            try:
                self._picam2.set_controls({"AfMode": 1, "AfTrigger": 0})
            except Exception:
                pass
