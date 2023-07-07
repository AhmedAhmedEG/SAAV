from PySide6.QtWidgets import QWidget, QFrame, QGridLayout, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSlider, QLineEdit
from PySide6.QtCore import QObject, Signal, Slot, QPointF, QTimer, QLineF, Qt, QRectF, QRunnable, QSize
from PySide6.QtGui import QPainter, QGuiApplication
from PySide6 import QtGui
import numpy as np
import math
import sys


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
WINDOW_SIZE = QSize(1080, 445)

RASPBERRY_PI_HOST = 'raspberrypi.local'
ESP_A_HOST = '192.168.43.106'
ESP_B_HOST = '192.168.43.198'


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


class CustomWindowFrame(QWidget):

    def __init__(self, title, closable=True, maximizable=True, minimizable=True, movable=True):
        super().__init__()
        self.setFixedHeight(30)

        self.movable = movable

        self.mouse_offset = None
        self.grabbed = False

        # Structure
        self.title_body = QGridLayout()
        self.title_body.setContentsMargins(6, 0, 0, 0)

        self.title_container = QWidget()
        self.title_container.setFixedHeight(15)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 6, 0, 2)

        # Components
        self.title = QLabel(title)
        self.title.setStyleSheet('font-size: 12px')

        self.minimize_btn = QPushButton('–')
        self.minimize_btn.setFixedWidth(20)
        self.minimize_btn.setFlat(True)

        self.maximize_btn = QPushButton('❒')
        self.maximize_btn.setFixedWidth(20)
        self.maximize_btn.setFlat(True)

        self.exit_btn = QPushButton('X')
        self.exit_btn.setFixedWidth(20)
        self.exit_btn.setFlat(True)

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        # Functionality
        self.minimize_btn.clicked.connect(self.minimize)
        self.maximize_btn.clicked.connect(self.maximize)
        self.exit_btn.clicked.connect(self.exit)

        # Assembly
        self.title_body.addWidget(self.title, 0, 0, alignment=Qt.AlignLeft)

        if minimizable:
            self.title_body.addWidget(self.minimize_btn, 0, 2, alignment=Qt.AlignRight)

        if maximizable:
            self.title_body.addWidget(self.maximize_btn, 0, 3, alignment=Qt.AlignRight)

        if closable:
            self.title_body.addWidget(self.exit_btn, 0, 4, alignment=Qt.AlignRight)

        self.title_body.setColumnStretch(1, 1)
        self.title_container.setLayout(self.title_body)

        self.body.addWidget(self.title_container)
        self.body.addWidget(self.separator)

        self.setLayout(self.body)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if not self.movable:
            return

        self.mouse_offset = event.pos()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)

        if not self.movable:
            return

        self.grabbed = False

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(event)

        if not self.movable:
            return

        if not self.grabbed and event.y() < self.height() and self.mouse_offset.y() < self.height():
            self.grabbed = True

        if self.grabbed:
            x, y = event.globalX(), event.globalY()
            self.parent().move(x - self.mouse_offset.x(), y - self.mouse_offset.y())

    def minimize(self):
        self.parent().resize(WINDOW_SIZE)

    def maximize(self):
        mw, mh = QGuiApplication.screens()[0].size().toTuple()

        if self.parent().size() == QSize(mw - 1, mh - 1):
            self.parent().resize(QSize(854, 480))
            self.parent().move(QGuiApplication.screens()[0].geometry().center() - self.parent().frameGeometry().center())

        else:
            self.parent().resize(QSize(mw - 1, mh - 1))
            self.parent().move(0, 0)

    @staticmethod
    def exit():
        sys.exit(0)


class Worker(QObject, QRunnable):
    start = Signal(int)

    def __init__(self, func=None, *args, **kwargs):
        QObject.__init__(self)
        QRunnable.__init__(self)

        self.func = func
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self):
        self.func(*self.args, **self.kwargs)

    def set_func(self, func):
        self.func = func


class CustomSlider(QWidget):
    value_changed = Signal()

    def __init__(self, mn, mx, default=None):
        super().__init__()

        # Structure
        self.body = QHBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)

        # Components
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.slider.setMinimum(mn)
        self.slider.setMaximum(mx)

        if default is not None:
            self.slider.setValue(default)

        self.counter_le = QLineEdit(str(self.slider.value()))
        self.counter_le.setAlignment(Qt.AlignCenter)
        self.counter_le.setFixedWidth(50)

        # Functionality
        self.slider.valueChanged.connect(self.value_changed)
        self.slider.valueChanged.connect(self.update_counter)

        self.counter_le.returnPressed.connect(lambda: self.slider.setValue(int(self.counter_le.text())))

        # Assembly
        self.body.addWidget(self.slider)
        self.body.addWidget(self.counter_le)

        self.setLayout(self.body)

    def update_counter(self):
        self.counter_le.setText(str(self.slider.value()))

    def __getattr__(self, item):
        return getattr(self.slider, item)


class HSeparator(QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)


class Joystick(QWidget):
    value_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(100, 150)
        self.center_offset = QPointF(0, 0)
        self.grabbed = False
        self.distance = 50

        QTimer.singleShot(0, lambda: setattr(self, 'center_offset', QPointF(self.width()/2, self.height()/2)))

    def mousePressEvent(self, e):
        self.grabbed = self.center_ellipse().contains(e.pos())
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.grabbed = False
        self.center_offset = QPointF(0, 0)
        self.update()
        super().mouseReleaseEvent(e)

    def mouseMoveEvent(self, e):

        if self.grabbed:
            line = QLineF(self.center(), e.pos())

            if line.length() > self.distance:
                line.setLength(self.distance)

            self.center_offset = line.p2()
            self.update()

            self.value_changed.emit()

        super().mouseMoveEvent(e)

    def paintEvent(self, event):
        painter = QPainter(self)
        bounds = QRectF(-self.distance, -self.distance, self.distance * 2, self.distance * 2).translated(self.center())

        painter.setPen(Qt.black)
        painter.setBrush(Qt.black)
        painter.drawEllipse(bounds)

        painter.setPen(Qt.black)
        painter.setBrush(Qt.red)
        painter.drawEllipse(self.center_ellipse())

    def center_ellipse(self):

        if self.grabbed:
            return QRectF(-20, -20, 40, 40).translated(self.center_offset)

        return QRectF(-20, -20, 40, 40).translated(self.center())

    def center(self):
        return QPointF(self.width()/2, self.height()/2)

    def value(self):
        norm_vector = QLineF(self.center(), self.center_offset)
        current_distance = norm_vector.length()
        angle = norm_vector.angle()

        distance = min(current_distance / self.distance, 1.0) * 100
        return int(angle), int(distance)
