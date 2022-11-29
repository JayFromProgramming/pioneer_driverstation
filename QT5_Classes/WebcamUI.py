import datetime
import logging

import requests as requests
from PIL.ImageQt import ImageQt
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtQuick import QQuickItem
from PyQt5.QtWidgets import QWidget, QLabel, QOpenGLWidget

# from QT5_Classes.WebcamTest import NetworkMJPGImage


class WebcamWindow(QWidget):

    def __init__(self, robot, parent=None):
        """Is a widget within the main window that displays the webcam image"""
        try:
            super().__init__()
            super().setParent(parent)
            super().setFixedSize(640, 480)
            self.robot = robot
            self.parent = parent

            self.image_label = QLabel(self)
            self.image_label.resize(640, 480)
            self.image_label.move(0, 0)

            # self.quick_item = QQuickItem()
            # self.streamer = NetworkMJPGImage()

            self.info_label = QLabel(self)
            self.info_label.setStyleSheet("QLabel { background-color : black; color : white; }")
            self.info_label.resize(640, 20)
            self.info_label.move(0, 460)

            self.robot.hook_on_ready(self.on_ready)

            # Start timer
            # self.timer = QtCore.QTimer()
            # self.timer.timeout.connect(self.fetch_image)
            # self.timer.start(1000)
        except Exception as e:
            logging.error(f"Error initializing webcam: {e}")

    def on_ready(self):
        # Set teh video widget address
        ip = self.robot.address
        # print(f"{self.video_stream.state()}")
        # The stream is of type mjpeg
        net_resource = QtCore.QUrl(f"http://{ip}:8080")
        self.streamer.setSourceURL(net_resource)
        self.streamer.start()
        logging.info(f"Webcam stream started")

    def paintEvent(self, event):
        try:
            painter = QtGui.QPainter(self)
            self.streamer.paint(painter)
        except Exception as e:
            logging.error(f"Error in paintEvent: {e}")
