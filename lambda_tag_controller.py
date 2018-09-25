# This will be invocated everytime new data is pushed into DD
# It is responsible for collecting tags seen from which anchors
import boto3
import json

client = boto3.client('sns')


def lambda_handler(event, context):
    tags = []
    found_tags = []
    for record in event['Records']:

        anchor_id = record['dynamodb']['NewImage']['anchor']['S']
        tag_id = record['dynamodb']['NewImage']['tag']['S']

        anchor = {
            "id": anchor_id,
            "dist": float(record['dynamodb']['NewImage']['data']['M']['dist']['S']),
            "ts": record['dynamodb']['NewImage']['data']['M']['ts']['S']
        }

        try:
            t_id = found_tags.index(tag_id)
            tags[t_id]['anchors'].append(anchor)

        except ValueError:
            tag = {
                "id": tag_id,
                "anchors": [anchor]
            }
            tags.append(tag)
            found_tags.append(tag_id)

    num_records = len(event['Records'])
    for tag in tags:
        # basic sanity check if we get a spam on duplicates
        if len(tag['anchors']) > num_records:
            continue

        client.publish(
            TopicArn='arn:aws:sns:ap-southeast-2:430634712358:atlas-lambda',
            Message=json.dumps(tag)
        )
