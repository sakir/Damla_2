# -*- coding: utf-8 -*-
"""Damla_2 - Yapılandırma ve sabitler."""

# Kamera çözünürlükleri (Arducam 64MP - sensör modları)
RESOLUTIONS = [
    (1280, 720),
    (2312, 1736),
    (4624, 3472),
    (9152, 6944),
]
DEFAULT_RESOLUTION = (2312, 1736)

# Görüntü modları
IMAGE_MODES = ["Renkli", "Gri"]

# Aydınlatma filtreleri
LIGHT_FILTERS = ["Yok", "CLAHE", "Gamma"]
DEFAULT_LIGHT_FILTER = "Gamma"

# Zoom 1-15x
ZOOM_MIN, ZOOM_MAX = 1, 15
ZOOM_DEFAULT = 1

# Focus default (manuel)
FOCUS_DEFAULT = 9

# Pan default
PAN_DEFAULT = (0, 0)

# LED lokasyonları (8'li stick: Tumu, Sag_Dis, Sol_Dis, Orta)
LED_LOCATIONS = ["Yok", "Tumu", "Sag_Dis", "Sol_Dis", "Orta"]
LED_COUNT = 8

# Analiz modelleri
ANALYSIS_MODELS = [
    "Young_Laplace",
    "Wenzel",
    "Circle_Fitting",
    "Cassie_Baxter",
    "Polynominal_Fitting",
]
DEFAULT_ANALYSIS_MODEL = "Circle_Fitting"

# Model parametreleri (slider için min, max, default)
# Young-Laplace: yüzey gerilimi (mN/m), Bond sayısı
YOUNG_LAPLACE_PARAMS = {
    "surface_tension": (10, 100, 72.8),
    "bond_number": (0.01, 2.0, 0.5),
}
# Wenzel: pürüzlülük faktörü R_f
WENZEL_PARAMS = {
    "roughness_factor": (1.0, 3.0, 1.2),
}
# Circle fitting: eşik / hassasiyet
CIRCLE_FITTING_PARAMS = {
    "edge_threshold": (1, 100, 50),
    "min_radius_px": (5, 100, 20),
}
# Cassie-Baxter: f1 (katı alan oranı), theta1 (derece)
CASSIE_BAXTER_PARAMS = {
    "f1": (0.0, 1.0, 0.5),
    "theta1_deg": (0, 180, 110),
}
# Polynomial fitting: polinom derecesi
POLYNOMIAL_FITTING_PARAMS = {
    "degree": (2, 6, 4),
}

# Performans: gösterilecek alan (300mm mesafe, 50x50mm nesne - piksel alanı hesaplanacak)
MAX_DISTANCE_MM = 300
OBJECT_WIDTH_MM = 50
OBJECT_HEIGHT_MM = 50
CROP_ENABLED = True
# Görsel alanı biraz genişletmek için (1.0 = tam, 1.2 = %20 pay)
CROP_MARGIN = 1.1

# Veritabanı
DB_PATH = "damla_2.db"
