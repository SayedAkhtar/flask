import time
import serial

try:
    ser = serial.Serial(
    port='/dev/ttyUSB0',
     baudrate = 9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
    )
    counter=0
    while 1:

        x=ser.readline()
        print(x)
except Exception as e:
    print(f"No temperature Sensor {e}")
