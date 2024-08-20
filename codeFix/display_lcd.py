from RPLCD import *
from time import sleep
from RPLCD.i2c import CharLCD
lcd = CharLCD('PCF8574', 0x27)
import os
import glob
import time
import subprocess
import socket
import Adafruit_DHT
import time
 
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def get_internal_temp():
	sensor = Adafruit_DHT.DHT22
	pin = 23

	humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
	return humidity, temperature

def get_ip_address(interface):
    try:
        # Buat socket dan dapatkan alamat IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect((f"8.8.8.8", 1))  # Menggunakan DNS Google
        ip_address = s.getsockname()[0]
        return ip_address
    except Exception as e:
        return "Tidak Diketahui"

def get_IP():
	IP = subprocess.check_output(["hostname", "-I"]).split()[0]
	IP2 = 'IP' + str(IP)
	IP3 = (IP2[5:-1])
	return IP3

def get_cpu_temp():
	tmp = open('/sys/class/thermal/thermal_zone0/temp')
	cpu = tmp.read()
	tmp.close()
	return '{:.2f}'.format( float(cpu)/1000 ) + ' C'

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines



def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c
try:
	while True:
		temperature_celsius = read_temp()
		temperature_cpu = get_cpu_temp()
		suhu_internal = get_internal_temp()
		internal_temperature_celsius = str(round(suhu_internal[1],1))
		ip_wlan = get_ip_address("wlan0")
		ip = str(get_IP())
		#cpu_temperature = round(temperature_cpu,2)
		temperature = round(temperature_celsius,1)
		suhu = str(temperature)
		cpu = str(temperature_cpu)
		#internal_temp_str = str(interal_temperature_celsius)
		lcd.cursor_pos = (0, 0)
		lcd.write_string("Suhu Laut: "+suhu)
		lcd.cursor_pos = (1, 0)
		lcd.write_string("CPU: "+cpu)
		lcd.cursor_pos = (2, 0)
		lcd.write_string("IP: "+ip_wlan)
		lcd.cursor_pos = (3,0)
		lcd.write_string("Suhu Internal: "+internal_temperature_celsius)
		print(round(suhu_internal[1], 1))
		time.sleep(5)
except KeyboardInterrupt:
    # If there is a KeyboardInterrupt (when you press ctrl+c), exit the program>
	print("Cleaning up!")
	lcd.clear()


#lcd.cursor_pos = (0, 0)
#lcd.write_string('Hello Nurhadi Sasono :)')
