# instance of a single tags seen anchors and distances
import json
import redis

r = redis.StrictRedis(host='atlas-pubsub-dev.poxwmo.ng.0001.apse2.cache.amazonaws.com', port=6379, db=0)


def triangulate(a):
    print(a)
    r.publish('tags', str(a[0]['dist']))
    return 0


def lambda_handler(event, context):
    data = json.loads(event['Records'][0]['Sns']['Message'])
    tag = data['id']
    anchors = data['anchors']
    anchors.append({"id": '99A2', "dist": 3.52, "ts": '1537923894.0602722'})
    anchors.append({"id": '99A1', "dist": 7.52, "ts": '1537923802.0602722'})
    anchors.append({"id": '99A3', "dist": 1.52, "ts": '1537923823.0602722'})
    # anchors = [
    #     {"id": '99A2', "dist": 3.52, "ts": '1537923894.0602722'},
    #     {"id": '99A1', "dist": 7.52, "ts": '1537923802.0602722'},
    #     {"id": '99A3', "dist": 1.52, "ts": '1537923823.0602722'},
    #     {"id": '99A4', "dist": 0.52, "ts": '1537923835.0602722'}
    # ]
    a_len = len(anchors)
    if a_len < 3:
        print('not enough anchor points for accurate triangulation')
        return
    else:
        if a_len == 3:
            triangulate(anchors)
        else:
            anchors.sort(key=lambda x: x['dist'])
            triangulate(anchors[0:3])
