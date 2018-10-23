# instance of a single tags seen anchors and distances
import json
import numpy as np
import itertools
import math
import boto3


sns_client = boto3.client('sns', region_name='ap-southeast-2')
iot_data_client = boto3.client('iot-data', region_name='ap-southeast-2')
db_resource = boto3.resource('dynamodb')
table = db_resource.Table('atlas_dev_anchor_location')

# TODO: get positions from db
positions = {
    "99A4": [1.0, 15.5, 3.7],
    "CBB5": [1.5, 5.5, 3.6],
    "8986": [7.3, 23.9, 3.7],
    "1123": [7.4, 16.0, 3.6],
    "422F": [7.2, 6.0, 3.6],
    "9895": [1.0, 23.0, 3.7]
}


## Circle class; used for finding the intersection points of two circles
class Circle(object):
    """ An OOP implementation of a circle as an object """

    def __init__(self, xposition, yposition, radius):
        self.xpos = xposition
        self.ypos = yposition
        self.radius = radius

    def circle_intersect(self, circle2):
        """
        Intersection points of two circles using the construction of triangles
        as proposed by Paul Bourke, 1997.
        http://paulbourke.net/geometry/circlesphere/
        """
        PRECISION = 8
        X1, Y1 = self.xpos, self.ypos
        X2, Y2 = circle2.xpos, circle2.ypos
        R1, R2 = self.radius, circle2.radius

        Dx = X2-X1
        Dy = Y2-Y1
        D = round(math.sqrt(Dx**2 + Dy**2), PRECISION)
        # Distance between circle centres
        if D > R1 + R2:
            return "The circles do not intersect"
        elif D < math.fabs(R2 - R1):
            return "No Intersect - One circle is contained within the other"
        elif D == 0 and R1 == R2:
            return "No Intersect - The circles are equal and coincident"
        else:
            if D == R1 + R2 or D == R1 - R2:
                CASE = "The circles intersect at a single point"
            else:
                CASE = "The circles intersect at two points"
            chorddistance = (R1**2 - R2**2 + D**2)/(2*D)
            # distance from 1st circle's centre to the chord between intersects
            halfchordlength = math.sqrt(R1**2 - chorddistance**2)
            chordmidpointx = X1 + (chorddistance*Dx)/D
            chordmidpointy = Y1 + (chorddistance*Dy)/D
            I1 = (round(chordmidpointx + (halfchordlength*Dy)/D, PRECISION),
                  round(chordmidpointy - (halfchordlength*Dx)/D, PRECISION))
            theta1 = round(math.degrees(math.atan2(I1[1]-Y1, I1[0]-X1)),
                           PRECISION)
            I2 = (round(chordmidpointx - (halfchordlength*Dy)/D, PRECISION),
                  round(chordmidpointy + (halfchordlength*Dx)/D, PRECISION))
            theta2 = round(math.degrees(math.atan2(I2[1]-Y1, I2[0]-X1)),
                           PRECISION)
            if theta2 > theta1:
                I1, I2 = I2, I1
            return (I1, I2, CASE)


# Calculate distance between two points given Cartesian coordinates
def calc_dist(p0, p1):
    diff = p1 - p0
    sum_sq = np.sum(diff**2)
    return sum_sq**.5


## Do two spheres intersect?
def sphere_intersect(anchorA, rA, anchorB, rB, r0, r1):
    dist = calc_dist(anchorA, anchorB)
    if dist > (rA + rB) or (dist + r1) < r0 or (dist + r0) < r1:
        return False
    else:
        return True


def find_two_closest(pointsA, pointsB):
    dist0 = calc_dist(pointsA[0], pointsB[0])
    dist1 = calc_dist(pointsA[1], pointsB[0])
    dist2 = calc_dist(pointsA[0], pointsB[1])
    dist3 = calc_dist(pointsA[1], pointsB[1])
    min_dist = min(dist0, dist1, dist2, dist3)
    if min_dist == dist0:
        return([0, 0])
    elif min_dist == dist1:
        return([1, 0])
    elif min_dist == dist2:
        return([0, 1])
    else:
        return([1, 1])


# Given three intersecting spheres, find the two points of intersection
def trilateration(anchor0, r0, anchor1, r1, anchor2, r2):
    if not (sphere_intersect(anchor0, r0, anchor1, r1, r0, r1) and sphere_intersect(anchor0, r0, anchor2, r2, r0, r1) and sphere_intersect(anchor1, r1, anchor2, r2, r0, r1)):
        return([])

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

    x = (r0**2 - r1**2 + anchor1_mod[0]**2) / (2 * anchor1_mod[0])
    y = ((r0**2 - r2**2 + anchor2_mod[0]**2 + anchor2_mod[1]**2) / (2 * anchor2_mod[1])) - ((x * anchor2_mod[0]) / anchor2_mod[1])

    if (r0**2 - x**2 - y**2) >= 0:
        z_pos = np.sqrt(r0**2 - x**2 - y**2)
        z_neg = -1 * np.sqrt(r0**2 - x**2 - y**2)
        p0 = anchor0 + x*e_x + y*e_y + z_pos*e_z
        p1 = anchor0 + x*e_x + y*e_y + z_neg*e_z
        return([p0, p1])
    else:
        c0 = Circle(0, 0, r0)
        c1 = Circle(anchor1_mod[0], 0, r1)
        c2 = Circle(anchor2_mod[0], anchor2_mod[1], r2)
        p0_1 = np.array(c0.circle_intersect(c1)[0:2])
        p0_2 = np.array(c0.circle_intersect(c2)[0:2])
        p1_2 = np.array(c1.circle_intersect(c2)[0:2])
        print('p0_1')
        print(p0_1)
        print('p0_2')
        print(p0_2)
        print('p1_2')
        print(p1_2)
        closest01_02 = find_two_closest(p0_1, p0_2)
        closest01_12 = find_two_closest(p0_1, p1_2)
        p0 = p0_1[closest01_02[0]]
        p1 = p0_2[closest01_02[1]]
        p2 = p1_2[closest01_12[1]]
        ave_point = np.mean(np.array([p0, p1, p2]), axis=0)
        ave_point = anchor0 + ave_point[0]*e_x + ave_point[1]*e_y
        return(ave_point)


def triangulate(anchors, tag_id):
    # Find all possible singal points based on trilateration
    a0 = np.array(positions[anchors[0]['id']])
    r0 = anchors[0]['dist']
    a1 = np.array(positions[anchors[1]['id']])
    r1 = anchors[1]['dist']
    a2 = np.array(positions[anchors[2]['id']])
    r2 = anchors[2]['dist']
    a3 = np.array(positions[anchors[3]['id']])
    r3 = anchors[3]['dist']

    ## Find all possible singal points based on trilateration
    trianchors = itertools.combinations([(a0, r0), (a1, r1), (a2, r2), (a3, r3)], 3)
    candidates = []
    selections = []
    for B in trianchors:
        trilat = trilateration(B[0][0], B[0][1], B[1][0], B[1][1], B[2][0], B[2][1])
        if len(trilat) == 0:
            continue
        if type(trilat) == list:
            candidates.append(trilat)
        else:
            selections.append(trilat)

    ## Compare pairs of points from trilaterion
    votes = np.zeros((len(candidates), 2))
    for i in range(0, len(candidates) - 1):
        for j in range(i+1, len(candidates)):
            pair0 = candidates[i]
            pair1 = candidates[j]
            dist0 = calc_dist(pair0[0], pair1[0])
            dist1 = calc_dist(pair0[1], pair1[0])
            dist2 = calc_dist(pair0[0], pair1[1])
            dist3 = calc_dist(pair0[1], pair1[1])
            min_dist = min([dist0, dist1, dist2, dist3])
            if min_dist == dist0:
                votes[i, 0] += 1
                votes[j, 0] += 1
            elif min_dist == dist1:
                votes[i, 1] += 1
                votes[j, 0] += 1
            elif min_dist == dist2:
                votes[i, 0] += 1
                votes[j, 1] += 1
            else:
                votes[i, 1] += 1
                votes[j, 1] += 1

    ## Compare pairs to single points from trilateration
    for i in range(len(candidates)):
        for sel in selections:
            dist0 = calc_dist(candidates[i][0], sel)
            dist1 = calc_dist(candidates[i][1], sel)
            min_dist = min([dist0, dist1])
            if min_dist == dist0:
                votes[i, 0] += 1
            else:
                votes[i, 1] += 1

    ## Pick good points from pairs and add them to the list of selections
    for i in range(len(candidates)):
        if votes[i, 0] > votes[i, 1]:
            selections.append(candidates[i][0])
        elif votes[i, 1] > votes[i, 0]:
            selections.append(candidates[i][1])
        else:
            selections.append(np.mean(candidates[i], 0))

    pos_mean = np.mean(selections, axis=0)

    print('pos_mean: ')
    print(pos_mean)

    data = {
        "tag": tag_id,
        "x": pos_mean[0] - 1,
        "y": pos_mean[1] - 1,
        "z": pos_mean[2] - 1
    }

    iot_data_client.publish(
        topic='atlasDevTagCoords',
        payload=json.dumps(data)
    )

    sns_client.publish(
        TopicArn='arn:aws:sns:ap-southeast-2:430634712358:atlas-proximity-event',
        Message=json.dumps(data)
    )
    return 0


def lambda_handler(event, context):
    # get tags and anchors
    data = json.loads(event['Records'][0]['Sns']['Message'])

    # get anchor positions
    response = table.scan(Select='ALL_ATTRIBUTES')
    anchor_positions = {}
    for i in response['Items']:
        anchor_positions[i['anchorId']] = i['coords']

    print(anchor_positions)

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
            anchors.sort(key=lambda x: x['ts'], reverse=True)
            triangulate(anchors[0:4], tag_id)