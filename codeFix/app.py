import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, request
from flask_socketio import SocketIO
import time
import random
import smbus2
import bme280
import RPi.GPIO as GPIO
from datetime import datetime
import sqlite3

app = Flask(__name__)
socketio = SocketIO(app, ping_timeout=60, ping_interval=25)

# Initialize sensors
bme280_address = 0x76
bus = smbus2.SMBus(1)
calibration_params = bme280.load_calibration_params(bus, bme280_address)

TRIG = 15
ECHO = 14
anemometer_pin = 17

count = 0
radius = 10.5  # cm
interval = 1  # seconds
background_task_started = False  # Initialize the background task flag

GPIO.setwarnings(False)  # Disable warnings
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(anemometer_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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
        distance = round(distance, 2)

        return distance
    except Exception as e:
        print(f'Error reading ultrasonic sensor: {e}')
        return None

def calculate_wind_speed(count, interval):
    rotations_per_sec = count / interval
    wind_speed_cm_per_sec = rotations_per_sec * 2 * 3.1416 * radius
    return wind_speed_cm_per_sec / 100

def count_pulse(channel):
    global count
    count += 1

GPIO.add_event_detect(anemometer_pin, GPIO.FALLING, callback=count_pulse)

def generate_sensor_data():
    global count
    while True:
        bme280_data = read_bme280_sensor()
        ultrasonic_distance = read_ultrasonic_sensor()

        count = 0
        time.sleep(interval)
        wind_speed = calculate_wind_speed(count, interval)

        if bme280_data and ultrasonic_distance is not None:
            combined_data = {
                'temperature_celsius': bme280_data['temperature_celsius'],
                'wave_height': ultrasonic_distance,
                'wind_speed': round(wind_speed, 2),
                'rain_intensity': round(random.uniform(1, 20), 2),
                'timestamp': int(time.time())
            }
            print('Combined Data:', combined_data, datetime.now())
            socketio.emit('update', combined_data)
        else:
            print('Error in sensor data')
            socketio.sleep(5)

@app.route("/")
def hello_world():
    return "hello world"

@app.route('/register', methods=['POST'])
def process_register():
    data_nama_lengkap   = request.form['nama_lengkap']
    data_username       = request.form['username']
    data_password       = request.form['password']
    add_user(nama_lengkap = data_nama_lengkap , username = data_username, password = data_password)
    if add_user:
        return jsonify({'status': True, 'message': 'Registrasi Berhasil'}), 201
    else:
        return jsonify({'status': False, 'message': 'Registrasi Gagal'}), 200

@app.route('/login', methods=['POST'])
def process_login():
    data_username = request.form['username']
    data_password = request.form['password']

    app.logger.debug(f'Data yang ditangkap: {data_username} {data_password}')

    user = check_login(username = data_username, password = data_password)

    if user:
        return jsonify({'status': True, 'message': 'Login Berhasil'}), 200
        #return jsonify(response), 200
    else:
        return jsonify({'status': False, 'message': 'Login Gagal !, Pastikan Username dan Password Benar'}), 200
        #return jsonify(response), 401


@socketio.on('connect')
def handle_connect():
    global background_task_started
    print('Client connected')
    if not background_task_started:
        background_task_started = True
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
