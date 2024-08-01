import RPi.GPIO as GPIO
import time
import statistics

# Set GPIO mode
GPIO.setmode(GPIO.BCM)

# Set pin for anemometer
anemometer_pin = 17
GPIO.setup(anemometer_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Variables to store wind speed
count = 0
radius = 9.0  # Radius of anemometer in cm
interval = 1  # Measurement interval in seconds
calibration_factor = 1.0  # Initial calibration factor

# Wind speed in m/s
def calculate_wind_speed(count, interval, calibration_factor):
    # Assuming each pulse corresponds to one rotation
    rotations_per_sec = count / interval
    # Calculate wind speed (assuming 1 rotation = 2*pi*radius distance)
    wind_speed_cm_per_sec = rotations_per_sec * 2 * 3.1416 * radius
    wind_speed_m_per_sec = wind_speed_cm_per_sec / 100
    # Apply calibration factor
    calibrated_wind_speed = wind_speed_m_per_sec * calibration_factor
    return calibrated_wind_speed

# Callback function for counting pulses
def count_pulse(channel):
    global count
    count += 1

# Add event detection for the anemometer pin
GPIO.add_event_detect(anemometer_pin, GPIO.FALLING, callback=count_pulse)

# Main loop to measure wind speed for calibration
try:
    calibration_data = []
    while True:
        count = 0
        time.sleep(interval)
        wind_speed = calculate_wind_speed(count, interval, calibration_factor)
        print(f"Measured Wind Speed: {wind_speed:.2f} m/s")

        # Here, you would compare the measured wind speed with the reference anemometer
        # For the purpose of this example, we'll assume a reference wind speed of 3.4 m/s
        reference_wind_speed = 3.4  # Replace this with the actual reference value
        calibration_data.append((wind_speed, reference_wind_speed))

        # Collect enough data for calibration (e.g., 30 samples)
        if len(calibration_data) >= 30:
            break

    # Calculate calibration factor
    measured_speeds, reference_speeds = zip(*calibration_data)
    calibration_factor = statistics.mean(reference_speeds) / statistics.mean(measured_speeds)
    print(f"Calibration Factor: {calibration_factor:.2f}")

    # Update the calculation with the new calibration factor
    while True:
        count = 0
        time.sleep(interval)
        wind_speed = calculate_wind_speed(count, interval, calibration_factor)
        print(f"Calibrated Wind Speed: {wind_speed:.2f} m/s")

except KeyboardInterrupt:
    GPIO.cleanup()
