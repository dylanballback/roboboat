
import board
import digitalio
import adafruit_max31856
import time
import sqlite3

# Create sensor object, communicating over the board's default SPI bus
spi = board.SPI()

# Allocate CS pins for all six thermocouples and set the direction
cs_pins = [board.D13, board.D19, board.D26, board.D16, board.D20, board.D21]
cs_objects = [digitalio.DigitalInOut(pin) for pin in cs_pins]
for cs in cs_objects:
    cs.direction = digitalio.Direction.OUTPUT

# Create thermocouple objects with the above
thermocouples = [adafruit_max31856.MAX31856(spi, cs) for cs in cs_objects]

def celsius_to_fahrenheit(celsius):
    return celsius * 9 / 5 + 32

# Initialize the database and create the table
db_connection = sqlite3.connect('temperature_data.db')
cursor = db_connection.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS temperatures (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        sensor INTEGER,
        temp_c REAL,
        temp_f REAL
    )
''')
db_connection.commit()

# Assuming the offset is 10 degrees Celsius for example
offset = 10.0

try:
    print("Starting temperature monitoring...")
    while True:
        temperatures_line = ""
        for i, thermocouple in enumerate(thermocouples):
            try:
                # print(f"Reading temperature from sensor {i+1}")
                temperature_c = thermocouple.temperature + offset  # Apply the offset here
                temperature_f = celsius_to_fahrenheit(temperature_c)

                # Insert the temperature data into the database
                cursor.execute('''
                    INSERT INTO temperatures (sensor, temp_c, temp_f)
                    VALUES (?, ?, ?)
                ''', (i+1, temperature_c, temperature_f))
                db_connection.commit()

                temperatures_line += f"Sensor {i+1}: {temperature_c:.2f} °C / {temperature_f:.2f} °F | "
            except Exception as e:
                print(f"Error reading temperature from sensor {i+1}: {e}")

        print(temperatures_line.strip("| "))
        # Wait for one second before reading again
        time.sleep(.2)
except KeyboardInterrupt:
    print("Program interrupted. Exiting gracefully.")
finally:
    db_connection.close()
    print("Database connection closed.")
