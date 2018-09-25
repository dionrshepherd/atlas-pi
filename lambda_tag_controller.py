# This will be invocated everytime new data is pushed into DD
# It is responsible for collecting tags seen from which anchors


# Tag class for storing the tags and distances
class Tag(object):
    tag_id = ''
    distance = 0.0
    time_stamp = ''

    def __init__(self, ti, dist, ts):
        self.tag_id = ti
        self.distance = dist
        self.time_stamp = ts

    def __repr__(self):
        return "Tag: %s, dist: %s, ts: %s" % (self.tag_id, self.distance, self.time_stamp)


# Anchor class for storing id tags seen
class Anchor(object):
    anchor_id = ''
    tags = []
    tag_ids = []

    def __init__(self, ai):
        self.anchor_id = ai

    def __repr__(self):
        return "Anchor: %s, Tags: %s, tagIds: %s" % (self.anchor_id, self.tags, self.tag_ids)


def lambda_handler(event, context):
    list_data = []
    found_anchors = []
    for record in event['Records']:
        # get anchor and tag id each iteration
        anchor_id = record['dynamodb']['NewImage']['anchor']['S']
        tag_id = record['dynamodb']['NewImage']['tag']['S']

        # set instance of tag class for every iteration
        tag = Tag(tag_id, float(record['dynamodb']['NewImage']['data']['M']['dist']['S']), record['dynamodb']['NewImage']['data']['M']['ts']['S'])

        try:
            a_idx = found_anchors.index(anchor_id)
            try:
                t_idx = list_data[a_idx].tag_ids.index(tag_id)
                list_data[a_idx].tags[t_idx] = tag
            except ValueError:
                list_data[a_idx].tags.append(tag)
        except ValueError:
            anchor = Anchor(anchor_id)
            anchor.tags.append(tag)
            anchor.tag_ids.append(tag_id)
            list_data.append(anchor)
            found_anchors.append(anchor_id)

    # from here spawn new lambda instances
    print(list_data[0])