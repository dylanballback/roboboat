import board
import digitalio
import adafruit_max31856

# Create sensor object, communicating over the board's default SPI bus
spi = board.SPI()

# allocate a CS pin and set the direction
cs = digitalio.DigitalInOut(board.D20)
cs.direction = digitalio.Direction.OUTPUT

# create a thermocouple object with the above
thermocouple = adafruit_max31856.MAX31856(spi, cs)

# measure the temperature! (takes approx 160ms)
print(thermocouple.temperature)

# alternative (non-blocking) way to get temperature
thermocouple.initiate_one_shot_measurement()
# <perform other tasks>
# now wait for measurement to complete
while thermocouple.oneshot_pending:
  pass
print(thermocouple.unpack_temperature())
