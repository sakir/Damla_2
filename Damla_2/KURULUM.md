# Damla_2 – Raspberry Pi Kurulum Adımları

Klasörü `/home/mercan/Documents/Damla_2` altına kopyaladıysanız aşağıdaki adımları **sırayla** uygulayın.

---

## 1. Sistemi güncelleyin

```bash
sudo apt update
sudo apt full-upgrade -y
```

İsterseniz bu adımdan sonra yeniden başlatın: `sudo reboot`

---

## 2. Python ve temel paketleri kurun

```bash
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y python3-pyqt5 python3-opencv
sudo apt install -y libopenblas-dev libatlas-base-dev
```

---

## 3. Proje klasörüne gidin

```bash
cd /home/mercan/Documents/Damla_2
```

---

## 4. Python bağımlılıklarını kurun

```bash
pip3 install --user numpy
# Pi'de picamera2 genelde sistemle gelir; yoksa:
sudo apt install -y python3-picamera2
```

**Not:** `python3-picamera2` yoksa veya Arducam için özel sürüm gerekiyorsa, önce Adım 5’teki Arducam kurulumunu yapın; Arducam bazen kendi Picamera2’sini kurar.

---

## 5. Arducam 64MP kamera sürücüsünü kurun

Kamerayı kullanmak için Arducam’in sürücü kurulum betiği gerekir.

```bash
cd /home/mercan
wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh
chmod +x install_pivariety_pkgs.sh
```

Sırayla şu üç komutu çalıştırın (her biri birkaç dakika sürebilir):

```bash
./install_pivariety_pkgs.sh -p libcamera_dev
./install_pivariety_pkgs.sh -p libcamera_apps
./install_pivariety_pkgs.sh -p 64mp_pi_hawk_eye_kernel_driver
```

Config dosyasına overlay ekleyin. Raspberry Pi OS **Bookworm / yeni sürümler** için:

```bash
sudo nano /boot/firmware/config.txt
```

Dosyanın **en sonuna** şu satırı ekleyin (kamerayı varsayılan CSI portuna taktıysanız):

```
dtoverlay=arducam-64mp
```

Kaydedip çıkın (Ctrl+O, Enter, Ctrl+X).

**Eski Bullseye** kullanıyorsanız:

```bash
sudo nano /boot/config.txt
```

Aynı satırı en sona ekleyin, kaydedin.

Ardından **mutlaka yeniden başlatın**:

```bash
sudo reboot
```

---

## 6. Yeniden başladıktan sonra kamerayı test edin

```bash
# Kamera görünüyor mu?
libcamera-hello --list-cameras
# veya
rpicam-still --list-cameras
```

Listede 64MP kamera görünmeli. Kısa bir test çekimi:

```bash
rpicam-still -t 3000 -o ~/test_foto.jpg
```

---

## 7. (İsteğe bağlı) WS2812 LED için rpi_ws281x

Sadece LED stick kullanacaksanız:

```bash
sudo apt install -y python3-dev
pip3 install --user rpi_ws281x
```

LED kullanmayacaksanız bu adımı atlayabilirsiniz; program LED yoksa hata vermeden çalışır.

---

## 8. Damla_2 uygulamasını çalıştırın

```bash
cd /home/mercan/Documents/Damla_2
python3 main.py
```

Masaüstü (GUI) ortamında olmanız gerekir. SSH ile bağlıysanız:

```bash
export DISPLAY=:0
python3 main.py
```

veya doğrudan Pi’nin ekranına bağlı klavye/ekranla oturum açıp terminalden `python3 main.py` çalıştırın.

---

## Özet sıra

| Sıra | Ne yapıyorsunuz |
|------|------------------|
| 1 | `sudo apt update && sudo apt full-upgrade -y` |
| 2 | `sudo apt install -y python3-pyqt5 python3-opencv python3-pip` (+ gerekirse `python3-picamera2`) |
| 3 | `cd /home/mercan/Documents/Damla_2` |
| 4 | `pip3 install --user numpy` |
| 5 | Arducam betiğini indir, `libcamera_dev` → `libcamera_apps` → `64mp_pi_hawk_eye_kernel_driver` kur |
| 6 | `/boot/firmware/config.txt` (veya `/boot/config.txt`) sonuna `dtoverlay=arducam-64mp` ekle |
| 7 | `sudo reboot` |
| 8 | `libcamera-hello --list-cameras` ile kamerayı kontrol et |
| 9 | (İsteğe bağlı) `pip3 install --user rpi_ws281x` |
| 10 | `cd /home/mercan/Documents/Damla_2` → `python3 main.py` |

---

## Sorun çıkarsa

- **“No module named 'PyQt5'”**  
  `sudo apt install -y python3-pyqt5`

- **“No module named 'picamera2'”**  
  `sudo apt install -y python3-picamera2` veya Arducam kurulumunu tekrar yapın.

- **Kamera listelenmiyor**  
  `config.txt` değişikliğini yaptıktan sonra mutlaka `sudo reboot` yapın; CSI kablonun doğru takılı olduğundan emin olun.

- **LED hatası**  
  LED kullanmıyorsanız bu adımı atlayın; program LED olmadan da çalışır.

Bu adımları sırayla uyguladığınızda Damla_2’yi Raspberry Pi’de çalıştırmış olursunuz.
