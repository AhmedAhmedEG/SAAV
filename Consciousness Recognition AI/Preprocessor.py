from ExternalController.Modules.FaceMeshModule import FaceMeshDetector
from copy import copy
import numpy as np
import math
import csv
import cv2
import os

LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
for i in [8, 0]:
    LEFT_EYE.pop(i)

RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
for i in [8, 0]:
    RIGHT_EYE.pop(i)

LIPS_INNER = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191]
for i in [10, 0]:
    LIPS_INNER.pop(i)

DISTANCE_PAIRS = [(52, 159), (282, 386), (159, 145), (386, 374), (12, 15), (78, 308)]


def calc_metrics(face, frame):

    metrics = []
    for p in DISTANCE_PAIRS:
        metrics.append(math.dist(face[p[0]][:2], face[p[1]][:2]))

    a = (face[234][0] - face[454][0], face[234][1] - face[454][1], face[234][2] - face[454][2])
    b = (0, frame.shape[0], 0)

    x_rotation_radians = np.arccos(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    x_rotation_degrees = (x_rotation_radians * 180) / np.pi

    if np.isnan(x_rotation_degrees):
        x_rotation_degrees = 0

    a = (face[10][0] - face[152][0], face[10][1] - face[152][1], face[10][2] - face[152][2])
    b = (0, frame.shape[1], 0)

    y_rotation_radians = np.arccos(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    y_rotation_degrees = (y_rotation_radians * 180) / np.pi

    if np.isnan(y_rotation_degrees):
        y_rotation_degrees = 0

    metrics.append(x_rotation_degrees)
    metrics.append(y_rotation_degrees)
    return metrics


writer = csv.writer(open('Dataset.csv', 'w', newline=''))
detector = FaceMeshDetector(maxFaces=1, get_z=True)

for d, sfs, fs in os.walk('Dataset'):

    for f in fs:
        cap = cv2.VideoCapture(os.path.join(d, f))
        length = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        sample_deltas = []
        previous_metrics = None
        target_frame = 0
        frame_num = 0
        while True:
            _, frame = cap.read()
            _, faces = detector.findFaceMesh(frame)

            if frame is None:
                break

            if faces:
                cv2.line(frame, faces[0][DISTANCE_PAIRS[0][0]][:2], faces[0][DISTANCE_PAIRS[0][1]][:2], (0, 255, 0), 2)
                cv2.line(frame, faces[0][DISTANCE_PAIRS[1][0]][:2], faces[0][DISTANCE_PAIRS[1][1]][:2], (0, 255, 0), 2)
                cv2.line(frame, faces[0][DISTANCE_PAIRS[2][0]][:2], faces[0][DISTANCE_PAIRS[2][1]][:2], (0, 255, 0), 2)
                cv2.line(frame, faces[0][DISTANCE_PAIRS[3][0]][:2], faces[0][DISTANCE_PAIRS[3][1]][:2], (0, 255, 0), 2)
                cv2.line(frame, faces[0][12][:2], faces[0][15][:2], (0, 255, 0), 2)
                cv2.line(frame, faces[0][78][:2], faces[0][308][:2], (0, 255, 0), 2)
                cv2.line(frame, faces[0][10][:2], faces[0][152][:2], (0, 255, 0), 2)
                cv2.line(frame, faces[0][234][:2], faces[0][454][:2], (0, 255, 0), 2)

            if frame_num == target_frame:

                if faces:
                    metrics = calc_metrics(faces[0], frame)

                    if previous_metrics is None:
                        previous_metrics = copy(metrics)

                    metrics_delta = np.array(metrics) - np.array(previous_metrics)
                    sample_deltas.append(metrics_delta.tolist())

                    previous_metrics = copy(metrics)

                target_frame += fps // 4
                if target_frame >= length:
                    break

            frame_num += 1
            cv2.imshow("Preview", frame)
            cv2.waitKey(1)

        sample_deltas.pop(0)
        sample_deltas.append(1 if os.path.basename(d) == 'Fainting' else 0)
        writer.writerow(sample_deltas)


cap.release()
cv2.destroyAllWindows()
