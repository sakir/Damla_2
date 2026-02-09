# -*- coding: utf-8 -*-
"""Polinom uydurma ile damla profili ve temas açısı."""

import cv2
import numpy as np


def polynomial_fitting_contact_angle(
    image_bw, roi_contour_or_mask,
    degree=4,
    px_per_mm=1.0
):
    """
    ROI kenarını polinom ile uydurur, taban noktasındaki eğimden temas açısı.
    """
    if image_bw is None:
        return None, "Görüntü yok"
    if isinstance(roi_contour_or_mask, np.ndarray) and roi_contour_or_mask.ndim == 2:
        mask = roi_contour_or_mask
    else:
        h, w = image_bw.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(mask, [roi_contour_or_mask], -1, 255, -1)
    roi = cv2.bitwise_and(image_bw, image_bw, mask=mask)
    edges = cv2.Canny(roi, 30, 60)
    pts = np.column_stack(np.where(edges > 0))
    if len(pts) < degree + 2:
        return None, "Yeterli nokta yok"
    # x = col, y = row (görüntüde y aşağı)
    x = pts[:, 1].astype(np.float64)
    y = pts[:, 0].astype(np.float64)
    coeffs = np.polyfit(x, y, min(degree, len(pts) - 1))
    poly = np.poly1d(coeffs)
    # Taban: y maksimum olduğu x
    x_flat = np.linspace(x.min(), x.max(), 50)
    y_flat = poly(x_flat)
    idx = np.argmax(y_flat)
    x_base = x_flat[idx]
    y_base = y_flat[idx]
    # Türev at x_base -> eğim
    dpoly = np.polyder(poly)
    slope = dpoly(x_base)
    angle_rad = np.arctan(np.abs(slope))
    angle_deg = np.degrees(angle_rad)
    return float(np.clip(angle_deg, 0, 180)), None
