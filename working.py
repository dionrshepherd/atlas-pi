import time
import serial
import boto3
import sys
import os

anchorId = '99A4'
print('...Anchor ID: ' + anchorId + '...')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('atlas_dev')

def putToDB(timeStamp, tagId, distance, anchorId):
    payload = {
        'ts': str(timeStamp),
        'dist': distance,
    }

    response = table.put_item(
        Item={
            'anchor': anchorId,
            'tag': tagId,
            'data': payload
        }
    )

print('...Opening serial port...')
ser = serial.Serial(
    port='/dev/tty.usbmodem1421',
    baudrate=115200,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_ONE_POINT_FIVE,
    bytesize=serial.SEVENBITS,
)

print('...Sending les command...')
# 2 newlines needed to access the command prompt
ser.write(b'\r\r')
time.sleep(0.5)

# clear the buffer 
ser.readline()
ser.readline()

# send command
ser.write(b'les\r')
time.sleep(0.5)

# clear the buffer 
ser.readline()
time.sleep(2)
ser.flushInput()

# keep reading positions
print('...Reading positions...')
try:
    while True:
        timeStamp = time.time()
        data = ser.read()
        while (data != b' '):
            data = ser.read()

        line = ser.read(27)
        tagId = line[2:6].decode()
        distance = line[23:27].decode()

        # debugging
        print(line)

        putToDB(timeStamp, tagId, distance, anchorId)

        # flush the buffers after send so we get the most up to date information
        ser.flushOutput()

except KeyboardInterrupt:
    print('...Closing...')
    ser.write(b'\r\r')
    ser.readline()
    ser.write(b'quit\r')
    ser.readline()
    time.sleep(2)
    ser.close()
    sys.exit(0)