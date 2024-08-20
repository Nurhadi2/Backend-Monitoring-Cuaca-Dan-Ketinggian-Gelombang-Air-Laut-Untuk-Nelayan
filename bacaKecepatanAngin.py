import RPi.GPIO as GPIO
import time

# Konfigurasi GPIO
GPIO.setmode(GPIO.BCM)
anemometer_pin = 22  # Sesuaikan dengan pin GPIO yang Anda gunakan
GPIO.setup(anemometer_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Variabel untuk menghitung kecepatan angin
wind_count = 0  # Menghitung jumlah putaran
radius = 1.23  # Radius baling-baling dalam meter
circumference = 2 * 3.1416 * radius  # Keliling baling-baling

# Konstanta waktu (misal, 5 detik untuk sampel)
sampling_interval = 5  # Detik

def count_wind_speed(channel):
    global wind_count
    wind_count += 1  # Menghitung setiap putaran (1 putaran = 1 pulsa)

# Deteksi event ketika ada pulsa dari anemometer
GPIO.add_event_detect(anemometer_pin, GPIO.FALLING, callback=count_wind_speed, bouncetime=10)

try:
    while True:
        wind_count = 0  # Reset hitungan
        time.sleep(sampling_interval)  # Tunggu selama interval sampling
        
        # Hitung kecepatan angin
        rotations = wind_count / 2  # Setiap putaran menghasilkan 2 pulsa (disesuaikan jika berbeda)
        distance = rotations * circumference  # Jarak yang ditempuh oleh baling-baling
        wind_speed = distance / sampling_interval  # Kecepatan angin dalam meter per detik (m/s)
        
        # Konversi ke km/jam
        wind_speed_kmh = wind_speed * 3.6
        
        print(f"Kecepatan Angin: {wind_speed_kmh:.2f} km/jam")

except KeyboardInterrupt:
    print("Pengukuran dihentikan.")
finally:
    GPIO.cleanup()
