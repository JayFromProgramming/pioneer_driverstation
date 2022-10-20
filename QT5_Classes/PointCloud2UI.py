import base64
import logging
import struct
import time
import traceback

import numpy as np

from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton

logging = logging.getLogger(__name__)


class PointCloud2UI(QWidget):

    def __init__(self, robot, parent=None):
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(640, 500)
        try:
            self.robot = robot

            self.point_cloud_topic = self.robot.robot_state_monitor.state_watcher.state("sonar")

            # self.window = QWidget()
            self.label = QLabel(self)
            self.label.setFixedSize(640, 470)
            self.label.setStyleSheet("background-color: black")
            # Add a paint event to the label
            self.label.paintEvent = self.labelPaintEvent

            self.toggle_button = QPushButton("Toggle Scan", self)

            # self.dot_x_offset = 3
            # self.dot_y_offset = 8
            self.dot_x_offset = 0
            self.dot_y_offset = 0

            # Create a 2D array to store the point cloud
            self.captures = []
            self.fused_captures = []
            self.last_position = (0, 0)
            self.last_angle = 0

            self.toggle_button.clicked.connect(self.toggle)
            self.toggle_button.move(10, 471)

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
            points = []

            pose = self.robot.robot_state_monitor.state_watcher.state("odometry").value
            if pose is None:
                return
            current_position = (pose['pose']['pose']['position']['x'] / 1000, pose['pose']['pose']['position']['y'] / 1000)
            current_orientation = pose['pose']['pose']['orientation']['z']

            # Generate a rotation and translation matrix
            rotation_matrix = np.array([[np.cos(current_orientation), -np.sin(current_orientation)],
                                        [np.sin(current_orientation), np.cos(current_orientation)]])
            translation_matrix = np.array([current_position[0] * 100, current_position[1] * 100]) + np.array([320, 240])

            for point in cloud:
                # Values are in meters from the center of the robot, so we need to convert them to pixels
                # Max range is 5 meters, so we need to scale the values to fit on the screen
                # raw_x = point["y"] - 0.5 if point["y"] > 0 else point["y"] + 0.5
                raw_x = point["y"]
                raw_y = point["x"] + 0.2 if point["x"] > 0 else point["x"] - 0.2

                # Apply the rotation and translation matrix
                point_position = np.dot(rotation_matrix, np.array([raw_x * 100, raw_y * 100])) + translation_matrix

                # calculate the distance from the center of the robot
                distance = np.sqrt(point["x"] ** 2 + point["y"] ** 2)

                if distance > 5:
                    points.append((None, None))
                else:
                    points.append((point_position[0], point_position[1]))
                # Move the dot to the correct location
                # dot.move(x, y)
                dot_num += 1

            # If there is more than 20 captures, remove the oldest one
            if len(self.captures) > 20:
                self.captures.pop(0)
            self.captures.append(points)

        except Exception as e:
            logging.error(f"Error in process_cloud: {e} {traceback.format_exc()}")

    def fuse_captures(self) -> list:
        """Fuses the captures into a single list of points, using the current position and orientation of the robot
        to calculate the correct position of each point relative to the current position of the robot"""
        try:
            if len(self.captures) == 0:
                return []

            # Create a list to store the points
            points = []

            # Loop through each capture
            for capture in self.captures:
                # Loop through each point in the capture
                for point in capture:
                    # If the point is None, add it to the list and continue
                    if point[0] is None:
                        # points.append((None, None))
                        continue

                    # Because the robot is moving, we need to calculate the position of each point relative to the current
                    # position of the robot

                    # Generate a rotation and translation matrix using the last position of the robot
                    rotation_matrix = np.array([[np.cos(self.last_angle), -np.sin(self.last_angle)],
                                                [np.sin(self.last_angle), np.cos(self.last_angle)]])
                    translation_matrix = np.array([self.last_position[0] * 100, self.last_position[1] * 100]) \
                                         + np.array([320, 240])

                    # Apply the rotation and translation matrix to the point
                    point_position = np.dot(rotation_matrix, np.array([point[0], point[1]])) + translation_matrix

                    # Add the point to the list
                    points.append((point_position[0], point_position[1]))

            return points
        except Exception as e:
            logging.error(f"Error in fuse_captures: {e} {traceback.format_exc()}")
            return []

    def draw_lines(self, qp):
        """Draw lines inbetween each adjacent point"""

        if not self.point_cloud_topic.has_data:
            qp.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.SolidLine))
        elif self.point_cloud_topic._last_update < time.time() - 5 or not self.point_cloud_topic._listener.is_subscribed:
            qp.setPen(QtGui.QPen(QtCore.Qt.darkYellow, 1, QtCore.Qt.SolidLine))
        else:
            qp.setPen(QtGui.QPen(QtCore.Qt.green, 1, QtCore.Qt.SolidLine))

        points = self.fused_captures
        if len(points) == 0:
            return

        # last_point = points[-1]

        for point in points:
            # Draw a line from the last dot to the current dot

            # Create a rotation matrix and a translation matrix to draw the points relative to the robot

            x = int(point[0])
            y = int(point[1])

            qp.drawLine(x, y, x, y)

        qp.setPen(QtGui.QPen(QtCore.Qt.gray, 1, QtCore.Qt.DashLine))
        qp.drawLine(320, 0, 320, 480)
        qp.drawLine(0, 240, 640, 240)

    def toggle(self):
        try:
            logging.info("Toggling PointCloud2UI")
            if self.point_cloud_topic._listener.is_subscribed:
                self.point_cloud_topic.unsubscribe()
                self.timer.stop()
            else:
                self.point_cloud_topic.resubscribe()
                self.timer.start()
        except Exception as e:
            logging.error(f"Error in toggle: {e} {traceback.format_exc()}")

    def process_2d_point_cloud(self):
        """Renders the 2D point cloud from the robot's sonar"""
        try:
            if self.point_cloud_topic is None or not self.point_cloud_topic.has_data:
                return

            # print(self.point_cloud_topic.value["points"])
            self.process_cloud(self.point_cloud_topic.value["points"])
            self.fused_captures = self.fuse_captures()

        except Exception as e:
            logging.error(f"Error in render_2d_point_cloud: {e} {traceback.format_exc()}")

    def labelPaintEvent(self, event) -> None:
        try:
            # Clear the previous image
            self.label.clear()
            qp = QtGui.QPainter()
            qp.begin(self.label)
            self.draw_lines(qp)
            qp.end()
        except Exception as e:
            logging.error(f"Error in paintEvent: {e} {traceback.format_exc()}")
