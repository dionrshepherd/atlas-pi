import time
import serial
import re
import boto3
import sys
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import json

if len(sys.argv) != 2:
    print('No anchor id provided')
    sys.exit(1)

anchorId = sys.argv[1]
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('spark_iot_tag_distances')

def getFromStream(anchorId):
    try:
        response = table.get_item(
            Key={
                'anchors': anchorId
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        item = response['Item']
        data = item['data']
        print(data['dist'])

while True:
    getFromStream(anchorId)
    # time.sleep(0.2)