import base64
import logging
import struct
import traceback

import numpy as np

from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QLabel

logging = logging.getLogger(__name__)


class PointCloud2UI(QWidget):

    def __init__(self, robot, parent=None):
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(640, 480)
        try:
            self.robot = robot

            self.point_cloud_topic = self.robot.robot_state_monitor.state_watcher.state("sonar")

            # Create a 2D array to store the point cloud
            self.point_cloud = np.zeros((480, 640), dtype=np.uint8)

            # self.window = QWidget()
            self.label = QLabel(self)
            self.label.setFixedSize(640, 480)

            # self.window.show()

            # Start the timer
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.process_2d_point_cloud)
            self.timer.start(100)
        except Exception as e:
            logging.error(f"Error in __init__: {e} {traceback.format_exc()}")

    def process_cloud(self, cloud: list):
        try:
            # Clear the point cloud
            self.point_cloud.fill(0)
            for point in cloud:
                x = int(point["x"] * 10)
                y = int(point["y"] * 10)

                # Center the values at the center of the array
                x += 320
                y += 240

                # Set the pixel to white
                self.point_cloud[x, y] = 255
        except Exception as e:
            logging.error(f"Error in process_cloud: {e} {traceback.format_exc()}")

    def render_2d_point_cloud(self):
        """Display the 2d array"""
        try:

            # Convert the array to a QImage
            image = QImage(self.point_cloud, 640, 480, QImage.Format_Grayscale8)

            # Convert the QImage to a QPixmap
            pixmap = QPixmap(image)

            # Display the QPixmap
            self.label.setPixmap(pixmap)

        except Exception as e:
            logging.error(f"Error in render_2d_point_cloud: {e} {traceback.format_exc()}")

    def process_2d_point_cloud(self):
        """Renders the 2D point cloud from the robot's sonar"""
        try:
            if not self.point_cloud_topic.exists:
                return

            # print(self.point_cloud_topic.value["points"])
            self.process_cloud(self.point_cloud_topic.value["points"])

        except Exception as e:
            logging.error(f"Error in render_2d_point_cloud: {e} {traceback.format_exc()}")

    def paintEvent(self, event) -> None:
        try:
            self.render_2d_point_cloud()
        except Exception as e:
            logging.error(f"Error in paintEvent: {e} {traceback.format_exc()}")
