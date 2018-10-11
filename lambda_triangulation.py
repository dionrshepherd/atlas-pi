# instance of a single tags seen anchors and distances
import json
import redis
import numpy as np
import itertools

r = redis.StrictRedis(host='atlas-pubsub-dev.poxwmo.ng.0001.apse2.cache.amazonaws.com', port=6379, db=0)
# positions = {
#     "99A4": {
#         "x": 4.00,
#         "y": 7.50,
#         "z": 1
#     },
#     "CBB5": {
#         "x": 4.00,
#         "y": 4.00,
#         "z": 1
#     },
#     "8986": {
#         "x": 10.54,
#         "y": 7.50,
#         "z": 1
#     },
#     "9895": {
#         "x": 10.54,
#         "y": 4.00,
#         "z": 1
#     }
# }
positions = {
    "99A4": [4.00, 7.5, 5.30],
    "CBB5": [4.00, 4.00, 5.30],
    "8986": [10.54, 7.50, 5.30],
    "9895": [10.54, 4.00, 5.30]
}


# Calculate distance between two points given Cartesian coordinates
def calc_dist(p0, p1):
    diff = p1 - p0
    sum_sq = np.sum(diff**2)
    return sum_sq**.5


# Given three intersecting spheres, find the two points of intersection
def trilateration(anchor0, r0, anchor1, r1, anchor2, r2):
    anchor0_mod = np.subtract(anchor0, anchor0)
    anchor1_mod = np.subtract(anchor1, anchor0)
    anchor2_mod = np.subtract(anchor2, anchor0)

    e_x = (np.subtract(anchor1_mod, anchor0_mod)) / calc_dist(anchor0_mod, anchor1_mod)
    i = np.sum(e_x * (np.subtract(anchor2_mod, anchor0_mod)))
    e_y = (np.subtract(anchor2_mod, anchor0_mod) - i*e_x) / calc_dist(np.subtract(anchor2_mod, anchor0_mod), i*e_x)
    e_z = np.array((e_x[1]*e_y[2] - e_x[2]*e_y[1], e_x[2]*e_y[0] - e_x[0]*e_y[2], e_x[0]*e_y[1] - e_x[1]*e_y[0]))

    anchor0_mod = np.array((np.sum(anchor0_mod*e_x), np.sum(anchor0_mod*e_y), np.sum(anchor0_mod*e_z)))
    anchor1_mod = np.array((np.sum(anchor1_mod*e_x), np.sum(anchor1_mod*e_y), np.sum(anchor1_mod*e_z)))
    anchor2_mod = np.array((np.sum(anchor2_mod*e_x), np.sum(anchor2_mod*e_y), np.sum(anchor2_mod*e_z)))

    # print('mods')
    # print(anchor0_mod)
    # print(anchor1_mod)
    # print(anchor2_mod)

    x = (r0**2 - r1**2 + anchor1_mod[0]**2) / (2 * anchor1_mod[0])
    y = ((r0**2 - r2**2 + anchor2_mod[0]**2 + anchor2_mod[1]**2) / (2 * anchor2_mod[1])) - ((x * anchor2_mod[0]) / anchor2_mod[1])
    z_pos = np.sqrt(r0**2 - x**2 - y**2)
    z_neg = -1 * np.sqrt(r0**2 - x**2 - y**2)

    p0 = anchor0 + x*e_x + y*e_y + z_pos*e_z
    p1 = anchor0 + x*e_x + y*e_y + z_neg*e_z
    return([p0, p1])


def triangulate(anchors, tag_id):
    # Find all possible singal points based on trilateration
    print('anchors')
    print(anchors)

    a0 = np.array(positions[anchors[0]['id']])
    r0 = anchors[0]['dist']
    a1 = np.array(positions[anchors[1]['id']])
    r1 = anchors[1]['dist']
    a2 = np.array(positions[anchors[2]['id']])
    r2 = anchors[2]['dist']
    a3 = np.array(positions[anchors[3]['id']])
    r3 = anchors[3]['dist']
    print('anchor arr')
    print(a0)
    print(a1)
    print(a2)
    print(a3)

    trianchors = itertools.combinations([(a0, r0), (a1, r1), (a2, r2), (a3, r3)], 3)
    candidates = [trilateration(B[0][0], B[0][1], B[1][0], B[1][1], B[2][0], B[2][1]) for B in trianchors]
    # print('cands')
    # print(candidates)

    # calculate
    votes = np.zeros((len(candidates), 2))
    for i in range(0, len(candidates) - 1):
        for j in range(i+1, len(candidates)):
            pair0 = candidates[i]
            pair1 = candidates[j]
            dist_0 = calc_dist(pair0[0], pair1[0])
            dist_1 = calc_dist(pair0[1], pair1[0])
            dist_2 = calc_dist(pair0[0], pair1[1])
            dist_3 = calc_dist(pair0[1], pair1[1])
            min_dist = min([dist_0, dist_1, dist_2, dist_3])
            if min_dist == dist_0:
                votes[i, 0] += 1
                votes[j, 0] += 1
            elif min_dist == dist_1:
                votes[i, 1] += 1
                votes[j, 0] += 1
            elif min_dist == dist_2:
                votes[i, 0] += 1
                votes[j, 1] += 1
            else:
                votes[i, 1] += 1
                votes[j, 1] += 1

    selections = []
    for i in range(len(candidates)):
        if votes[i, 0] > votes[i, 1]:
            selections.append(candidates[i][0])
        elif votes[i, 1] > votes[i, 0]:
            selections.append(candidates[i][1])
        else:
            selections.append(np.mean(candidates[i], 0))

    data = {
        "tag": tag_id,
        "position": np.mean(selections, axis=0)
    }
    r.publish('atlas_tags', data)
    return 0


def lambda_handler(event, context):
    data = json.loads(event['Records'][0]['Sns']['Message'])
    tag_id = data['id']
    anchors = data['anchors']

    a_len = len(anchors)
    if a_len < 4:
        print('not enough anchor points for accurate triangulation')
        return
    else:
        if a_len == 4:
            triangulate(anchors, tag_id)
        else:
            anchors.sort(key=lambda x: x['dist'])
            triangulate(anchors[0:4], tag_id)
