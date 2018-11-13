import boto3
import json
import time


sns_client = boto3.client('sns', region_name='ap-southeast-2')
iot_data_client = boto3.client('iot-data', region_name='ap-southeast-2')


def lambda_handler(event, context):
    logger = {}
    logger['level'] = ''
    logger['message'] = ''

    try:
        tag_id = event['tag']
        logger['tagId'] = tag_id

        tag = {
            "tag": tag_id,
            "x": float(event['x']),
            "y": float(event['y']),
            "z": float(event['z']),
            "ts": str(time.time())
        }

        iot_data_client.publish(
            topic='atlasDevTagCoords',
            payload=json.dumps(tag)
        )

        sns_client.publish(
            TopicArn='arn:aws:sns:ap-southeast-2:608821816028:proximity_event',
            Message=json.dumps(tag)
        )

        logger['level'] = 'SUCCESS'
        logger['message'] = 'successful MQTT and SNS publish'
        print(json.dumps(logger))

    except ValueError:
        logger['level'] = 'ERROR'
        logger['message'] = 'Number Value Error; float parse failed'
        print(json.dumps(logger))
    except NameError:
        logger['level'] = 'ERROR'
        logger['message'] = 'Name Read Error; cannot access value by name'
        print(json.dumps(logger))
