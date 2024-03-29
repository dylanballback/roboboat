import board
import digitalio
import adafruit_max31856
import time

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

# Assuming the offset is 10 degrees Celsius for example
offset = 10.0

# Measure the temperature from all six thermocouples every second
while True:
    temperatures_line = ""
    for i, thermocouple in enumerate(thermocouples):
        temperature_c = thermocouple.temperature + offset  # Apply the offset here
        temperature_f = celsius_to_fahrenheit(temperature_c)
        temperatures_line += f"Temp {i+1}: {temperature_c:.2f} °C / {temperature_f:.2f} °F | "

    print(temperatures_line.strip('| '))
    # Wait for one second before reading again
    time.sleep(1)
