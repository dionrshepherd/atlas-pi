# This will be invocated everytime new data is pushed into DD
# It is responsible for collecting tags seen from which anchors

print('Calling Handler')

def lambda_handler(event, context):
    tags = []
    found_tags = []
    for record in event['Records']:

        anchor_id = record['dynamodb']['NewImage']['anchor']['S']
        tag_id = record['dynamodb']['NewImage']['tag']['S']

        anchor = {
            'id': anchor_id,
            'dist': float(record['dynamodb']['NewImage']['data']['M']['dist']['S']),
            'ts': record['dynamodb']['NewImage']['data']['M']['ts']['S']
        }

        try:
            t_id = found_tags.index(tag_id)
            tags[t_id]['anchors'].append(anchor)

        except ValueError:
            tag = {
                'id': tag_id,
                'anchors': [anchor]
            }
            tags.append(tag)
            found_tags.append(tag_id)

    print(tags)