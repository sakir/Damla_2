# -*- coding: utf-8 -*-
"""Wenzel modeli: pürüzlü yüzeyde temas açısı."""

import numpy as np


def wenzel_angle(
    image_bw, roi_contour_or_mask,
    roughness_factor=1.2,
    smooth_contact_angle_deg=None,
    px_per_mm=1.0
):
    """
    Wenzel: cos(theta_rough) = R_f * cos(theta_smooth).
    smooth_contact_angle_deg verilmezse circle fitting ile tahmin edilir.
    """
    if smooth_contact_angle_deg is None:
        try:
            from .circle_fitting import circle_fitting_contact_angle
        except ImportError:
            from circle_fitting import circle_fitting_contact_angle
        smooth_contact_angle_deg, err = circle_fitting_contact_angle(
            image_bw, roi_contour_or_mask, px_per_mm=px_per_mm
        )
        if smooth_contact_angle_deg is None:
            return None, err
    rad = np.radians(smooth_contact_angle_deg)
    cos_rough = roughness_factor * np.cos(rad)
    cos_rough = np.clip(cos_rough, -1, 1)
    angle_deg = np.degrees(np.arccos(cos_rough))
    return float(np.clip(angle_deg, 0, 180)), None
