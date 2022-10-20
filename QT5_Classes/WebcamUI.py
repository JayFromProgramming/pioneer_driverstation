import datetime
import logging

import requests as requests
from PIL.ImageQt import ImageQt
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QWidget, QLabel, QOpenGLWidget


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

            self.video_stream = QMediaPlayer(self, QMediaPlayer.VideoSurface)

            self.video_player = QVideoWidget(self)
            self.video_player.resize(640, 480)
            self.video_player.move(0, 0)
            self.video_stream.error.connect(self.handleError)
            self.video_stream.setVideoOutput(self.video_player)

            self.info_label = QLabel(self)
            self.info_label.setStyleSheet("QLabel { background-color : black; color : white; }")
            self.info_label.resize(640, 20)
            self.info_label.move(0, 460)

            self.robot.hook_on_ready(self.on_ready)

            self.video_player.show()

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
        net_resource = QtCore.QUrl(f"http://{ip}:8080")
        print(f"Setting video stream to {net_resource}")
        media_content = QMediaContent(net_resource)
        print(f"Media content: {media_content}")
        print(f"Media: {self.video_stream.isVideoAvailable()}")
        self.video_stream.setMedia(media_content)
        # print(f"{self.video_stream.state()}")
        self.video_stream.play()
        # print(f"{self.video_stream.state()}")

        print("Playing video")

    def closeEvent(self, event):
        self.robot.stop()
        event.accept()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        self.info_label.setText(f"Webcam: {self.robot.address}; {self.video_stream.state()}")

    def handleError(self):
        print(self.video_stream.errorString())
