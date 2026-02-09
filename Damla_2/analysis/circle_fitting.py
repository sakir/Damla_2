# -*- coding: utf-8 -*-
"""Circle fitting (dairesel yay) ile temas açısı."""

import cv2
import numpy as np


def circle_fitting_contact_angle(
    image_bw, roi_contour_or_mask,
    edge_threshold=50, min_radius_px=20,
    px_per_mm=1.0
):
    """
    ROI içindeki damla profilini dairesel yay ile uydurur, temas açısı (derece) döner.
    image_bw: gri görüntü
    roi_contour_or_mask: OpenCV contour veya binary mask
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
    edges = cv2.Canny(roi, edge_threshold, edge_threshold * 2)
    pts = np.column_stack(np.where(edges > 0))
    if len(pts) < 5:
        return None, "Yeterli kenar noktası yok"
    pts_xy = pts[:, [1, 0]].astype(np.float32)
    (cx, cy), radius = cv2.minEnclosingCircle(pts_xy)
    if radius < min_radius_px:
        return None, "Çok küçük daire"
    # Temas açısı: daire ile yatay (taban) arasındaki açı
    # Basit geometri: taban y = max(pts[:,0]); teğet açı
    y_base = float(np.max(pts[:, 0]))
    dy = y_base - cy
    if abs(dy) < 1e-6:
        return 90.0, None
    # cos(contact_angle) = dy / radius -> contact_angle = arccos(dy/radius)
    cos_a = np.clip(dy / radius, -1, 1)
    angle_rad = np.arccos(cos_a)
    angle_deg = np.degrees(angle_rad)
    return angle_deg, None
