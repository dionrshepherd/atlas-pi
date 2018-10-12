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

        if tag_id in str(found_tags):
            continue
        else:
            response = table.scan(
                FilterExpression=Attr('tag').eq(tag_id)
            )
            anchors = response['Items']
            for a in anchors:
                if a['anchor'] == '99A4':
                    a11 = float(a['data']['dist'])
                    a12 = a['data']['ts']
                if a['anchor'] == 'CBB5':
                    a21 = float(a['data']['dist'])
                    a22 = a['data']['ts']
                if a['anchor'] == '8986':
                    a31 = float(a['data']['dist'])
                    a32 = a['data']['ts']
                if a['anchor'] == '9895':
                    a41 = float(a['data']['dist'])
                    a42 = a['data']['ts']

            tag = {
                "id": tag_id,
                "anchors": [
                    {
                        "id": '99A4',
                        "dist": a11,
                        "ts": a12
                    },
                    {
                        "id": 'CBB5',
                        "dist": a21,
                        "ts": a22
                    },
                    {
                        "id": '8986',
                        "dist": a31,
                        "ts": a32
                    },
                    {
                        "id": '9895',
                        "dist": a41,
                        "ts": a42
                    }
                ]
            }
            print(tag)
            found_tags.append(tag_id)
            sns_client.publish(
                TopicArn='arn:aws:sns:ap-southeast-2:430634712358:atlas-lambda',
                Message=json.dumps(tag)
            )
