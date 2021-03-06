# instance of a single tags seen anchors and distances
import json
import numpy as np
import itertools
import math
import boto3
import time
import uuid


sns_client = boto3.client('sns', region_name='ap-southeast-2')
iot_data_client = boto3.client('iot-data', region_name='ap-southeast-2')
db_resource = boto3.resource('dynamodb')
table = db_resource.Table('atlas_dev_anchor_location')
TIME_DIFFERENCE = 0.4


## Circle class; used for finding the intersection points of two circles
class Circle(object):
    """ An OOP implementation of a circle as an object """

    def __init__(self, xposition, yposition, radius):
        self.xpos = xposition
        self.ypos = yposition
        self.radius = radius

    def circle_intersect(self, circle2, logger):
        """
        Intersection points of two circles using the construction of triangles
        as proposed by Paul Bourke, 1997.
        http://paulbourke.net/geometry/circlesphere/
        """
        X1, Y1 = self.xpos, self.ypos
        X2, Y2 = circle2.xpos, circle2.ypos
        R1, R2 = self.radius, circle2.radius

        Dx = X2-X1
        Dy = Y2-Y1
        D = math.sqrt(Dx**2 + Dy**2)
        # Distance between circle centres
        if D > R1 + R2:
            logger['message'] = 'The circles do not intersect'
            logger['level'] = 'ERROR'
            print(json.dumps(logger))
            return "The circles do not intersect"
        elif D < math.fabs(R2 - R1):
            logger['message'] = 'No Intersect - One circle is contained within the other'
            logger['level'] = 'ERROR'
            print(json.dumps(logger))
            return "No Intersect - One circle is contained within the other"
        elif D == 0 and R1 == R2:
            logger['message'] = 'No Intersect - The circles are equal and coincident'
            logger['level'] = 'ERROR'
            print(json.dumps(logger))
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
            I1 = (chordmidpointx + (halfchordlength*Dy)/D,
                  chordmidpointy - (halfchordlength*Dx)/D)
            theta1 = math.degrees(math.atan2(I1[1]-Y1, I1[0]-X1))
            I2 = (chordmidpointx - (halfchordlength*Dy)/D,
                  chordmidpointy + (halfchordlength*Dx)/D)
            theta2 = math.degrees(math.atan2(I2[1]-Y1, I2[0]-X1))
            if theta2 > theta1:
                I1, I2 = I2, I1
            return (I1, I2, CASE)

    def __str__(self):
        return "x is %s, y is %s, radius is %s" % (self.xpos, self.ypos, self.radius)


# Calculate distance between two points given Cartesian coordinates
def calc_dist(p0, p1):
    diff = p1 - p0
    sum_sq = np.sum(diff**2)
    return sum_sq**.5


## Do two spheres intersect?
def sphere_intersect(anchorA, rA, anchorB, rB):
    dist = calc_dist(anchorA, anchorB)
    if dist >= (rA + rB) or (dist + rA) <= rB or (dist + rB) <= rA:
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
def trilateration(anchor0, r0, anchor1, r1, anchor2, r2, logger):
    anchor0_mod = np.subtract(anchor0, anchor0)
    anchor1_mod = np.subtract(anchor1, anchor0)
    anchor2_mod = np.subtract(anchor2, anchor0)

    e_x = (anchor1_mod - anchor0_mod) / calc_dist(anchor0_mod, anchor1_mod)
    i = np.sum(e_x * (anchor2_mod - anchor0_mod))
    e_y = (anchor2_mod - anchor0_mod - i*e_x) / calc_dist(anchor2_mod - anchor0_mod, i*e_x)
    e_z = np.array((e_x[1]*e_y[2] - e_x[2]*e_y[1], e_x[2]*e_y[0] - e_x[0]*e_y[2], e_x[0]*e_y[1] - e_x[1]*e_y[0]))

    anchor0_mod = np.array((np.sum(anchor0_mod*e_x), np.sum(anchor0_mod*e_y), np.sum(anchor0_mod*e_z)))
    anchor1_mod = np.array((np.sum(anchor1_mod*e_x), np.sum(anchor1_mod*e_y), np.sum(anchor1_mod*e_z)))
    anchor2_mod = np.array((np.sum(anchor2_mod*e_x), np.sum(anchor2_mod*e_y), np.sum(anchor2_mod*e_z)))

    x = (r0**2 - r1**2 + anchor1_mod[0]**2) / (2 * anchor1_mod[0])
    y = ((r0**2 - r2**2 + anchor2_mod[0]**2 + anchor2_mod[1]**2) / (2 * anchor2_mod[1])) - ((x * anchor2_mod[0]) / anchor2_mod[1])

    if not (sphere_intersect(anchor0, r0, anchor1, r1) and sphere_intersect(anchor0, r0, anchor2, r2) and sphere_intersect(anchor1, r1, anchor2, r2)):
        candidates = []
        selections = []
        for B in [(anchor0_mod, r0, anchor1_mod, r1), (anchor0_mod, r0, anchor2_mod, r2), (anchor1_mod, r1, anchor2_mod, r2)]:
            anchorA = np.array([])
            anchorB = np.array([])
            rA = 0
            rB = 0
            if B[1] > B[3]:
                anchorA = B[0]
                anchorB = B[2]
                rA = B[1]
                rB = B[3]
            else:
                anchorA = B[2]
                anchorB = B[0]
                rA = B[3]
                rB = B[1]
            if sphere_intersect(anchorA, rA, anchorB, rB):
                cA = Circle(anchorA[0], anchorA[1], rA)
                cB = Circle(anchorB[0], anchorB[1], rB)
                candidates.append((np.array(cA.circle_intersect(cB, logger)[0]), np.array(cA.circle_intersect(cB, logger)[1])))
            else:
                dist = calc_dist(anchorA, anchorB)
                if dist > (rA + rB):
                    logger['circleIntersects'] = 'No intersect but far apart'
                    vec_A_to_B = anchorB - anchorA
                    unit_vec_A_to_B = vec_A_to_B / np.sum(vec_A_to_B**2)**.5
                    edgeA = anchorA + rA*unit_vec_A_to_B
                    edgeB = anchorB - rB*unit_vec_A_to_B
                    selections.append(np.mean((edgeA, edgeB), axis = 0)[0:2])
                else:
                    logger['circleIntersects'] = 'Sphere within a sphere'
                    vec_A_to_B = anchorB - anchorA
                    unit_vec_A_to_B = vec_A_to_B / np.sum(vec_A_to_B**2)**.5
                    edgeA = anchorA + rA*unit_vec_A_to_B
                    edgeB = anchorB + rB*unit_vec_A_to_B
                    selections.append(np.mean((edgeA, edgeB), axis = 0)[0:2])
        for candidate in candidates:
            dist0 = calc_dist(candidate[0], selections[0])
            dist1 = calc_dist(candidate[1], selections[0])
            if dist0 < dist1:
                selections.append(candidate[0])
            else:
                selections.append(candidate[1])
        ave_point = np.mean(selections, axis=0)
        ave_point = anchor0 + ave_point[0]*e_x + ave_point[1]*e_y
        return(ave_point)
    elif (r0**2 - x**2 - y**2) >= 0:
        logger['circleIntersects'] = 'Other'
        z_pos = np.sqrt(r0**2 - x**2 - y**2)
        z_neg = -1 * np.sqrt(r0**2 - x**2 - y**2)
        p0 = anchor0 + x*e_x + y*e_y + z_pos*e_z
        p1 = anchor0 + x*e_x + y*e_y + z_neg*e_z
        return([p0, p1])
    else:
        logger['circleIntersects'] = 'Normal'
        c0 = Circle(0, 0, r0)
        c1 = Circle(anchor1_mod[0], 0, r1)
        c2 = Circle(anchor2_mod[0], anchor2_mod[1], r2)
        p0_1 = np.array(c0.circle_intersect(c1, logger)[0:2])
        p0_2 = np.array(c0.circle_intersect(c2, logger)[0:2])
        p1_2 = np.array(c1.circle_intersect(c2, logger)[0:2])
        closest01_02 = find_two_closest(p0_1, p0_2)
        closest01_12 = find_two_closest(p0_1, p1_2)
        p0 = p0_1[closest01_02[0]]
        p1 = p0_2[closest01_02[1]]
        p2 = p1_2[closest01_12[1]]
        ave_point = np.mean(np.array([p0, p1, p2]), axis=0)
        ave_point = anchor0 + ave_point[0]*e_x + ave_point[1]*e_y
        return(ave_point)


def triangulate(anchors, tag_id, positions, logger):
    # Find all possible singal points based on trilateration
    combinations = []
    for i in range(0, len(anchors)):
        combinations.append([np.array(positions[anchors[i]['id']]), anchors[i]['dist']])

    ## Find all possible singal points based on trilateration
    trianchors = itertools.combinations(combinations, 3)
    candidates = []
    selections = []
    for B in trianchors:
        trilat = trilateration(B[0][0], B[0][1], B[1][0], B[1][1], B[2][0], B[2][1], logger)
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

    data = {
        "tag": tag_id,
        "x": pos_mean[0] - 1,
        "y": pos_mean[1] - 1,
        "z": time.time()
    }

    iot_data_client.publish(
        topic='atlasDevTagCoords',
        payload=json.dumps(data)
    )

    iot_data_client.publish(
        topic='atlasTag' + tag_id + 'Coords',
        payload=json.dumps(data)
    )

    sns_client.publish(
        TopicArn='arn:aws:sns:ap-southeast-2:430634712358:atlas-proximity-event',
        Message=json.dumps(data)
    )

    logger['level'] = 'SUCCESS'
    logger['anchors'] = anchors
    logger['message'] = ''
    logger['coords'] = data
    print(json.dumps(logger))

    return 0


def time_check(s_a, l, logger):
    time_diff = s_a[0]['ts'] - s_a[l - 1]['ts']
    if time_diff < TIME_DIFFERENCE:
        return True
    else:
        logger['failedTimeChecks'].append('{} is greater than set time difference of {}'.format(time_diff, TIME_DIFFERENCE))
        return False


def lambda_handler(event, context):
    logger = {}

    # get tags and anchors
    data = json.loads(event['Records'][0]['Sns']['Message'])

    # get anchor positions
    response = table.scan(Select='ALL_ATTRIBUTES')
    anchor_positions = {}
    for i in response['Items']:
        coords = []
        coords.append(float(i['coords'][0]))
        coords.append(float(i['coords'][1]))
        coords.append(float(i['coords'][2]))
        anchor_positions[i['anchorId']] = coords

    tag_id = data['id']
    anchors = data['anchors']
    a_len = len(anchors)
    uid = str(uuid.uuid4())

    logger['uuid'] = uid
    logger['tagId'] = tag_id
    logger['anchors'] = anchors
    logger['failedTimeChecks'] = []
    logger['circleIntersects'] = ''

    if a_len < 4:
        logger['level'] = 'INFO'
        logger['message'] = 'not enough anchor points for accurate triangulation'
        print(json.dumps(logger))
        return

    else:
        # dist_sort = sorted(anchors,key=lambda x: x['dist'], reverse=True)
        time_sort = sorted(anchors, key=lambda x: x['ts'], reverse=True)

        for i in range(0, a_len - 4):
            if time_check(time_sort, a_len - i, logger):
                triangulate(time_sort, tag_id, anchor_positions, logger)
                return
            else:
                time_sort.pop()
        else:
            logger['level'] = 'DEBUG'
            logger['message'] = 'Tag skipped'
            print(json.dumps(logger))
            return