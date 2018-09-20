import time
import boto3
import sys
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import json
import math

if len(sys.argv) != 4:
    print('Anchor and Tag ID need to be set')
    sys.exit(1)

anchorId1 = sys.argv[1]
anchorId2 = sys.argv[2]
tagId = sys.argv[3]
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('atlas_dev')

def getFromStream(anchorId, tagId):
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
    getFromStream(anchorId1, tagId)
    # tagFromA1 = getFromStream(anchorId1, tagId)
    # tagFromA2 = getFromStream(anchorId2, tagId)

    # # this is the math i need 0.75m out
    # dist1 = math.sqrt((tagFromA1 * tagFromA1) - 0.5625)
    # dist2 = math.sqrt((tagFromA2 * tagFromA2) - 0.5625)

    # # print(dist1)
    # # print(dist2)

    # mid = abs(dist1 - dist2) / 2
    # # print(mid)
    # print(tagId + ':' + str(tagFromA1 + mid))