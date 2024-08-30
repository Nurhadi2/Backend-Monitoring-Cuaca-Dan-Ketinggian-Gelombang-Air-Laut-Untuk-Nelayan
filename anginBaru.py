import RPi.GPIO as GPIO
import time
import threading

# Parameter anemometer
rpmcount = 0  # Menghitung sinyal
last_micros = 0
timeold = 0
timemeasure = 10  # detik
timetoSleep = 1  # menit
sleepTime = 15  # menit
timeNow = 0
countThing = 0
GPIO_pulse = 22  # GPIO pin untuk pulse dari anemometer
flag = threading.Event()  # Menggunakan threading.Event untuk mengelola flag

rotasi_per_detik = 0.0  # rotasi/detik
kecepatan_kilometer_per_jam = 0.0  # kilometer/jam
kecepatan_meter_per_detik = 0.0  # meter/detik

def rpm_anemometer(channel):
    global flag
    flag.set()  # Set flag untuk menandakan ada sinyal yang diterima

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_pulse, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(GPIO_pulse, GPIO.RISING, callback=rpm_anemometer, bouncetime=5)

def loop():
    global rpmcount, last_micros, timeold, countThing, rotasi_per_detik, kecepatan_kilometer_per_jam, kecepatan_meter_per_detik

    while True:
        if flag.is_set():
            current_micros = time.time() * 1e6  # Mengambil waktu dalam mikrodetik
            if (current_micros - last_micros) >= 5000:  # 5000 mikrodetik = 5 milidetik
                rpmcount += 1
                last_micros = current_micros
            flag.clear()

        if (time.time() * 1e3 - timeold) >= timemeasure * 1000:
            countThing += 1
            GPIO.remove_event_detect(GPIO_pulse)  # Nonaktifkan interrupt saat menghitung
            rotasi_per_detik = float(rpmcount) / float(timemeasure)  # Rotasi per detik

            # Kalibrasi kecepatan angin dalam meter per detik
            kecepatan_meter_per_detik = ((-0.0181 * (rotasi_per_detik ** 2)) + (1.3859 * rotasi_per_detik) + 1.4055)
            if kecepatan_meter_per_detik <= 1.5:  # Minimum pembacaan sensor kecepatan angin
                kecepatan_meter_per_detik = 0.0

            kecepatan_kilometer_per_jam = kecepatan_meter_per_detik * 3.6  # Kilometer/jam

            print(f"rotasi_per_detik={rotasi_per_detik}   kecepatan_meter_per_detik={kecepatan_meter_per_detik:.1f}   kecepatan_kilometer_per_jam={kecepatan_kilometer_per_jam}")

            if countThing == 1:  # Mengirim data setiap 10 detik sekali
                print("Mengirim data ke server")
                countThing = 0

            timeold = time.time() * 1e3  # Update waktu
            rpmcount = 0  # Reset rpmcount
            GPIO.add_event_detect(GPIO_pulse, GPIO.RISING, callback=rpm_anemometer, bouncetime=5)  # Aktifkan interrupt kembali

if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        GPIO.cleanup()  # Bersihkan GPIO saat program dihentikan
