import boto3
from boto3.dynamodb.conditions import Attr
import uuid
import json
import time


db_resource = boto3.resource('dynamodb')
table = db_resource.Table('atlas_dev_v2')
sns_client = boto3.client('sns', region_name='ap-southeast-2')
iot_data_client = boto3.client('iot-data', region_name='ap-southeast-2')


def lambda_handler(event, context):
    uid = str(uuid.uuid4())
    found_tags = []
    logger = {}
    logger['uuid'] = uid
    logger['level'] = ''
    logger['message'] = ''

    for record in event['Records']: # might remove this first call, just get the state of the db
        tag_id = record['dynamodb']['Keys']['id']['S']

        if len(tag_id) == 4:
            if tag_id in str(found_tags):
                continue
            else:
                response = table.scan(
                    FilterExpression=Attr('id').eq(tag_id)
                )

                item = response['Items'][0] # is an array, should only return one, so take the first
                logger['tagId'] = tag_id

                try:
                    x = float(item['payload']['x'])
                    y = float(item['payload']['y'])
                    z = float(item['payload']['z'])
                except(ValueError):
                    logger['response'] = 'ERROR'
                    logger['message'] = 'Number Value Error:{}'.format(item)
                    print(json.dumps(logger))
                    continue

                tag = {
                    "tag": 'C52A',
                    "x": x,
                    "y": y,
                    "z": z,
                    "ts": str(time.time())
                }

                found_tags.append(tag_id)

                iot_data_client.publish(
                    topic='atlasDevTagCoords',
                    payload=json.dumps(tag)
                )

                sns_client.publish(
                    TopicArn='arn:aws:sns:ap-southeast-2:430634712358:atlas-proximity-event',
                    Message=json.dumps(tag)
                )

                logger['response'] = 'SUCCESS'
                logger['message'] = ''
                print(json.dumps(logger))
        else:
            continue