import base64
import logging
import struct
import traceback

import numpy as np

from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QLabel

logging = logging.getLogger(__name__)


def render_2d_point_cloud():
    """Display the 2d array"""
    try:
        pass
    except Exception as e:
        logging.error(f"Error in render_2d_point_cloud: {e} {traceback.format_exc()}")


class PointCloud2UI(QWidget):

    def __init__(self, robot, parent=None):
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(640, 480)
        try:
            self.robot = robot

            self.point_cloud_topic = self.robot.robot_state_monitor.state_watcher.state("sonar")

            # self.window = QWidget()
            self.label = QLabel(self)
            self.label.setFixedSize(640, 480)
            self.label.setStyleSheet("background-color: black")

            # Create a 2D array to store the point cloud
            self.dots = []
            for i in range(16):
                dot = QLabel("•", parent=self.label)
                # self.dot.setFixedSize(5, 5)
                dot.setStyleSheet("background-color: transparent; color: green")
                dot.move(320, 240)
                self.dots.append(dot)

            # self.window.show()

            # Start the timer
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.process_2d_point_cloud)
            self.timer.start(100)
        except Exception as e:
            logging.error(f"Error in __init__: {e} {traceback.format_exc()}")

    def process_cloud(self, cloud: list):
        try:
            # Move each dot to a location on the screen
            dot_num = 0
            for point in cloud:
                # Values are in meters from the center of the robot, so we need to convert them to pixels
                # Max range is 5 meters, so we need to scale the values to fit on the screen
                x = int(-point["y"] * 25) + 320
                y = int(point["x"] * 25) + 240

                dot = self.dots[dot_num]

                # Move the dot to the correct location
                dot.move(x, y)
                dot_num += 1

        except Exception as e:
            logging.error(f"Error in process_cloud: {e} {traceback.format_exc()}")

    def toggle(self):
        logging.info("Toggling PointCloud2UI")
        if self.point_cloud_topic._listener.is_subscribed:
            self.point_cloud_topic.unsubscribe()
        else:
            self.point_cloud_topic.resubscribe()

    def process_2d_point_cloud(self):
        """Renders the 2D point cloud from the robot's sonar"""
        try:
            if self.point_cloud_topic is None or not self.point_cloud_topic.has_data:
                return

            # print(self.point_cloud_topic.value["points"])
            self.process_cloud(self.point_cloud_topic.value["points"])

        except Exception as e:
            logging.error(f"Error in render_2d_point_cloud: {e} {traceback.format_exc()}")

    def paintEvent(self, event) -> None:
        try:
            render_2d_point_cloud()
        except Exception as e:
            logging.error(f"Error in paintEvent: {e} {traceback.format_exc()}")
