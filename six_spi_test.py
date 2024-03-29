import spidev
import RPi.GPIO as GPIO
import time

# SPI settings
SPI_BUS = 10
SPI_DEVICE = 0

# GPIO pins for the CS lines of each thermocouple
CS_PINS = [6, 13, 19, 22, 10, 16]

# Initialize SPI
spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = 5000000  # Adjust as necessary for MAX31856

# Initialize GPIO for CS lines
GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
for pin in CS_PINS:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)  # CS active low, so initialize to HIGH

# Function to read temperature from a thermocouple
def read_temperature(cs_pin):
    # Activate the CS line for the current thermocouple
    GPIO.output(cs_pin, GPIO.LOW)
    
    # Send read command and read back the temperature data
    # This is just an example; you need to use the correct command for MAX31856
    response = spi.xfer2([0x00, 0x00, 0x00, 0x00])
    
    # Deactivate the CS line
    GPIO.output(cs_pin, GPIO.HIGH)

    # Process the response to get the temperature
    # This will depend on the specifics of the MAX31856 protocol
    temp = (response[1] << 8) | response[2]
    return temp / 100.0  # Example conversion, adjust according to actual data format

try:
    while True:
        for cs_pin in CS_PINS:
            temperature = read_temperature(cs_pin)
            print(f"Temperature (CS Pin {cs_pin}): {temperature} °C")

        time.sleep(1)

except KeyboardInterrupt:
    spi.close()
    GPIO.cleanup()
