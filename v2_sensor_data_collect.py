import serial
import time
import sqlite3

# Set up the serial port
serial_port = '/dev/ttyUSB0'
baud_rate = 9600
ser = serial.Serial(serial_port, baud_rate, timeout=1)
time.sleep(2)  # wait for the serial connection to initialize

# Set up the SQLite database
db_connection = sqlite3.connect('sensor_data.db')
cursor = db_connection.cursor()
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

try:
    while True:
        if ser.in_waiting > 0:
            raw_line = ser.readline().strip()
            parts = raw_line.split(b',')  # Split using byte literals
            if len(parts) == 5:
                # Decode each part individually, handling errors
                try:
                    VSensor = float(parts[0].decode('utf-8'))
                    Voltage = float(parts[1].decode('utf-8'))
                    VCurrentsensor = float(parts[2].decode('utf-8'))
                    Current = float(parts[3].decode('utf-8'))
                    ReadingTime = float(parts[4].decode('utf-8'))

                    # Insert the data into the SQLite database
                    cursor.execute('''
                    INSERT INTO sensor_data (VSensor, Voltage, VCurrentsensor, Current, ReadingTime)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (VSensor, Voltage, VCurrentsensor, Current, ReadingTime))
                    db_connection.commit()

                    print(f"Inserted: VSensor={VSensor}, Voltage={Voltage}, VCurrentsensor={VCurrentsensor}, Current={Current}, ReadingTime={ReadingTime}ms")
                except UnicodeDecodeError:
                    print(f"Could not decode line: {raw_line}")
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    ser.close()
    db_connection.close()
    print("Serial port and database connection closed")
