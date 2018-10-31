import time
import serial
import os
import sys
import boto3
import re


def put_to_db(time_stamp, tag_id, distance, anchor_id):
    print('tag: {}, distance: {}, ts: {}'.format(tag_id, distance, time_stamp))
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
previous_tic_tags = []
current_tags = []


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

        # loop variables
        max_dist = 0
        index = 0
        idx_of_max_dist = -1
        idx_of_previous_value = -1
        tag_data_of_previous = {}

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
                    previous_data = get_tag_index(current_data[0], previous_tic_tags)
                    if previous_data[0] > -1:
                        dist_diff = abs(float(current_data[1]) - float(previous_data[1]["dist"]))
                        time_diff = abs(float(timeStamp) - float(previous_data[1]["ts"]))
                        if dist_diff > 1.5 and time_diff < 0.8:
                            put_to_db(previous_data[1]["ts"], previous_data[1]["id"], previous_data[1]["dist"], anchorId)
                        else:
                            previous_tic_tags[previous_data[0]] = seen_tag
                            put_to_db(timeStamp, current_data[0], current_data[1], anchorId)
                    else:
                        previous_tic_tags.append(seen_tag)
                        put_to_db(timeStamp, current_data[0], current_data[1], anchorId)
        #             if previous_data[0] > -1:
        #                 dist_diff = abs(float(current_data[1]) - float(previous_data[1]["dist"]))
        #                 previous_tic_tags[previous_data[0]] = seen_tag
        #
        #                 if dist_diff > max_dist:
        #                     max_dist = dist_diff
        #                     idx_of_max_dist = index
        #                     idx_of_previous_value = previous_data[0]
        #                     tag_data_of_previous = previous_data[1]
        #             else:
        #                 previous_tic_tags.append(seen_tag)
        #
        #             current_tags.append(seen_tag)
        #             index = index + 1
        #
        # if idx_of_max_dist > -1 and idx_of_previous_value > -1 and current_tags > 4:
        #     del current_tags[idx_of_max_dist]
        #     previous_tic_tags[idx_of_previous_value] = tag_data_of_previous
        #
        # for t in current_tags:
        #     put_to_db(t["ts"], t["id"], t["dist"], anchorId)


except KeyboardInterrupt:
    print('...Closing...')
    ser.write(b'\r\r')
    ser.readline()
    ser.write(b'quit\r')
    ser.readline()
    time.sleep(2)
    ser.close()
    sys.exit(0)
