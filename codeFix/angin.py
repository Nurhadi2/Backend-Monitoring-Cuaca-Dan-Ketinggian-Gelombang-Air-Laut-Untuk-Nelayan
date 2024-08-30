import RPi.GPIO as GPIO
import time

# Parameter anemometer
rpmcount = 0
GPIO_pulse = 22  # GPIO pin untuk pulse dari anemometer
timemeasure = 10  # Waktu pengukuran dalam detik
threshold = 1.5  # Batas minimum untuk dianggap sebagai kecepatan non-zero

def rpm_anemometer(channel):
    global rpmcount
    rpmcount += 1

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_pulse, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(GPIO_pulse, GPIO.RISING, callback=rpm_anemometer, bouncetime=5)  # Inisialisasi interrupt

def calculate_wind_speed():
    rotasi_per_detik = rpmcount / timemeasure  # Rotasi per detik
    kecepatan_meter_per_detik = max(0, (-0.0181 * (rotasi_per_detik ** 2)) + (1.3859 * rotasi_per_detik) + 1.4055)

    if kecepatan_meter_per_detik < threshold:  # Jika kecepatan di bawah ambang batas
        kecepatan_meter_per_detik = 0.0

    print(f"Kecepatan angin: {kecepatan_meter_per_detik:.1f} m/s")

def loop():
    global rpmcount
    while True:
        time.sleep(timemeasure)  # Tunggu selama waktu pengukuran
        GPIO.remove_event_detect(GPIO_pulse)  # Menonaktifkan interrupt saat menghitung
        calculate_wind_speed()
        rpmcount = 0  # Reset hitungan rpm
        GPIO.add_event_detect(GPIO_pulse, GPIO.RISING, callback=rpm_anemometer, bouncetime=5)  # Aktifkan interrupt kembali

if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        GPIO.cleanup()  # Bersihkan GPIO saat program dihentikan
