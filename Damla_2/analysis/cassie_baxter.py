# -*- coding: utf-8 -*-
"""Cassie-Baxter modeli: heterojen yüzey."""

import numpy as np


def cassie_baxter_angle(
    image_bw, roi_contour_or_mask,
    f1=0.5, theta1_deg=110,
    theta2_deg=180,
    px_per_mm=1.0
):
    """
    Cassie-Baxter: cos(theta_c) = f1*cos(theta1) + f2*cos(theta2), f1+f2=1.
    f1: birinci faz alan oranı, theta1_deg: o fazın temas açısı.
    """
    f2 = 1.0 - f1
    cos_c = f1 * np.cos(np.radians(theta1_deg)) + f2 * np.cos(np.radians(theta2_deg))
    cos_c = np.clip(cos_c, -1, 1)
    angle_deg = np.degrees(np.arccos(cos_c))
    return float(np.clip(angle_deg, 0, 180)), None
