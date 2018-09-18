import json
import time
import serial
import re
import boto3
import sys

if len(sys.argv) != 2:
    print('No anchor id provided')
    sys.exit(1)

anchorId = sys.argv[1]
streamName = 'spark_iot_stream'
kinesisClient = boto3.client('kinesis')

def putToStream(time, tags, dist, anchorId):
    payload = {
        'anchor': anchorId,
        'time': time,
        'tags': tags,
        'dist': dist
    }

    response = kinesisClient.put_record(
        StreamName=streamName,
        Data=json.dumps(payload),
        PartitionKey=anchorId
    )

ser = serial.Serial(
    port='/dev/tty.usbmodem1421',
    baudrate=115200,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_ONE_POINT_FIVE,
    bytesize=serial.SEVENBITS,
    timeout=0.1
)

# 2 newlines needed to access the command prompt
ser.write(b'\r\r')

# clear the buffer 
ser.readline()
ser.readline()

time.sleep(1)

# send command
ser.write(b'les\r')

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

# keep reading positions
while True:
    # get position data and strip newlines
    data = ser.readline().rstrip().decode()

    # remove uneeded data that is between [] and split based on a space
    positions = re.sub("[\(\[].*?[\)\]]", '', data).split()

    # set timestamp arrays
    timeStamp = time.time()
    tags = []
    dist = []

    # create the arrays needed to push to stream
    for pos in positions:
        data = pos.split('=')

        if len(data) < 2:
            print('Incorrect format')
            ser.close()
            sys.exit(0)

        tags.append(data[0])
        dist.append(data[1])

        # only print out the first 20 positions to check valid
        count += 1
        if count < 20:
            print(data)

    putToStream(timeStamp, tags, dist, anchorId)
        