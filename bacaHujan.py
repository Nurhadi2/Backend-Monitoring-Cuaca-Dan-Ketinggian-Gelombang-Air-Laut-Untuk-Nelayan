import RPi.GPIO as GPIO
import time

# Konfigurasi pin GPIO
pin_interrupt = 27  # Sesuaikan dengan pin GPIO yang Anda gunakan
milimeter_per_tip = 0.70

# Variabel global
jumlah_tip = 0
curah_hujan = 0.00

flag = False

# Konfigurasi GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_interrupt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def hitung_curah_hujan(channel):
    global flag
    flag = True

# Tambahkan event detect untuk interrupt
GPIO.add_event_detect(pin_interrupt, GPIO.FALLING, callback=hitung_curah_hujan, bouncetime=499)

def printSerial():
    global jumlah_tip, curah_hujan
    print(f"Jumlah tip={jumlah_tip} kali")
    print(f"Curah hujan={curah_hujan:.1f} mm")
    print()

try:
    while True:
        if flag:
            curah_hujan += milimeter_per_tip
            jumlah_tip += 1
            time.sleep(0.5)
            flag = False

        curah_hujan = jumlah_tip * milimeter_per_tip

        printSerial()
        time.sleep(1)

except KeyboardInterrupt:
    print("Program dihentikan")
    GPIO.cleanup()
