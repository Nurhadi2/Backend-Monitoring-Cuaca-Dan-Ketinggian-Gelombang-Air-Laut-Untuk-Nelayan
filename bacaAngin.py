import RPi.GPIO as GPIO
import time

# Set GPIO mode
GPIO.setmode(GPIO.BCM)

# Set pin for anemometer
anemometer_pin = 17
GPIO.setup(anemometer_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Variables to store wind speed
count = 0
radius = 10.5  # Radius of anemometer in cm
interval = 5  # Measurement interval in seconds
#interval = 1


# Wind speed in m/s
def calculate_wind_speed(count, interval):
    # Assuming each pulse corresponds to one rotation
    rotations_per_sec = count / interval
    # Calculate wind speed (assuming 1 rotation = 2*pi*radius distance)
    wind_speed_cm_per_sec = rotations_per_sec * 2 * 3.1416 * radius
    wind_speed_m_per_sec = wind_speed_cm_per_sec / 100
    return wind_speed_m_per_sec

# Callback function for counting pulses
def count_pulse(channel):
    global count
    count += 1

# Add event detection for the anemometer pin
GPIO.add_event_detect(anemometer_pin, GPIO.FALLING, callback=count_pulse)

# Main loop to measure wind speed
try:
    while True:
        count = 0
        time.sleep(interval)
        wind_speed = calculate_wind_speed(count, interval)
        print(f"Wind Speed: {wind_speed:.2f} m/s")

except KeyboardInterrupt:
    GPIO.cleanup()
