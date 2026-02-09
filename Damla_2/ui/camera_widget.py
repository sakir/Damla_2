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
        self._roi = None  # QRect
        self._drawing = False
        self._start_point = None
        self._overlay_text = []  # [(x,y, text), ...]
        self._current_frame = None
        self._scale = 1.0
        self._offset_x = 0
        self._offset_y = 0

    def set_frame(self, frame_bgr_or_gray):
        """OpenCV frame (BGR veya gri) göster."""
        if frame_bgr_or_gray is None:
            return
        self._current_frame = frame_bgr_or_gray
        h, w = frame_bgr_or_gray.shape[:2]
        if len(frame_bgr_or_gray.shape) == 2:
            img = cv2.cvtColor(frame_bgr_or_gray, cv2.COLOR_GRAY2RGB)
        else:
            img = cv2.cvtColor(frame_bgr_or_gray, cv2.COLOR_BGR2RGB)
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
        if self._roi and not self._roi.isEmpty():
            pen = QPen(QColor(0, 255, 0), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self._roi)
        for (x, y, text) in self._overlay_text:
            painter.setPen(QColor(255, 255, 0))
            painter.drawText(int(x), int(y), str(text))
        painter.end()
        self.setPixmap(pm.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def paintEvent(self, event):
        super().paintEvent(event)
        self._display()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drawing = True
            self._start_point = event.pos()
            self._roi = QRect(event.pos(), event.pos())

    def mouseMoveEvent(self, event):
        if self._drawing and self._start_point:
            self._roi = QRect(self._start_point, event.pos()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drawing:
            self._drawing = False
            if self._pixmap and self._scale > 0:
                x0 = int((self._roi.x() - self._offset_x) / self._scale)
                y0 = int((self._roi.y() - self._offset_y) / self._scale)
                w = int(self._roi.width() / self._scale)
                h = int(self._roi.height() / self._scale)
                if w > 5 and h > 5:
                    self._roi_img = QRect(x0, y0, w, h)
                else:
                    self._roi_img = None
            else:
                self._roi_img = None
            self.roi_changed.emit(self._roi)
            self.update()

    def roi_clear(self):
        """Roi ve tüm overlay verilerini temizle."""
        self._roi = None
        self._roi_img = getattr(self, "_roi_img", None)
        self._roi_img = None
        self._overlay_text.clear()
        self.update()
        self.roi_changed.emit(None)

    def get_roi_rect(self):
        """Widget içinde ROI dikdörtgeni."""
        return self._roi

    def get_roi_in_image_coords(self):
        """Görüntü koordinatında ROI (x,y,w,h) veya None."""
        return getattr(self, "_roi_img", None)

    def add_overlay_text(self, x, y, text):
        self._overlay_text.append((x, y, text))

    def get_current_frame(self):
        return self._current_frame
