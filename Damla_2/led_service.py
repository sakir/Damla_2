# -*- coding: utf-8 -*-
"""WS2812 8'li stick LED servisi. Raspberry Pi'de rpi_ws281x, yoksa mock."""

import time

try:
    from rpi_ws281x import Adafruit_NeoPixel, Color
    WS281X_AVAILABLE = True
except ImportError:
    WS281X_AVAILABLE = False
    Adafruit_NeoPixel = None
    Color = None

from config import LED_COUNT

# Pin (GPIO 18 = PWM0)
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_INVERT = False
LED_CHANNEL = 0


class LedService:
    """8 adet WS2812 LED kontrolü. Lokasyon: Tumu, Sag_Dis, Sol_Dis, Orta (stick grupları)."""

    def __init__(self, num_leds=LED_COUNT):
        self.num_leds = num_leds
        self._strip = None
        self._brightness_r = 128
        self._brightness_g = 128
        self._brightness_b = 128
        self._location = "Yok"
        self._leds_mask = 0  # 0..255, her bit bir LED
        if WS281X_AVAILABLE and Adafruit_NeoPixel:
            try:
                self._strip = Adafruit_NeoPixel(
                    num_leds, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, 128, LED_CHANNEL
                )
                self._strip.begin()
            except Exception:
                self._strip = None
        else:
            self._strip = None

    def set_brightness_rgb(self, r, g, b):
        self._brightness_r = max(0, min(255, int(r)))
        self._brightness_g = max(0, min(255, int(g)))
        self._brightness_b = max(0, min(255, int(b)))

    def set_location(self, location):
        self._location = location
        # Lokasyona göre hangi LED'lerin yanacağı: basit eşleme
        # 8 LED: indeks 0-7. Tumu=hepsi, Sag_Dis=4-7, Sol_Dis=0-3, Orta=2-5
        if location == "Yok":
            self._leds_mask = 0
        elif location == "Tumu":
            self._leds_mask = 0xFF
        elif location == "Sag_Dis":
            self._leds_mask = 0xF0
        elif location == "Sol_Dis":
            self._leds_mask = 0x0F
        elif location == "Orta":
            self._leds_mask = 0x3C
        else:
            self._leds_mask = 0

    def set_leds_mask(self, mask):
        """mask: 0-255, her bit bir LED (0=kapalı, 1=açık)."""
        self._leds_mask = int(mask) & 0xFF
        # Lokasyon "Yok" ise mask'i kullan; lokasyon seçiliyse lokasyon mask ile birleştir
        self._update_strip()

    def get_leds_mask(self):
        return self._leds_mask

    def _update_strip(self):
        if self._strip is None:
            return
        # Lokasyon seçiliyse: lokasyon mask & leds_mask; yoksa sadece leds_mask
        if self._location == "Yok":
            active = self._leds_mask
        else:
            loc_mask = self._leds_mask_from_location(self._location)
            active = loc_mask & self._leds_mask
        r = (self._brightness_r * self._strip.getBrightness()) // 255
        g = (self._brightness_g * self._strip.getBrightness()) // 255
        b = (self._brightness_b * self._strip.getBrightness()) // 255
        for i in range(self.num_leds):
            if (active >> i) & 1:
                self._strip.setPixelColor(i, Color(g, r, b))
            else:
                self._strip.setPixelColor(i, Color(0, 0, 0))
        self._strip.show()

    def _leds_mask_from_location(self, location):
        if location == "Tumu":
            return 0xFF
        if location == "Sag_Dis":
            return 0xF0
        if location == "Sol_Dis":
            return 0x0F
        if location == "Orta":
            return 0x3C
        return 0

    def set_location_and_mask(self, location, leds_mask):
        self._location = location
        self._leds_mask = int(leds_mask) & 0xFF
        self._update_strip()

    def all_off(self):
        self._leds_mask = 0
        self._location = "Yok"
        self._update_strip()

    def set_color_only(self, r, g, b):
        """Sadece renk değiştir, mask/lokasyon aynı kalsın."""
        self._brightness_r = max(0, min(255, int(r)))
        self._brightness_g = max(0, min(255, int(g)))
        self._brightness_b = max(0, min(255, int(b)))
        self._update_strip()

    def test_sequence(self, duration_sec=3, on_confirm=None):
        """R, G, B sırayla yakar; her renk duration_sec saniye. on_confirm('R'/'G'/'B') ile kullanıcı onayı."""
        colors = [
            ("R", 255, 0, 0),
            ("G", 0, 255, 0),
            ("B", 0, 0, 255),
        ]
        for name, r, g, b in colors:
            self.set_location("Tumu")
            self.set_brightness_rgb(r, g, b)
            self.set_leds_mask(0xFF)
            self._update_strip()
            if on_confirm:
                on_confirm(name)
            time.sleep(duration_sec)
        self.all_off()
