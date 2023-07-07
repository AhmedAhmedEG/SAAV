from PySide6.QtWidgets import QWidget, QTabWidget, QApplication, QVBoxLayout, QLineEdit, QFormLayout, QPushButton, QLabel, QCheckBox, QHBoxLayout
from Modules.Props import Joystick, HSeparator, CustomSlider, DISTANCE_PAIRS, calc_metrics, CustomWindowFrame, WINDOW_SIZE, Worker, RASPBERRY_PI_HOST, \
    ESP_A_HOST, ESP_B_HOST
from PySide6.QtGui import QPalette, QColor, QImage, QPixmap
from PySide6.QtCore import Signal, Qt, QTimer, QThreadPool
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from Modules.FaceMeshModule import FaceMeshDetector
from keras.models import load_model
from winsound import Beep
from PySide6 import QtGui
from copy import copy
import numpy as np
import requests
import time
import cv2


class RemoteControlTab(QWidget):
    update_viewer = Signal(object)

    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)
        self.running = False
        self.rc_awaiting_command = None
        self.avoidance_awaiting_command = None

        # Structure
        self.rc_body = QFormLayout()
        self.rc_body.setSpacing(15)

        self.rc_container = QWidget()

        self.body = QHBoxLayout()
        self.body.setSpacing(15)

        # Components
        self.frame_viewer = QLabel()
        self.joystick = Joystick(self)

        self.turn_sl = CustomSlider(mn=0, mx=180, default=90)
        self.speed_sl = CustomSlider(mn=0, mx=500, default=300)
        self.avoidance_cb = QCheckBox()

        self.address_a_le = QLineEdit()
        self.address_a_le.setText(f'http://{ESP_A_HOST}/control')

        self.address_b_le = QLineEdit()
        self.address_b_le.setText(f'http://{ESP_B_HOST}')

        self.start_btn = QPushButton('Start')
        self.start_btn.setFixedHeight(90)

        self.rc_thread_pool = QThreadPool()
        self.avoidance_thread_pool = QThreadPool()
        self.streamer_thread_pool = QThreadPool()

        # Functionality
        self.update_viewer.connect(lambda f: self.frame_viewer.setPixmap(QPixmap.fromImage(f)))
        self.joystick.value_changed.connect(lambda: self.command('js'))

        self.turn_sl.value_changed.connect(lambda: self.command('sl'))
        self.speed_sl.value_changed.connect(lambda: self.command('sl'))
        self.avoidance_cb.stateChanged.connect(lambda: self.command('sl'))

        self.start_btn.clicked.connect(self.switch)

        # Assembly
        self.body.addWidget(self.frame_viewer)

        self.rc_body.addRow('Turn', self.turn_sl)
        self.rc_body.addRow('Speed', self.speed_sl)
        self.rc_body.addRow('Avoidance', self.avoidance_cb)
        self.rc_body.addRow(self.joystick)

        self.rc_body.addRow(HSeparator())

        self.rc_body.addRow('Address A', self.address_a_le)
        self.rc_body.addRow('Address B', self.address_b_le)
        self.rc_body.addRow(self.start_btn)

        self.rc_container.setLayout(self.rc_body)
        self.body.addWidget(self.rc_container)

        self.setLayout(self.body)

        QTimer.singleShot(0, lambda: self.streamer_thread_pool.start(Worker(self.streamer)))

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:

        if e.key() == Qt.Key_W:
            self.speed_sl.setValue(self.speed_sl.value() + 1)
            e.accept()

        elif e.key() == Qt.Key_S:
            self.speed_sl.setValue(self.speed_sl.value() - 1)
            e.accept()

        elif e.key() == Qt.Key_A:
            self.turn_sl.setValue(self.turn_sl.value() + 45)
            e.accept()

        elif e.key() == Qt.Key_D:
            self.turn_sl.setValue(self.turn_sl.value() - 45)
            e.accept()

        elif e.key() == Qt.Key_Q:
            self.stop()
            e.accept()

        elif e.key() == Qt.Key_E:
            self.avoidance_cb.setChecked(not self.avoidance_cb.isChecked())
            e.accept()

        else:
            super().keyPressEvent(e)

    def stop(self):
        self.start_btn.setText('Start')

        self.turn_sl.setValue(90)
        self.speed_sl.setValue(0)
        self.avoidance_cb.setChecked(False)
        self.running = False

    def start(self):
        self.start_btn.setText('Stop')

        self.running = True
        self.command('sl')

    def switch(self):

        if self.running:
            self.stop()

        else:
            self.start()

    def command(self, m):
        s = self.speed_sl.value()

        if m == 'sl':
            a, av = self.turn_sl.value(), self.avoidance_cb.isChecked()

        else:
            a, av = self.joystick.value()[0], self.avoidance_cb.isChecked()

            if a > 180:
                a = 360 - a

        if self.running:

            if self.rc_thread_pool.activeThreadCount() == 0:
                self.rc_awaiting_command = None
                self.rc_thread_pool.start(Worker(self.rc_requester, a, s))

            else:
                self.rc_awaiting_command = (a, s)

            if self.avoidance_thread_pool.activeThreadCount() == 0:
                self.avoidance_awaiting_command = None
                self.avoidance_thread_pool.start(Worker(self.avoidance_requester, s, av))

            else:
                self.avoidance_awaiting_command = (s, av)

    def streamer(self):
        cap = cv2.VideoCapture(f'http://{RASPBERRY_PI_HOST}:8000/', cv2.CAP_FFMPEG)

        while True:

            if self.parent().parent().currentIndex() != 0:
                time.sleep(1)
                continue

            _, frame = cap.read()
            if frame is None:
                cap = cv2.VideoCapture(f'http://{RASPBERRY_PI_HOST}:8000/', cv2.CAP_FFMPEG)
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pyside_frame = QImage(rgb_frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)

            self.update_viewer.emit(pyside_frame)

    def rc_requester(self, a, s):
        requests.post(self.address_a_le.text(), json={'angle': a, 'speed': s})

        while self.rc_awaiting_command is not None:
            a, s = self.rc_awaiting_command
            self.rc_awaiting_command = None

            requests.post(self.address_a_le.text(), json={'angle': a, 'speed': s})

    def avoidance_requester(self, s, av):
        requests.post(self.address_b_le.text(), json={'speed': s, 'avoidance': av})

        while self.avoidance_awaiting_command is not None:
            s, av = self.avoidance_awaiting_command
            self.avoidance_awaiting_command = None

            requests.post(self.address_b_le.text(), json={'speed': s, 'avoidance': av})


class FaintingDetectionTab(QWidget):

    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.current_frame = None
        self.current_face = None

        self.detector = FaceMeshDetector(maxFaces=1, get_z=True)
        self.previous_metrics = None
        self.alarms = 0

        # Structure
        self.body = QVBoxLayout()

        # Components
        self.frame_viewer = QLabel()
        self.camera_timer = QTimer()
        self.detect_timer = QTimer()
        self.check_timer = QTimer()

        # Functionality
        self.camera_timer.timeout.connect(self.streamer)
        self.detect_timer.timeout.connect(self.detect_face)
        self.check_timer.timeout.connect(self.check_consciousness)

        # Assembly
        self.body.addWidget(self.frame_viewer)
        self.setLayout(self.body)

        self.camera_timer.start(50)
        self.detect_timer.start(500)
        self.check_timer.start(4000)

    def streamer(self):

        if self.parent().parent().currentIndex() != 1:
            self.alarms = 0
            return

        _, frame = self.cap.read()
        _, faces = self.detector.findFaceMesh(frame)

        self.current_frame = frame

        if faces:
            cv2.line(frame, faces[0][DISTANCE_PAIRS[0][0]][:2], faces[0][DISTANCE_PAIRS[0][1]][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][DISTANCE_PAIRS[1][0]][:2], faces[0][DISTANCE_PAIRS[1][1]][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][DISTANCE_PAIRS[2][0]][:2], faces[0][DISTANCE_PAIRS[2][1]][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][DISTANCE_PAIRS[3][0]][:2], faces[0][DISTANCE_PAIRS[3][1]][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][78][:2], faces[0][308][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][10][:2], faces[0][152][:2], (0, 255, 0), 2)
            cv2.line(frame, faces[0][234][:2], faces[0][454][:2], (0, 255, 0), 2)

            self.current_face = faces[0]

        else:
            self.current_face = None

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pyside_frame = QImage(rgb_frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
        self.frame_viewer.setPixmap(QPixmap.fromImage(pyside_frame))

    def detect_face(self):

        if self.parent().parent().currentIndex() != 1:
            self.alarms = 0
            return

        if self.current_face:
            metrics = calc_metrics(self.current_face, self.current_frame)

            if not self.previous_metrics:
                self.previous_metrics = copy(metrics)

            else:
                eyebrow_moved = not np.allclose((metrics[0], metrics[1]), (self.previous_metrics[0], self.previous_metrics[1]), atol=2.3)
                eyes_blinked = not np.allclose((metrics[2], metrics[3]), (self.previous_metrics[2], self.previous_metrics[3]), atol=1.4)
                lips_moved = abs(metrics[4] - self.previous_metrics[4]) > 0.7
                mouth_moved = abs(metrics[5] - self.previous_metrics[5]) > 2.7
                face_x_rotated = abs(metrics[6] - self.previous_metrics[6]) > 1.6
                face_y_rotated = abs(metrics[7] - self.previous_metrics[7]) > 0.7

                if (eyebrow_moved, eyes_blinked, lips_moved, mouth_moved, face_x_rotated, face_y_rotated).count(True) >= 1:

                    if self.alarms != 0:
                        self.alarms -= 1

                else:

                    if self.alarms != 10:
                        self.alarms += 1

            self.previous_metrics = copy(metrics)

        else:

            if self.alarms != 10:
                self.alarms += 1

    def check_consciousness(self):

        if self.parent().parent().currentIndex() != 1:
            self.alarms = 0
            return

        print(self.alarms)
        if self.alarms >= 3:
            print('Unconscious')
            window.remote_control_tab.start()
            window.remote_control_tab.speed_sl.setValue(0)

            Beep(1000, 4000)

            window.remote_control_tab.avoidance_cb.setChecked(True)
            window.remote_control_tab.speed_sl.setValue(321)

        self.alarms = 0


class LocationTab(QWidget):

    def __init__(self):
        super().__init__()

        # Structure
        self.body = QVBoxLayout()

        # Components
        self.view = QWebEngineView()
        self.view.page().load('https://maps.google.com')
        self.send_btn = QPushButton('Send')

        # Functionality
        self.view.page().featurePermissionRequested.connect(lambda o, f: self.view.page().setFeaturePermission(o, f, QWebEnginePage.PermissionGrantedByUser))
        self.send_btn.clicked.connect(self.start)

        # Assembly
        self.body.addWidget(self.view)
        self.body.addWidget(self.send_btn)
        self.setLayout(self.body)

    def start(self):
        window.remote_control_tab.running = True
        window.remote_control_tab.avoidance_cb.setChecked(True)
        window.remote_control_tab.speed_sl.setValue(321)


class SignDetectionTab(QWidget):
    update_viewer = Signal(object)

    def __init__(self):
        super().__init__()
        self.model = load_model('SignDetetctorOld.h5')

        # Structure
        self.body = QVBoxLayout()

        # Components
        self.streamer_thread_pool = QThreadPool()
        self.frame_viewer = QLabel()

        # Functionality
        self.update_viewer.connect(lambda f: self.frame_viewer.setPixmap(QPixmap.fromImage(f)))

        # Assembly
        self.body.addWidget(self.frame_viewer)
        self.setLayout(self.body)

        QTimer.singleShot(0, lambda: self.streamer_thread_pool.start(Worker(self.streamer)))

    def streamer(self):
        cap = cv2.VideoCapture(f'http://{RASPBERRY_PI_HOST}:8000/', cv2.CAP_FFMPEG)

        while True:

            if self.parent().parent().currentIndex() != 2:
                time.sleep(1)
                continue

            _, frame = cap.read()
            if frame is None:
                cap = cv2.VideoCapture(f'http://{RASPBERRY_PI_HOST}:8000/', cv2.CAP_FFMPEG)
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pyside_frame = QImage(rgb_frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)

            self.update_viewer.emit(pyside_frame)

            prediction = self.model.predict(np.expand_dims(rgb_frame, axis=0))
            print(np.argmax(prediction))


class ExternalController(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)

        # Structure
        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)

        self.container = QTabWidget()
        self.container.setTabPosition(QTabWidget.TabPosition.West)

        # Components
        self.remote_control_tab = RemoteControlTab()
        self.fainting_detection_tab = FaintingDetectionTab()
        self.sign_detection_tab = SignDetectionTab()
        # self.location_tab = LocationTab()

        # Assembly
        self.container.addTab(self.remote_control_tab, 'Remote Control')
        self.container.addTab(self.fainting_detection_tab, 'Fainting Detection')
        self.container.addTab(self.sign_detection_tab, 'Sign Detection')
        # self.container.addTab(self.location_tab, 'Location')

        self.body.addWidget(CustomWindowFrame('Safety-Aware Autonomous Vehicle'))
        self.body.addWidget(self.container)

        self.setLayout(self.body)


if '__main__' in __name__:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#353535"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#2a2a2a"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#353535"))

    app = QApplication([])
    app.setStyle('Fusion')
    app.setPalette(palette)
    app.setStyleSheet('''QWidget {color: #ffffff}
                             QWidget:!enabled {color: #808080}''')

    window = ExternalController()
    window.resize(WINDOW_SIZE)
    window.show()

    app.exec()
