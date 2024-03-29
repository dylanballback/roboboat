import asyncio
import serial
import sqlite3
import board
import digitalio
import adafruit_max31856

# Set up the serial port
serial_port = '/dev/ttyUSB0'
baud_rate = 9600
ser = serial.Serial(serial_port, baud_rate, timeout=1)

# Set up the SPI bus and thermocouples
spi = board.SPI()
cs_pins = [board.D13, board.D19, board.D26, board.D16, board.D20, board.D21]
cs_objects = [digitalio.DigitalInOut(pin) for pin in cs_pins]
for cs in cs_objects:
    cs.direction = digitalio.Direction.OUTPUT
thermocouples = [adafruit_max31856.MAX31856(spi, cs) for cs in cs_objects]

# Set up the SQLite database
db_connection = sqlite3.connect('sensor_data.db')
cursor = db_connection.cursor()

# Table for the sensor data
cursor.execute('''
CREATE TABLE IF NOT EXISTS sensor_data (
    VSensor REAL,
    Voltage REAL,
    VCurrentsensor REAL,
    Current REAL,
    ReadingTime REAL,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
db_connection.commit()

# Table for the thermocouple data
cursor.execute('''
CREATE TABLE IF NOT EXISTS thermocouple_data (
    Thermocouple1 REAL,
    Thermocouple2 REAL,
    Thermocouple3 REAL,
    Thermocouple4 REAL,
    Thermocouple5 REAL,
    Thermocouple6 REAL,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
db_connection.commit()

def celsius_to_fahrenheit(celsius):
    return celsius * 9 / 5 + 32

async def read_serial():
    while True:
        if ser.in_waiting > 0:
            raw_line = ser.readline().strip()
            parts = raw_line.split(b',')
            if len(parts) == 5 and all(part.replace(b'.', b'').replace(b'-', b'').isdigit() for part in parts):
                try:
                    VSensor, Voltage, VCurrentsensor, Current, ReadingTime = map(float, parts)
                    cursor.execute('''
                    INSERT INTO sensor_data (VSensor, Voltage, VCurrentsensor, Current, ReadingTime)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (VSensor, Voltage, VCurrentsensor, Current, ReadingTime))
                    db_connection.commit()
                    print(f"Inserted sensor data: VSensor={VSensor}, Voltage={Voltage}, VCurrentsensor={VCurrentsensor}, Current={Current}, ReadingTime={ReadingTime}")
                except ValueError:
                    print(f"Could not convert data to float: {raw_line}")
            else:
                print(f"Non-numeric data or incorrect format received: {raw_line}")
        await asyncio.sleep(0)  # Allow other tasks to run

async def read_thermocouples():
    while True:
        temperatures = []
        for thermocouple in thermocouples:
            temperature_c = thermocouple.temperature + 10.0  # Example offset
            temperatures.append(temperature_c)

        cursor.execute('''
        INSERT INTO thermocouple_data (Thermocouple1, Thermocouple2, Thermocouple3, Thermocouple4, Thermocouple5, Thermocouple6)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', temperatures)
        db_connection.commit()

        print(f"Inserted thermocouple temperatures: {temperatures}")

        await asyncio.sleep(0)  # Allow other tasks to run

async def main():
    await asyncio.gather(
        read_serial(),
        read_thermocouples()
    )

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    ser.close()
    db_connection.close()
    print("Serial port and database connection closed")
