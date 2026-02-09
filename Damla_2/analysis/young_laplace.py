# -*- coding: utf-8 -*-
"""Young-Laplace eşitliği ile damla profil uydurma (basitleştirilmiş)."""

import numpy as np


def young_laplace_fit(
    image_bw, roi_contour_or_mask,
    surface_tension=72.8, bond_number=0.5,
    px_per_mm=1.0
):
    """
    Young-Laplace ile temas açısı tahmini.
    surface_tension: mN/m
    bond_number: Bond sayısı (gravite etkisi)
    ROI'den önce circle fitting ile kaba açı, sonra Y-L düzeltmesi (basit model).
    """
    try:
        from .circle_fitting import circle_fitting_contact_angle
    except ImportError:
        from circle_fitting import circle_fitting_contact_angle
    angle_circle, err = circle_fitting_contact_angle(
        image_bw, roi_contour_or_mask, px_per_mm=px_per_mm
    )
    if angle_circle is None:
        return None, err
    # Basit düzeltme: Bond sayısı arttıkça damla yassılaşır, görünen açı küçülür
    correction = 1.0 + 0.1 * (bond_number - 0.5)
    angle_yl = angle_circle * correction
    return float(np.clip(angle_yl, 0, 180)), None
