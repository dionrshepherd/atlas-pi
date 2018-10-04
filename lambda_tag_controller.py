# This will be invocated everytime new data is pushed into DD
# It is responsible for collecting tags seen from which anchors
import boto3
import json

client = boto3.client('sns')


def lambda_handler(event, context):
    tags = []
    found_tags = []
    for record in event['Records']:
        # in case we get an string that cannot be parsed
        try:
            dist = float(record['dynamodb']['NewImage']['data']['M']['dist']['S'])
        except ValueError or KeyError:
            continue

        anchor_id = record['dynamodb']['NewImage']['anchor']['S']
        tag_id = record['dynamodb']['NewImage']['tag']['S']

        # ignore negative numbers, 0 distances and the defined primary tag
        # primary tag must always be on and not in use, it will be attached
        # to the primary origin anchor
        if (dist > 0.00 and anchor_id != 'primary'):
            anchor = {
                "id": anchor_id,
                "dist": dist,
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
        else:
            continue

    num_records = len(event['Records'])
    for tag in tags:
        # basic sanity check if we get a spam on duplicates
        if len(tag['anchors']) > num_records:
            continue

        client.publish(
            TopicArn='arn:aws:sns:ap-southeast-2:430634712358:atlas-lambda',
            Message=json.dumps(tag)
        )
