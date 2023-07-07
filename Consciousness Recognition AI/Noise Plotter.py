from FaceMeshModule import FaceMeshDetector
import matplotlib.pyplot as plt
from datetime import datetime
from copy import copy
import numpy as np
import math
import cv2

LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
for i in [8, 0]:
    LEFT_EYE.pop(i)

RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
for i in [8, 0]:
    RIGHT_EYE.pop(i)

LIPS_INNER = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191]
for i in [10, 0]:
    LIPS_INNER.pop(i)

distances_pairs = [(52, 159), (282, 386), (159, 145), (386, 374), (12, 15), (78, 308)]


def calc_metrics(face, frame):

    metrics = []
    for p in distances_pairs:
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


detector = FaceMeshDetector(maxFaces=1, get_z=True)

cap = cv2.VideoCapture('Test.mp4')
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

previous_time = datetime.now()
previous_metrics = None

left_eyebrow = []
right_eyebrow = []
left_eye = []
right_eye = []
lips_moved = []
mouth_moved = []
face_x = []
face_y = []

length = cap.get(cv2.CAP_PROP_FRAME_COUNT)
fps = int(cap.get(cv2.CAP_PROP_FPS))
target_frame = 0
frame_num = 0
while True:
    _, frame = cap.read()
    _, faces = detector.findFaceMesh(frame)

    if frame is None:
        break

    if frame_num == target_frame:

        if faces:
            cv2.line(frame, faces[0][distances_pairs[0][0]][:2], faces[0][distances_pairs[0][1]][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][distances_pairs[1][0]][:2], faces[0][distances_pairs[1][1]][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][distances_pairs[2][0]][:2], faces[0][distances_pairs[2][1]][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][distances_pairs[3][0]][:2], faces[0][distances_pairs[3][1]][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][12][:2], faces[0][15][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][78][:2], faces[0][308][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][10][:2], faces[0][152][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][234][:2], faces[0][454][:2], (0, 255, 0), 2)

            metrics = calc_metrics(faces[0], frame)
            if previous_metrics is None:
                previous_metrics = copy(metrics)

            left_eyebrow.append(abs(metrics[0] - previous_metrics[0]))
            right_eyebrow.append(abs(metrics[1] - previous_metrics[1]))
            left_eye.append(abs(metrics[2] - previous_metrics[2]))
            right_eye.append(abs(metrics[3] - previous_metrics[3]))
            lips_moved.append(abs(metrics[4] - previous_metrics[4]))
            mouth_moved.append(abs(metrics[5] - previous_metrics[5]))
            face_x.append(abs(metrics[6] - previous_metrics[6]))
            face_y.append(abs(metrics[7] - previous_metrics[7]))

            target_frame += fps // 4
            if target_frame >= length:
                break

    frame_num += 1

plt.subplot(311)
plt.plot(left_eyebrow[1:], label='Left Eyebrow Elevation')
plt.plot(right_eyebrow[1:], label='Right Eyebrow Elevation')
plt.plot(left_eye[1:], label='Left Eye Opening')
plt.plot(right_eye[1:], label='Right Eye Opening')
plt.legend()

plt.title('Eyes Region Position Noise')
plt.xlabel('Time x τ')
plt.ylabel('Position Change (Pixel)')

plt.subplot(312)
plt.plot(lips_moved[1:], label='Lips Opening')
plt.plot(mouth_moved[1:], label='Mouth Wideness')
plt.legend()

plt.title('Mouth Region Position Noise')
plt.xlabel('Time x τ')
plt.ylabel('Position Change (Pixel)')

plt.subplot(313)
plt.plot(face_x[1:], label='Face Tilt')
plt.plot(face_y[1:], label='Face Turn')
plt.legend()

plt.title('Rotation Change Noise')
plt.xlabel('Time x τ')
plt.ylabel('Rotation Change (Degree)')

print('Left Eyebrow Average: ', sum(left_eyebrow) / len(left_eyebrow))
print('Right Eyebrow Average: ', sum(right_eyebrow) / len(right_eyebrow))
print('Left Eye Average: ', sum(left_eye) / len(left_eye))
print('Right Eye Average: ', sum(right_eye) / len(right_eye))
print('Lips Average: ', sum(lips_moved) / len(lips_moved))
print('Mouth Average: ', sum(mouth_moved) / len(mouth_moved))
print('Face Tilt Average: ', sum(face_x) / len(face_x))
print('Face Yaw Average: ', sum(face_y) / len(face_y))

plt.subplots_adjust(hspace=0.5)
plt.show()
cap.release()
cv2.destroyAllWindows()
