import board
import digitalio
import adafruit_max31856
import time

# Create sensor object, communicating over the board's default SPI bus
spi = board.SPI()

# Allocate a CS pin for the first thermocouple and set the direction
cs1 = digitalio.DigitalInOut(board.D20)
cs1.direction = digitalio.Direction.OUTPUT

# Allocate a CS pin for the second thermocouple and set the direction
cs2 = digitalio.DigitalInOut(board.D21)
cs2.direction = digitalio.Direction.OUTPUT

# Create thermocouple objects with the above
thermocouple1 = adafruit_max31856.MAX31856(spi, cs1, thermocouple_type=adafruit_max31856.ThermocoupleType.K)
thermocouple2 = adafruit_max31856.MAX31856(spi, cs2)

def celsius_to_fahrenheit(celsius):
    return celsius * 9 / 5 + 32

# Measure the temperature from both thermocouples every second
while True:
    temperature1_c = thermocouple1.temperature
    temperature2_c = thermocouple2.temperature

    temperature1_f = celsius_to_fahrenheit(temperature1_c)
    temperature2_f = celsius_to_fahrenheit(temperature2_c)

    print(f"Temperature 1: {temperature1_c:.2f} °C / {temperature1_f:.2f} °F")
    print(f"Temperature 2: {temperature2_c:.2f} °C / {temperature2_f:.2f} °F")

    # Wait for one second before reading again
    time.sleep(1)
