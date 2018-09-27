# instance of a single tags seen anchors and distances
import json
import redis
from functools import reduce

r = redis.StrictRedis(host='atlas-pubsub-dev.poxwmo.ng.0001.apse2.cache.amazonaws.com', port=6379, db=0)
positions = {
    "99A4": {
        "x": 20,
        "y": 20
    },
    "16B6": {
        "x": 40,
        "y": 60
    },
    "65TG": {
        "x": 30,
        "y": 65
    },
    "99A1": {
        "x": 90,
        "y": 85
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

    anchors.append({"id": '16B6', "dist": 3.52, "ts": '1537923894.0602722'})
    anchors.append({"id": '99A1', "dist": 9.99, "ts": '1537923802.0602722'})
    anchors.append({"id": '65TG', "dist": 1.52, "ts": '1537923823.0602722'})

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
