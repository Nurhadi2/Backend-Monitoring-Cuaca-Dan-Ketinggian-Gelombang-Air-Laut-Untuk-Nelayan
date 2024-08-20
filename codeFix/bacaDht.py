import Adafruit_DHT
import time

# Tentukan jenis sensor dan pin yang digunakan
sensor = Adafruit_DHT.DHT22
pin = 23  # Pin GPIO yang terhubung dengan pin data sensor

while True:
    # Membaca data dari sensor
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

    if humidity is not None and temperature is not None:
        print(f"Suhu: {temperature:.1f}°C  Kelembapan: {humidity:.1f}%")
    else:
        print("Gagal membaca data dari sensor DHT22")

    # Tunggu 2 detik sebelum membaca ulang
    time.sleep(2)
