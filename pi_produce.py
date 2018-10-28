import time
import serial
import os
import sys
import boto3
import re


def put_to_db(time_stamp, tag_id, distance, anchor_id):
    print('tag: {}, distance: {}, ts: {}').format(tag_id, distance, time_stamp)
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


def get_tag_index(id, tags):
    for i, t in enumerate(tags):
        if t['id'] == id:
            return i, t
    return -1, {}


anchorId = os.environ['ANCHOR_ID']
if len(anchorId) > 4:
    print('Anchor ID has not been set in .bashrc')
    sys.exit(1)
print('...Anchor ID: ' + anchorId + '...')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('atlas_dev')
init_tag = 'CC18'
seen_tags = []

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
        # get position data and strip newlines
        current_data = ser.readline().rstrip().decode()

        # remove uneeded data that is between [] and split based on a space
        positions = re.sub("[\(\[].*?[\)\]]", '', current_data).split()

        # set timestamp arrays
        timeStamp = time.time()

        # split array of tags
        for pos in positions:
            current_data = pos.split('=')
            if len(current_data) == 2:
                if current_data[0] != init_tag and len(current_data[0]) == 4:
                    seen_tag = {
                        "id": current_data[0],
                        "dist": current_data[1],
                        "ts": timeStamp
                    }
                    previous_data = get_tag_index(current_data[0], seen_tags)
                    if previous_data[0] > -1:
                        dist_diff = abs(float(current_data[1]) - float(previous_data[1]["dist"]))
                        time_diff = abs(float(timeStamp) - float(previous_data[1]["ts"]))
                        if dist_diff > 2 and time_diff < 1:
                            put_to_db(previous_data[1]["ts"], previous_data[1]["id"], previous_data[1]["dist"], anchorId)
                        else:
                            seen_tags[previous_data[0]] = seen_tag
                            put_to_db(timeStamp, current_data[0], current_data[1], anchorId)
                    else:
                        seen_tags.append(seen_tag)
                        put_to_db(timeStamp, current_data[0], current_data[1], anchorId)


except KeyboardInterrupt:
    print('...Closing...')
    ser.write(b'\r\r')
    ser.readline()
    ser.write(b'quit\r')
    ser.readline()
    time.sleep(2)
    ser.close()
    sys.exit(0)
