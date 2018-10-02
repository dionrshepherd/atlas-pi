import time
import serial
import os
import sys
import boto3

anchorId = os.environ['ANCHOR_ID']
if len(anchorId) > 4:
    print('Anchor ID has not been set in .bashrc')
    sys.exit(1)
print('...Anchor ID: ' + anchorId + '...')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('atlas_dev')


def put_to_db(time_stamp, tag_id, distance, anchor_id):
    payload = {
        'ts': str(time_stamp),
        'dist': distance,
    }

    table.put_item(
        Item={
            'anchor': anchor_id,
            'tag': tag_id,
            'data': payload
        }
    )
    return


print('...Opening serial port...')
ser = serial.Serial(
    port='/dev/ttyACM0',
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
        start_time = time.time()
        timeStamp = time.time()
        data = ser.read()
        while data != b' ':
            data = ser.read()

        tagId = ser.read(6)

        if int(tagId[0]) == 13:
            data = ser.read(21)
            tagId = tagId[2:6]
        else:
            data = ser.read(19)
            tagId = tagId[0:4]

        # print distances to debug
        # print(data[-4:])

        put_to_db(timeStamp, tagId.decode(), data[-4:].decode(), anchorId)

        print(str(time.time() - start_time))
        start_time = time.time()

except KeyboardInterrupt:
    print('...Closing...')
    ser.write(b'\r\r')
    ser.readline()
    ser.write(b'quit\r')
    ser.readline()
    time.sleep(2)
    ser.close()
    sys.exit(0)
