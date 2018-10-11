#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  7 16:44:23 2018

@author: alex
"""

import numpy as np
import itertools

positions = {
    "99A4": [4.00, 7.5, 5.30],
    "CBB5": [4.00, 4.00, 5.30],
    "8986": [10.54, 7.50, 5.30],
    "9895": [10.54, 4.00, 5.30]
}

anchors = [
    {
        "id": "99A4",
        "dist": 3.9,
        "ts": "1539219559.4443283"
    },
    {
        "id": "CBB5",
        "dist": 3.5,
        "ts": "1539219559.0569048"
    },
    {
        "id": "8986",
        "dist": 4.14,
        "ts": "1539219559.5450587"
    },
    {
        "id": "9895",
        "dist": 4.12,
        "ts": "1539219559.5450587"
    }
]


## Calculate distance between two points given Cartesian coordinates
def calc_dist(p0, p1):
    diff = p1 - p0
    sum_sq = np.sum(diff**2)
    return(sum_sq**.5)

## Given three intersecting spheres, find the two points of intersection
def trilateration(anchor0, r0, anchor1, r1, anchor2, r2):
    anchor0_mod = anchor0 - anchor0
    anchor1_mod = anchor1 - anchor0
    anchor2_mod = anchor2 - anchor0

    e_x = (anchor1_mod - anchor0_mod) / calc_dist(anchor0_mod, anchor1_mod)
    i = np.sum(e_x * (anchor2_mod - anchor0_mod))
    e_y = (anchor2_mod - anchor0_mod - i*e_x) / calc_dist(anchor2_mod - anchor0_mod, i*e_x)
    e_z = np.array((e_x[1]*e_y[2] - e_x[2]*e_y[1], e_x[2]*e_y[0] - e_x[0]*e_y[2], e_x[0]*e_y[1] - e_x[1]*e_y[0]))

    anchor0_mod = np.array((np.sum(anchor0_mod*e_x), np.sum(anchor0_mod*e_y), np.sum(anchor0_mod*e_z)))
    anchor1_mod = np.array((np.sum(anchor1_mod*e_x), np.sum(anchor1_mod*e_y), np.sum(anchor1_mod*e_z)))
    anchor2_mod = np.array((np.sum(anchor2_mod*e_x), np.sum(anchor2_mod*e_y), np.sum(anchor2_mod*e_z)))

    x = (r0**2 - r1**2 + anchor1_mod[0]**2) / (2 * anchor1_mod[0])
    y = ((r0**2 - r2**2 + anchor2_mod[0]**2 + anchor2_mod[1]**2) / (2 * anchor2_mod[1])) - ((x * anchor2_mod[0]) / anchor2_mod[1])
    z_pos = np.sqrt(r0**2 - x**2 - y**2)
    z_neg = -1 * np.sqrt(r0**2 - x**2 - y**2)

    p0 = anchor0 + x*e_x + y*e_y + z_pos*e_z
    p1 = anchor0 + x*e_x + y*e_y + z_neg*e_z
    return([p0, p1])


## Specify anchor points and radii
# anchor0 = np.array((1.8, 0.9, 1.2))
# anchor1 = np.array((-0.2, 7.3, 1.6))
# anchor2 = np.array((6.5, 1.3, 0.8))
# anchor3 = np.array((8.1, 6.9, 1.5))

#anchor0 = np.array((1.8, 0.9, 0))
#anchor1 = np.array((-0.2, 7.3, 0.2))
#anchor2 = np.array((6.5, 1.3, 1.9))
#anchor3 = np.array((8.1, 6.9, 2.2))

anchor0 = np.array(positions[anchors[0]['id']])
anchor1 = np.array(positions[anchors[1]['id']])
anchor2 = np.array(positions[anchors[2]['id']])
anchor3 = np.array(positions[anchors[3]['id']])

signal = np.array((7.4, 5.2, 5.1))

# r0 = calc_dist(anchor0, signal) + np.random.rand()*.1 + .05
# r1 = calc_dist(anchor1, signal) + np.random.rand()*.1 + .05
# r2 = calc_dist(anchor2, signal) + np.random.rand()*.1 + .05
# r3 = calc_dist(anchor3, signal) + np.random.rand()*.1 + .05

r0 = anchors[0]['dist']
r1 = anchors[1]['dist']
r2 = anchors[2]['dist']
r3 = anchors[3]['dist']

## Find all possible singal points based on trilateration
trianchors = itertools.combinations([(anchor0, r0), (anchor1, r1), (anchor2, r2), (anchor3, r3)], 3)
candidates = [trilateration(B[0][0], B[0][1], B[1][0], B[1][1], B[2][0], B[2][1]) for B in trianchors]

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

signal_hat = np.mean(selections, axis=0)
error = signal_hat - signal
mag_error = np.sum(error**2)**.5
mag_error_xy = np.sum(error[0:2]**2)**.5

print("Signal:                                      " + str(signal))
print("Estimated signal:                            " + str(signal_hat))
print("Error:                                       " + str(error))
print("Magnitude of error:                          " + str(mag_error))
print("Magnitude of error, x and y components only: " + str(mag_error_xy))
