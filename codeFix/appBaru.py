import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
import sqlite3
import RPi.GPIO as GPIO
import time
from datetime import datetime
import smbus2
import bme280

app = Flask(__name__)
socketio = SocketIO(app)

# Setup GPIO pins
pin_interrupt_hujan = 27
pin_pulse_angin = 22
pin_trig_gelombang = 15
pin_echo_gelombang = 14

GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_interrupt_hujan, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_pulse_angin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_trig_gelombang, GPIO.OUT)
GPIO.setup(pin_echo_gelombang, GPIO.IN)

# BME280 sensor address (default address)
address_bme280 = 0x76

# Initialize I2C bus
bus = smbus2.SMBus(1)
calibration_params = bme280.load_calibration_params(bus, address_bme280)

# Initialize variables for rainfall measurement
jumlah_tip = 0
curah_hujan = 0.00
milimeter_per_tip = 0.70
flag_hujan = False

# Initialize variables for wind speed measurement
rpmcount = 0
timemeasure = 10
threshold = 1.5

# Interrupt callbacks
def hitung_curah_hujan(channel):
    global flag_hujan
    flag_hujan = True

def rpm_anemometer(channel):
    global rpmcount
    rpmcount += 1

# Attach interrupts
GPIO.add_event_detect(pin_interrupt_hujan, GPIO.FALLING, callback=hitung_curah_hujan, bouncetime=500)
GPIO.add_event_detect(pin_pulse_angin, GPIO.RISING, callback=rpm_anemometer, bouncetime=5)

def calculate_wind_speed():
    rotasi_per_detik = rpmcount / timemeasure
    kecepatan_meter_per_detik = max(0, (-0.0181 * (rotasi_per_detik ** 2)) + (1.3859 * rotasi_per_detik) + 1.4055)
    if kecepatan_meter_per_detik < threshold:
        kecepatan_meter_per_detik = 0.0
    return kecepatan_meter_per_detik

def measure_wave_height():
    GPIO.output(pin_trig_gelombang, False)
    time.sleep(2)
    GPIO.output(pin_trig_gelombang, True)
    time.sleep(0.00001)
    GPIO.output(pin_trig_gelombang, False)
    while GPIO.input(pin_echo_gelombang) == 0:
        pulse_start = time.time()
    while GPIO.input(pin_echo_gelombang) == 1:
        pulse_end = time.time()
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 34300 / 2
    distance = round(distance, 1)
    return distance

def measure_temperature_and_pressure():
    data = bme280.sample(bus, address_bme280, calibration_params)
    temperature_celsius = data.temperature
    pressure = data.pressure
    humidity = data.humidity
    return temperature_celsius, pressure, humidity

#@app.route('/')
#def index():
#    return render_template('index.html')

def update_sensors():
    global curah_hujan, flag_hujan, rpmcount

    while True:
        # Measure wind speed
        time.sleep(timemeasure)
        GPIO.remove_event_detect(pin_pulse_angin)
        wind_speed = calculate_wind_speed()
        rpmcount = 0
        GPIO.add_event_detect(pin_pulse_angin, GPIO.RISING, callback=rpm_anemometer, bouncetime=5)

        # Measure wave height
        ombak = measure_wave_height()

        # Measure temperature and pressure
        temperature_celsius, pressure, humidity = measure_temperature_and_pressure()

        # Measure rainfall
        if flag_hujan:
            curah_hujan += milimeter_per_tip
            flag_hujan = False

        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        #socketio.emit('update', {
	 #   'wave_height': ombak,
          #  #'wave_height': wave_height,
           # 'temperature_celsius': temperature_celsius,
            #'wind_speed': wind_speed,
            #'rain_intensity': curah_hujan,
            #'timestamp': timestamp
        #})

        time.sleep(1)

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
    print("Client connected")
    emit('update', {
        #'wave_height': measure_wave_height(),
        #'temperature_celsius': measure_temperature_and_pressure()[0],
        #'wind_speed': calculate_wind_speed(),
        #'rain_intensity': curah_hujan,
        #'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
 	'wave_height': ombak,
    	'temperature_celsius': temperature_celsius,
    	'wind_speed': wind_speed,
    	'rain_intensity': curah_hujan,
    	'timestamp': timestamp
    })

if __name__ == '__main__':
    try:
        socketio.start_background_task(update_sensors)
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        GPIO.cleanup()
