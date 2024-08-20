import RPi.GPIO as GPIO
import time
from datetime import datetime

# Setup GPIO
pin_interrupt = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_interrupt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize variables
jumlah_tip = 0
curah_hujan = 0.00
curah_hujan_per_menit = 0.00
curah_hujan_per_jam = 0.00
curah_hujan_per_hari = 0.00
curah_hujan_hari_ini = 0.00
temp_curah_hujan_per_menit = 0.00
temp_curah_hujan_per_jam = 0.00
temp_curah_hujan_per_hari = 0.00
milimeter_per_tip = 0.70
cuaca = ""

flag = False

# Interrupt callback
def hitung_curah_hujan(channel):
    global flag
    flag = True

# Attach interrupt
GPIO.add_event_detect(pin_interrupt, GPIO.FALLING, callback=hitung_curah_hujan, bouncetime=500)

def konversi_jam(angka):
    if len(angka) == 1:
        angka = "0" + angka
    return angka

try:
    while True:
        if flag:
            curah_hujan += milimeter_per_tip
            jumlah_tip += 1
            flag = False

        now = datetime.now()
        jam = konversi_jam(str(now.hour))
        menit = konversi_jam(str(now.minute))
        detik = konversi_jam(str(now.second))
        
        curah_hujan_hari_ini = jumlah_tip * milimeter_per_tip
        print(f"{jam}:{menit}:{detik} -> {jumlah_tip} tips, {curah_hujan_hari_ini:.2f} mm")

        temp_curah_hujan_per_menit = curah_hujan

        if curah_hujan_hari_ini <= 0.50:
            cuaca = "Berawan"
        elif curah_hujan_hari_ini <= 20.00:
            cuaca = "Hujan Ringan"
        elif curah_hujan_hari_ini <= 50.00:
            cuaca = "Hujan Sedang"
        elif curah_hujan_hari_ini <= 100.00:
            cuaca = "Hujan Lebat"
        elif curah_hujan_hari_ini <= 150.00:
            cuaca = "Hujan Sangat Lebat"
        else:
            cuaca = "Hujan Ekstrem"

        print(f"Cuaca saat ini: {cuaca}")

        if detik == "00":
            curah_hujan_per_menit = temp_curah_hujan_per_menit
            temp_curah_hujan_per_jam += curah_hujan_per_menit
            
            if menit == "00":
                curah_hujan_per_jam = temp_curah_hujan_per_jam
                temp_curah_hujan_per_hari += curah_hujan_per_jam
                temp_curah_hujan_per_jam = 0.00

            if menit == "00" and jam == "00":
                curah_hujan_per_hari = temp_curah_hujan_per_hari
                temp_curah_hujan_per_hari = 0.00
                curah_hujan_hari_ini = 0.00
                jumlah_tip = 0

            print(f"Curah hujan per menit: {curah_hujan_per_menit:.1f} mm")
            print(f"Curah hujan per jam: {curah_hujan_per_jam:.1f} mm")
            print(f"Curah hujan per hari: {curah_hujan_per_hari:.1f} mm")

        time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()
