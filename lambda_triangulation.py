# instance of a single tags seen anchors and distances
import json
import redis
from functools import reduce

r = redis.StrictRedis(host='atlas-pubsub-dev.poxwmo.ng.0001.apse2.cache.amazonaws.com', port=6379, db=0)
positions = {
    "99A4": {
        "x": 4.00,
        "y": 7.50
    },
    "CBB5": {
        "x": 4.00,
        "y": 4.00
    },
    "8986": {
        "x": 10.54,
        "y": 7.50
    },
    "9895": {
        "x": 10.54,
        "y": 4.00
    }
}


def triangulate(anchors, tag):
    tag_x = 0
    tag_y = 0

    sum_of_inv = reduce(lambda x, y: x + (1 / y['dist']), anchors, 0)

    for a in anchors:
        dist_by_inv = a['dist'] / sum_of_inv
        tag_x += (positions[a['id']]['x'] / dist_by_inv)
        tag_y += (positions[a['id']]['y'] / dist_by_inv)

    data = {
        "tag": tag,
        "x": tag_x,
        "y": tag_y
    }
    r.publish('atlas_tags', data)
    return 0


def lambda_handler(event, context):
    data = json.loads(event['Records'][0]['Sns']['Message'])
    tag = data['id']
    anchors = data['anchors']

    a_len = len(anchors)
    if a_len < 3:
        print('not enough anchor points for accurate triangulation')
        return
    else:
        if a_len == 3:
            triangulate(anchors, tag)
        else:
            anchors.sort(key=lambda x: x['dist'])
            triangulate(anchors[0:3], tag)
