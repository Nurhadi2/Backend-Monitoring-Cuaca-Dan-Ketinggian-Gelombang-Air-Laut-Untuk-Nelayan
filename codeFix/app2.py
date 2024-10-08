import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
import time
import random
import smbus2
import bme280
import RPi.GPIO as GPIO
from datetime import datetime, timedelta
import sqlite3
import threading

app = Flask(__name__)
socketio = SocketIO(app, ping_timeout=60, ping_interval=25)

# Initialize sensors
bme280_address = 0x76
bus = smbus2.SMBus(1)
calibration_params = bme280.load_calibration_params(bus, bme280_address)

TRIG = 15
ECHO = 14
anemometer_pin = 22
rain_sensor_pin = 27  # Pin untuk sensor hujan

# Anemometer parameters
rpmcount = 0
last_micros = 0
timeold = 0
timemeasure = 30  # seconds
flag = threading.Event()  # For managing interrupts

# Rainfall parameters
milimeter_per_tip = 0.70
jumlah_tip = 0
curah_hujan = 0.00
rain_flag = False

#radius = 10.5  # cm
interval = 1  # seconds
background_task_started = False

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(anemometer_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(rain_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def check_login(username, password):
    conn = sqlite3.connect('monitoring.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tb_users WHERE username=? AND password=? ", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(nama_lengkap, username, password):
    conn = sqlite3.connect('monitoring.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tb_users(nama_lengkap, username, password) VALUES(?, ?, ?)", (nama_lengkap, username, password))
    conn.commit()
    conn.close()

def save_sensor_data_to_db(data):
    conn = sqlite3.connect('monitoring.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tb_data (suhu, tinggi_gelombang, kecepatan_angin, intensitas_hujan, tanggal_waktu)
        VALUES (?, ?, ?, ?, ?)
    """, (data['temperature_celsius'], data['wave_height'], data['wind_speed'], data['rain_intensity'], data['tanggal_waktu']))
    conn.commit()
    conn.close()

def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32

def read_bme280_sensor():
    try:
        data = bme280.sample(bus, bme280_address, calibration_params)
        return {'temperature_celsius': round(data.temperature, 2)}
    except Exception as e:
        print(f'Error reading BME280 sensor: {e}')
        return None

def read_ultrasonic_sensor():
    try:
        GPIO.output(TRIG, False)
        time.sleep(2)

        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        pulse_start = time.time()
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()

        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150 / 100
        distance = 4.06 - distance

        return distance
    except Exception as e:
        print(f'Error reading ultrasonic sensor: {e}')
        return None

def calculate_wind_speed():
    global rpmcount, last_micros, timeold, flag

    while True:
        if flag.is_set():
            current_micros = time.time() * 1e6
            if (current_micros - last_micros) >= 5000:
                rpmcount += 1
                last_micros = current_micros
            flag.clear()

        if (time.time() * 1e3 - timeold) >= timemeasure * 1000:
            GPIO.remove_event_detect(anemometer_pin)

            rotations_per_sec = float(rpmcount) / float(timemeasure)
            wind_speed_meter_per_sec = ((-0.0181 * (rotations_per_sec ** 2)) + (1.3859 * rotations_per_sec) + 1.4055)
            if wind_speed_meter_per_sec <= 1.5:
                wind_speed_meter_per_sec = 0.0

            wind_speed_km_per_h = wind_speed_meter_per_sec * 3.6

            timeold = time.time() * 1e3
            rpmcount = 0
            GPIO.add_event_detect(anemometer_pin, GPIO.RISING, callback=rpm_anemometer, bouncetime=5)
            return wind_speed_meter_per_sec

def rpm_anemometer(channel):
    global flag
    flag.set()

GPIO.add_event_detect(anemometer_pin, GPIO.RISING, callback=rpm_anemometer, bouncetime=5)

def hitung_curah_hujan(channel):
    global rain_flag
    rain_flag = True

GPIO.add_event_detect(rain_sensor_pin, GPIO.FALLING, callback=hitung_curah_hujan, bouncetime=499)

def read_rain_sensor():
    global jumlah_tip, curah_hujan, rain_flag

    if rain_flag:
        curah_hujan += milimeter_per_tip
        jumlah_tip += 1
        rain_flag = False

    curah_hujan = jumlah_tip * milimeter_per_tip
    return curah_hujan

def reset_rainfall_at_midnight():
    global jumlah_tip, curah_hujan
    while True:
        current_time = datetime.now()
        next_midnight = (current_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        sleep_time = (next_midnight - current_time).total_seconds()
        time.sleep(sleep_time)

        # Reset rainfall data
        jumlah_tip = 0
        curah_hujan = 0.00
        print('Rainfall data reset at midnight')

def generate_sensor_data():
    global flag
    while True:
        bme280_data = read_bme280_sensor()
        ultrasonic_distance = read_ultrasonic_sensor()
        wind_speed = calculate_wind_speed()
        rain_intensity = read_rain_sensor()

        if bme280_data and ultrasonic_distance is not None:
            current_time = datetime.now()
            combined_data = {
                'temperature_celsius': "{:.2f}".format(bme280_data['temperature_celsius']),
                'wave_height': "{:.2f}".format(ultrasonic_distance),
                'wind_speed': "{:.2f}".format(wind_speed),
                'rain_intensity': "{:.2f}".format(rain_intensity),
                'timestamp': str(int(time.time())),
                'tanggal_waktu': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            print('Combined Data:', combined_data, datetime.now())
            #print(rain_intensity)
            socketio.emit('update', combined_data)
            save_sensor_data_to_db(combined_data)
        else:
            print('Error in sensor data')

        socketio.sleep(2)

@app.route("/")
def hello_world():
    return "hello world"

@app.route('/register', methods=['POST'])
def process_register():
    data_nama_lengkap = request.form['nama_lengkap']
    data_username = request.form['username']
    data_password = request.form['password']
    add_user(nama_lengkap=data_nama_lengkap, username=data_username, password=data_password)
    return jsonify({'status': True, 'message': 'Registrasi Berhasil'}), 201

@app.route('/login', methods=['POST'])
def process_login():
    data_username = request.form['username']
    data_password = request.form['password']

    app.logger.debug(f'Data yang ditangkap: {data_username} {data_password}')

    user = check_login(username=data_username, password=data_password)

    if user:
        return jsonify({'status': True, 'message': 'Login Berhasil'}), 200
    else:
        return jsonify({'status': False, 'message': 'Login Gagal !, Pastikan Username dan Password Benar'}), 200

@socketio.on('connect')
def handle_connect():
    global background_task_started
    print('Client connected')
    if not background_task_started:
        background_task_started = True
        threading.Thread(target=reset_rainfall_at_midnight, daemon=True).start()
        socketio.start_background_task(generate_sensor_data)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print('Program stopped')
    finally:
        GPIO.cleanup()
