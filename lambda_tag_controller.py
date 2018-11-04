# This will be invocated everytime new data is pushed into DD
# It is responsible for collecting tags seen from which anchors
import boto3
import json
from boto3.dynamodb.conditions import Attr

sns_client = boto3.client('sns')
db_resource = boto3.resource('dynamodb')
table = db_resource.Table('atlas_dev')
# s3_client = boto3.client('s3')


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

            # s3_client.put_object(
            #     Bucket='atlas-previous-tags',
            #     Key=tag_id + '/', # this will be the id
            #     Body=b"{id: 32}"
            # )
            #
            # data = s3_client.get_object(
            #     Bucket='atlas-previous-tags',
            #     Key='loop'
            # )

            # debug
            # print(data['Body'].read().decode("utf-8"))
            print(tag)

            found_tags.append(tag_id)
            sns_client.publish(
                TopicArn='arn:aws:sns:ap-southeast-2:430634712358:atlas-lambda',
                Message=json.dumps(tag)
            )
