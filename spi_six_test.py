import spidev
import time

# Function to initialize SPI device
def init_spi(bus, device):
    spi = spidev.SpiDev()
    spi.open(bus, device)
    spi.max_speed_hz = 5000000  # Adjust as necessary for MAX31856
    spi.mode = 0b01  # MAX31856 requires mode 1, according to its datasheet
    return spi

# Function to read temperature from a thermocouple
# This is a placeholder; you need to implement according to MAX31856 protocol
def read_temperature(spi):
    # Send read command and read back the temperature data
    # This is just an example; you need to use the correct command and process for MAX31856
    response = spi.xfer2([0x00, 0x00, 0x00, 0x00])
    temp = (response[1] << 8) | response[2]
    return temp / 100.0  # Example conversion, adjust according to actual data format

# Initialize SPI devices for each thermocouple
spi_devices = [
    init_spi(10, 0),  # Assuming bus 10, device 0 corresponds to /dev/spidev10.0
    init_spi(10, 1),  # Continue with the correct bus/device numbers
    init_spi(10, 2),
    init_spi(10, 3),
    init_spi(10, 4),
    init_spi(10, 5)
]

try:
    while True:
        for i, spi_device in enumerate(spi_devices):
            temperature = read_temperature(spi_device)
            print(f"Temperature {i+1}: {temperature} °C")
        
        time.sleep(1)

except KeyboardInterrupt:
    for spi_device in spi_devices:
        spi_device.close()
