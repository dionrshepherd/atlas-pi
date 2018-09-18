import time
import serial
import re
import boto3
import sys
import os

print("starting")
anchorId = os.environ['ANCHOR_ID']
if len(anchorId) > 4:
    print('Anchor ID has not been set in .bashrc')
    sys.exit(1)
anchorId = '99A4'
print('anchorId: ' + anchorId)
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

print("Opening serial")
ser = serial.Serial(
    # port='/dev/tty.usbmodem1421',
    port='/dev/ttyACM0',
    baudrate=115200,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_ONE_POINT_FIVE,
    bytesize=serial.SEVENBITS,
    timeout=0.1
)

print("Cleaning up some data")
# 2 newlines needed to access the command prompt
ser.write(b'\r\r')

# clear the buffer 
ser.readline()
ser.readline()

print("sleepn. How bout a nap")

time.sleep(1)

print("writing command bits")
# send command
ser.write(b'les\r')

print("re-re-reclearing buffer")
# clear the buffer 
ser.readline().decode()
ser.readline().decode()
ser.readline().decode()

# For some reason this doesnt work everytime,
# not sure if its an issue with the serial library
# or the Decawave library.
# With a tag close to the anchor you are starting
# check to see if positional data is returned or
# if there is some garbled positional data or no 
# positional data. if so then kill and run again
count = 0

print("HERE WE GO (in mario voice)")
# keep reading positions
while True:
    # get position data and strip newlines
    #data = ser.read(128)#line()#.rstrip().decode()
    line = ""

    data = ser.read()
    while (data != b'\r'):
        line += data.decode()
        data = ser.read()

    data = ser.read()
    if (data == b'\n'):
        print(line)

    # while (data != b'\r'):
    #     bufr += data.decode()
    #     data = ser.read()

    # print(bufr)

    # remove uneeded data that is between [] and split based on a space
    #positions = re.sub("[\(\[].*?[\)\]]", '', data).split()

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
        
