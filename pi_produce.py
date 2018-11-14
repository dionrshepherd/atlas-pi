import time
import serial
import os
import sys
import boto3
import re
import logging
import uuid


def put_to_db(time_stamp, tag_id, distance, anchor_id):
    payload = {
        'ts': str(time_stamp),
        'dist': distance,
    }

    adapter.warning('payload for tag %s: %s', tag_id, payload)

    response = table.put_item(
        Item={
            'anchor': anchor_id,
            'tag': tag_id,
            'data': payload
        }
    )

    adapter.warning('Response: %s', response)
    print('tag: {}, distance: {}, ts: {}'.format(tag_id, distance, time_stamp))
    return


def get_tag_index(id_to_check, tags):
    for i, t in enumerate(tags):
        if t['id'] == id_to_check:
            return i, t
    return -1, {}


class CustomAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        # use my_context from kwargs or the default given on instantiation
        my_context = kwargs.pop('uid', self.extra['uid'])
        return '[%s] %s' % (my_context, msg), kwargs


anchorId = os.environ['ANCHOR_ID']
if len(anchorId) > 4:
    print('Anchor ID has not been set in .bashrc')
    sys.exit(1)
print('...Anchor ID: {}...'.format(anchorId))

filename = '/home/linaro/{}.log'.format(anchorId)
logging.basicConfig(filename=filename, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.WARNING)
logger = logging.getLogger(__name__)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('atlas_dev')

print('...Opening serial port...')
ser = serial.Serial(
    port='/dev/ttyACM0',
    baudrate=115200,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_ONE_POINT_FIVE,
    bytesize=serial.SEVENBITS,
)

print('...Sending les command...')
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
ser.readline()
ser.readline()
ser.flushInput()

# keep reading positions
print('...Reading positions...')
try:
    while True:
        adapter = CustomAdapter(logger, {'uid': str(uuid.uuid4())})
        # get position data and strip newlines
        raw_data = ser.readline().rstrip().decode()
        adapter.warning('Raw data: %s', raw_data)

        # remove uneeded data that is between [] and split based on a space
        positions = re.sub("[\(\[].*?[\)\]]", '', raw_data).split()
        adapter.warning('%d raw positions after regex: %s', len(positions), positions)

        # set timestamp arrays
        timeStamp = time.time()

        # split array of tags
        for pos in positions:
            current_data = pos.split('=')
            if len(current_data) == 2:
                if len(current_data[0]) == 4 and len(current_data[1]) > 0:
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
