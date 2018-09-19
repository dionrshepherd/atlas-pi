import time
import serial
import re
import boto3
import sys
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import json

anchorId = '99A4'
tagId = 'C52A'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('atlas_dev')

def getFromStream(anchorId):
    try:
        response = table.get_item(
            Key={
                'anchor': anchorId,
                'tag': tagId
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