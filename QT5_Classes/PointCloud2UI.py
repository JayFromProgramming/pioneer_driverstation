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

            self.dot_x_offset = 3
            self.dot_y_offset = 8

            # Create a 2D array to store the point cloud
            self.dots = []
            for i in range(16):
                dot = QLabel("•", parent=self.label)
                # self.dot.setFixedSize(5, 5)
                dot.setStyleSheet("background-color: transparent; color: green")
                dot.move(320 - self.dot_x_offset, 240 - self.dot_y_offset)
                self.dots.append(dot)

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
            for point in cloud:
                # Values are in meters from the center of the robot, so we need to convert them to pixels
                # Max range is 5 meters, so we need to scale the values to fit on the screen
                # raw_x = point["y"] - 0.5 if point["y"] > 0 else point["y"] + 0.5
                raw_y = point["x"] + 0.5 if point["x"] > 0 else point["x"] - 0.5
                x = (round(-point["y"] * 30) + 320) - self.dot_x_offset
                y = (round(-raw_y * 30) + 240) - self.dot_y_offset

                dot = self.dots[dot_num]

                # Move the dot to the correct location
                dot.move(x, y)
                dot_num += 1

        except Exception as e:
            logging.error(f"Error in process_cloud: {e} {traceback.format_exc()}")

    def draw_lines(self, qp):
        """Draw lines inbetween each adjacent point"""

        last_dot = self.dots[-1]  # Grab the last point in the list

        if not self.point_cloud_topic.has_data:
            qp.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.SolidLine))
        elif self.point_cloud_topic._last_update < time.time() - 5 or not self.point_cloud_topic._listener.is_subscribed:
            qp.setPen(QtGui.QPen(QtCore.Qt.darkYellow, 1, QtCore.Qt.SolidLine))
        else:
            qp.setPen(QtGui.QPen(QtCore.Qt.green, 1, QtCore.Qt.SolidLine))

        for dot in self.dots:
            # Draw a line from the last dot to the current dot
            start_x = last_dot.x() + self.dot_x_offset
            start_y = last_dot.y() + self.dot_y_offset
            end_x = dot.x() + self.dot_x_offset
            end_y = dot.y() + self.dot_y_offset
            qp.drawLine(start_x, start_y, end_x, end_y)
            last_dot = dot

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
