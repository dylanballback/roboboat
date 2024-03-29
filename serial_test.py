import serial
import time

# Replace 'COM3' with the serial port your Arduino is connected to
# For example, on macOS it might be something like '/dev/tty.usbmodem14101'
serial_port = '/dev/ttyUSB0'
baud_rate = 9600  # In Arduino, Serial.begin(baud_rate)

try:
    ser = serial.Serial(serial_port, baud_rate, timeout=1)
    time.sleep(2)  # wait for the serial connection to initialize

    while True:
        if ser.in_waiting > 0:
            line = ser.readline()
            print(line)
except serial.SerialException as e:
    print("Error opening serial port: {}".format(e))
except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial port closed")
