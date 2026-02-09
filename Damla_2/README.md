# Damla_2 – Su Damlası Ölçüm Programı

Raspberry Pi 5, Arducam 64MP ve WS2812 LED ile su damlası (temas açısı) ölçümü için arayüz ve analiz yazılımı.

## Donanım

- **Raspberry Pi 5** (8 GB)
- **Rasperian** (Raspberry Pi OS)
- **Arducam 64MP** kamera
- **WS2812** 8’li RGB LED stick

## Kurulum (Raspberry Pi)

1. Gerekli paketler:

```bash
sudo apt update
sudo apt install -y python3-pyqt5 python3-opencv python3-pip
pip3 install numpy
```

2. Arducam 64MP sürücü ve Picamera2 (Arducam’in kurulum betiği ile):

```bash
wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh
chmod +x install_pivariety_pkgs.sh
./install_pivariety_pkgs.sh -p libcamera_dev
./install_pivariety_pkgs.sh -p libcamera_apps
./install_pivariety_pkgs.sh -p 64mp_pi_hawk_eye_kernel_driver
```

`/boot/firmware/config.txt` (veya `/boot/config.txt`) dosyasına ekleyin:

```
dtoverlay=arducam-64mp
```

Ardından yeniden başlatın: `sudo reboot`

3. Picamera2 Python:

```bash
pip3 install picamera2
```

4. WS2812 (isteğe bağlı):

```bash
pip3 install rpi_ws281x
```

5. Uygulamayı çalıştırma:

```bash
cd Damla_2
python3 main.py
```

## Arayüz

- **Sol:** Kamera görüntüsü (sadece ölçüm alanı; performans için ~300 mm mesafe, 50×50 mm nesne alanı).
- **Sağ:** Sekmeli menü – **Kamera**, **Aydınlatma**, **Kalibrasyon**, **Analiz**, **Log**.

### Kamera sekmesi

- Çözünürlük: (1280×720), (2312×1736), (4624×3472), (9152×6944) – varsayılan 2312×1736
- FPS slider ve gerçek FPS
- Görüntü modu: Renkli / Gri
- Aydınlatma filtresi: Yok, CLAHE, Gamma (Gamma/CLAHE slider’ları)
- Zoom: 1–15×
- Focus: Manuel (F+/F−, netlik değeri) veya Otomatik (Autofocus tekrarla)
- Pan: Yukarı, Aşağı, Sol, Sağ, Merkeze
- Preset: Kaydet, Düzenle, Sil, Uygula, Başlangıç (veritabanı)

### Aydınlatma sekmesi

- **Led_Test:** R, G, B sırayla 3 saniye; kamera ile onay sonrası buton “Test_OK”
- R/G/B parlaklık slider’ları
- Lokasyon: Yok, Tumu, Sag_Dis, Sol_Dis, Orta
- 8 LED için tek tek checkbox
- Preset: Kaydet, Düzenle, Sil, Uygula, Başlangıç

### Kalibrasyon sekmesi

- İsim, Genişlik (mm), Yükseklik (mm), Uzaklık (mm)
- Kaydet, Yeni Kaydet (veritabanı)

### Analiz sekmesi

- **Roi_Temizle:** ROI ve overlay’leri temizle
- Model: Young_Laplace, Wenzel, Circle_Fitting, Cassie_Baxter, Polynominal_Fitting (varsayılan: Circle_Fitting)
- Seçili modele göre parametre slider’ları
- **Hesapla:** ROI seçiliyken seçilen modele göre temas açısı hesaplar

### Log sekmesi

- Olay ve hata logları, Log temizle butonu

## Veritabanı

SQLite: `damla_2.db` (kamera/aydınlatma/kalibrasyon preset’leri ve başlangıç preset’leri).

## Geliştirme / Test (kamera yok)

Kamera yoksa veya Pi dışında çalıştırıyorsanız, `camera_service` OpenCV ile varsayılan web kamerasına düşer; LED servisi donanım yoksa sessizce atlanır.
