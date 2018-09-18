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
table = dynamodb.Table('spark_iot_tag_distances')

def putToDB(time, tags, dist, anchorId):
    payload = {
        'time': str(time),
        'tags': tags,
        'dist': dist
    }

    response = table.put_item(
        Item={
            'anchors': anchorId,
            'data': payload
        }
    )

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
        data = ser.read()
        while (data != b' '):
            data = ser.read()

        bLine = ser.read(27)
        sLine = bLine[2:6].decode()
        sLine += bLine[22:27].decode()

        print(sLine)

except KeyboardInterrupt:
    print('...Closing...')
    ser.write(b'\r\r')
    ser.readline()
    ser.write(b'quit\r')
    ser.readline()
    time.sleep(2)
    ser.close()
    sys.exit(0)

    # set timestamp arrays
    #timeStamp = time.time()
    #tags = []
    #dist = []

    # create the arrays needed to push to stream
    #for pos in positions:
    #    data = pos.split('=')

     #   if len(data) < 2:
      #      print('Incorrect format')
       #     ser.close()
        #    sys.exit(0)

       # tags.append(data[0])
       # dist.append(data[1])
        # print out for debugging purposes
    #print(data, end='',flush=True)
    #print(timeStamp)

    #putToDB(timeStamp, tags, dist, anchorId)

    # flush the buffers after send so we get the most up to date information
    #ser.flushOutput()
        
