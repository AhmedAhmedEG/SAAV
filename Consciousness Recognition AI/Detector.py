from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
from FaceMeshModule import FaceMeshDetector
from datetime import datetime
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
model = load_model('FaintingDetector.h5')
scaler = MinMaxScaler()

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

memory = []
previous_time = datetime.now()
while True:
    _, frame = cap.read()
    _, faces = detector.findFaceMesh(frame)

    if faces:
        cv2.line(frame, faces[0][distances_pairs[0][0]][:2], faces[0][distances_pairs[0][1]][:2], (0, 255, 0), 2)
        cv2.line(frame, faces[0][distances_pairs[1][0]][:2], faces[0][distances_pairs[1][1]][:2], (0, 255, 0), 2)
        cv2.line(frame, faces[0][distances_pairs[2][0]][:2], faces[0][distances_pairs[2][1]][:2], (0, 255, 0), 2)
        cv2.line(frame, faces[0][distances_pairs[3][0]][:2], faces[0][distances_pairs[3][1]][:2], (0, 255, 0), 2)
        cv2.line(frame, faces[0][78][:2], faces[0][308][:2], (0, 255, 0), 2)
        cv2.line(frame, faces[0][10][:2], faces[0][152][:2], (0, 255, 0), 2)
        cv2.line(frame, faces[0][234][:2], faces[0][454][:2], (0, 255, 0), 2)

        time_passed = (datetime.now() - previous_time).microseconds * 1e-6

        if time_passed >= 0.25:
            previous_time = datetime.now()
            metrics = calc_metrics(faces[0], frame)

            if len(memory) != 17:
                memory.append(metrics)

            else:
                scaler.fit(memory)
                memory = scaler.transform(memory).tolist()

                prediction = model.predict(np.expand_dims(np.array(memory), axis=0))

                fainted = np.argmax(prediction)
                if fainted:
                    print('FAINTED')

                memory.pop(-1)

    cv2.imshow("Preview", frame)
    cv2.waitKey(1)

cap.release()
cv2.destroyAllWindows()
