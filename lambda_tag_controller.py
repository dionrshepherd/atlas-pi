# This will be invocated everytime new data is pushed into DD
# It is responsible for collecting tags seen from which anchors
import boto3
import json
from boto3.dynamodb.conditions import Attr

sns_client = boto3.client('sns')
db_resource = boto3.resource('dynamodb')
table = db_resource.Table('atlas_dev')


def lambda_handler(event, context):
    found_tags = []

    for record in event['Records']:
        tag_id = record['dynamodb']['Keys']['tag']['S']

        if tag_id == 'CC18':
            print('Skipping Primary Tag')
            continue

        if tag_id in str(found_tags):
            continue
        else:
            response = table.scan(
                FilterExpression=Attr('tag').eq(tag_id)
            )

            anchors = []
            items = response['Items']

            for i in items:
                try:
                    item_dist = float(i['data']['dist'])
                except(ValueError):
                    print("Value error: " + i['data']['dist'])
                    continue
                anchors.append({
                    "id": i['anchor'],
                    "dist": item_dist,
                    "ts": float(i['data']['ts'])
                })
            tag = {
                "id": tag_id,
                "anchors": anchors
            }
            # debug
            print(tag)

            found_tags.append(tag_id)
            sns_client.publish(
                TopicArn='arn:aws:sns:ap-southeast-2:430634712358:atlas-lambda',
                Message=json.dumps(tag)
            )
