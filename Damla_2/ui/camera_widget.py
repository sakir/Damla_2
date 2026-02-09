# -*- coding: utf-8 -*-
"""Kamera önizleme ve ROI çizimi."""

from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
import cv2
import numpy as np


class CameraWidget(QLabel):
    """Kamera çıktısı ve ROI (dikdörtgen) çizimi. Roi temizle ile overlay silinir."""

    roi_changed = pyqtSignal(object)  # QRect or None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(320, 240)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #1a1a1a;")
        self._pixmap = None
        self._roi_img = None  # QRect (image coords)
        self._drawing = False
        self._start_point_img = None
        self._overlay_text = []  # [(x,y, text), ...]
        self._current_frame = None
        self._scale = 1.0
        self._offset_x = 0
        self._offset_y = 0
        self._display_origin_x = 0
        self._display_origin_y = 0
        self._display_roi_only = False

    def set_frame(self, frame_bgr_or_gray):
        """OpenCV frame (BGR veya gri) göster."""
        if frame_bgr_or_gray is None:
            return
        self._current_frame = frame_bgr_or_gray
        frame = frame_bgr_or_gray
        h, w = frame.shape[:2]
        self._display_origin_x = 0
        self._display_origin_y = 0
        if self._display_roi_only and self._roi_img and not self._roi_img.isEmpty():
            x0 = max(0, min(self._roi_img.x(), w - 1))
            y0 = max(0, min(self._roi_img.y(), h - 1))
            rw = max(1, min(self._roi_img.width(), w - x0))
            rh = max(1, min(self._roi_img.height(), h - y0))
            frame = frame[y0 : y0 + rh, x0 : x0 + rw]
            h, w = frame.shape[:2]
            self._display_origin_x = x0
            self._display_origin_y = y0
        if len(frame.shape) == 2:
            img = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        else:
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        bytes_per_line = img.shape[2] * w
        qimg = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self._pixmap = QPixmap.fromImage(qimg)
        scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._scale = scaled.width() / self._pixmap.width() if self._pixmap.width() else 1.0
        self._offset_x = (self.width() - scaled.width()) / 2
        self._offset_y = (self.height() - scaled.height()) / 2
        self._display()

    def _display(self):
        if self._pixmap is None:
            return
        pm = self._pixmap.copy()
        painter = QPainter(pm)
        if self._roi_img and not self._roi_img.isEmpty():
            pen = QPen(QColor(0, 255, 0), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self._roi_img.translated(-self._display_origin_x, -self._display_origin_y))
        for (x, y, text) in self._overlay_text:
            painter.setPen(QColor(255, 255, 0))
            painter.drawText(
                int(x - self._display_origin_x),
                int(y - self._display_origin_y),
                str(text),
            )
        painter.end()
        self.setPixmap(pm.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def paintEvent(self, event):
        super().paintEvent(event)
        self._display()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            start = self._widget_to_image(event.pos(), clamp=False)
            if start is None:
                return
            self._display_roi_only = False
            self._drawing = True
            self._start_point_img = start
            x, y = start
            self._roi_img = QRect(x, y, 1, 1)

    def mouseMoveEvent(self, event):
        if self._drawing and self._start_point_img:
            cur = self._widget_to_image(event.pos(), clamp=True)
            if cur is None:
                return
            x0, y0 = self._start_point_img
            x1, y1 = cur
            self._roi_img = QRect(x0, y0, x1 - x0, y1 - y0).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drawing:
            self._drawing = False
            if self._start_point_img:
                cur = self._widget_to_image(event.pos(), clamp=True)
                if cur is not None:
                    x0, y0 = self._start_point_img
                    x1, y1 = cur
                    self._roi_img = QRect(x0, y0, x1 - x0, y1 - y0).normalized()
            self._start_point_img = None
            if self._roi_img and (self._roi_img.width() <= 5 or self._roi_img.height() <= 5):
                self._roi_img = None
            self._display_roi_only = bool(self._roi_img and not self._roi_img.isEmpty())
            self.roi_changed.emit(self._roi_img)
            self.update()

    def roi_clear(self):
        """Roi ve tüm overlay verilerini temizle."""
        self._roi_img = None
        self._start_point_img = None
        self._display_roi_only = False
        self._overlay_text.clear()
        self.update()
        self.roi_changed.emit(None)

    def get_roi_rect(self):
        """Görüntü koordinatında ROI dikdörtgeni."""
        return self._roi_img

    def get_roi_in_image_coords(self):
        """Görüntü koordinatında ROI (x,y,w,h) veya None."""
        return getattr(self, "_roi_img", None)

    def _widget_to_image(self, pos, clamp=False):
        if self._pixmap is None or self._scale <= 0:
            return None
        x = (pos.x() - self._offset_x) / self._scale
        y = (pos.y() - self._offset_y) / self._scale
        if clamp:
            w = max(1, self._pixmap.width())
            h = max(1, self._pixmap.height())
            x = min(max(x, 0), w - 1)
            y = min(max(y, 0), h - 1)
            return int(x + self._display_origin_x), int(y + self._display_origin_y)
        if x < 0 or y < 0 or x >= self._pixmap.width() or y >= self._pixmap.height():
            return None
        return int(x + self._display_origin_x), int(y + self._display_origin_y)

    def add_overlay_text(self, x, y, text):
        self._overlay_text.append((x, y, text))

    def get_current_frame(self):
        return self._current_frame
