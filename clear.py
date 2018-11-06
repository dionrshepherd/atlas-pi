import time
import serial
import sys


print('...Opening serial port...')
ser = serial.Serial(
    port='/dev/ttyACM0',
    baudrate=115200,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_ONE_POINT_FIVE,
    bytesize=serial.SEVENBITS,
    timeout=0.2
)

print('...Send command...')
ser.write(b'\r\r')
time.sleep(0.5)

# clear the buffer
ser.readline()
ser.readline()

print('...Resetting...')
ser.write(b'nmt\r')
ser.readline()
time.sleep(2)
ser.close()
sys.exit(0)
