
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
    VSensor1 REAL,
    Voltage1 REAL,
    VCurrentsensor1 REAL,
    Current1 REAL,
    ReadingTime REAL,  -- Updated column type to REAL for milliseconds
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
db_connection.commit()

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().strip()
            try:
                # Attempt to decode as UTF-8, replace errors to avoid UnicodeDecodeError
                decoded_line = line.decode('utf-8', 'replace')
                parts = decoded_line.split(',')
                if len(parts) == 9:  # Ensure there are nine parts per line now
                    try:
                        # Convert parts to float and unpack
                        VSensor, Voltage, VCurrentsensor, Current, VSensor1, Voltage1, VCurrentsensor1, Current1, ReadingTime = map(float, parts)

                        # Insert the data into the SQLite database
                        cursor.execute('''
                        INSERT INTO sensor_data (VSensor, Voltage, VCurrentsensor, Current, VSensor1, Voltage1, VCurrentsensor1, Current1, ReadingTime)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (VSensor, Voltage, VCurrentsensor, Current, VSensor1, Voltage1, VCurrentsensor1, Current1, ReadingTime))
                        db_connection.commit()

                        print(f"Inserted: VSensor={VSensor}, Voltage={Voltage}, VCurrentsensor={VCurrentsensor}, Current={Current}, VSensor1={VSensor1}, Voltage1={Voltage1}, VCurrentsensor1={VCurrentsensor1}, Current1={Current1}, ReadingTime>
                    except ValueError:
                        # Skip the line if conversion to float fails
                        print(f"Invalid data skipped: {decoded_line}")
            except UnicodeDecodeError:
                # Handle lines that still cannot be decoded properly
                print(f"Line with invalid encoding skipped: {line}")


except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    ser.close()
    db_connection.close()
    print("Serial port and database connection closed")

