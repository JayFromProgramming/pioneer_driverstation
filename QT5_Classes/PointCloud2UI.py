import base64
import logging
import struct
import subprocess
import time
import traceback

import numpy as np

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QOpenGLWidget

logging = logging.getLogger(__name__)


class PointCloud2UI(QOpenGLWidget):

    def __init__(self, robot, parent=None):
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(640, 500)
        try:
            self.robot = robot

            self.point_cloud_topic = self.robot.robot_state_monitor.state_watcher.state("sonar")

            # self.window = QWidget()
            # self.label = QLabel(self)
            # self.label.setFixedSize(640, 470)
            # self.label.setStyleSheet("background-color: black")
            # Add a paint event to the label
            # self.label.paintEvent = self.labelPaintEvent

            self.toggle_button = QPushButton("Toggle Scan", self)
            self.webcam_button = QPushButton("Open Webcam", self)
            self.webcam_button.clicked.connect(self.open_webcam)

            self.dot_x_offset = 2
            # self.dot_x_offset = 0
            self.dot_y_offset = 2
            # self.dot_y_offset = 0

            # Create a 2D array to store the point cloud
            self.dots = []
            for i in range(16):
                self.dots.append((320, 240, 0))
                # self.dot.setFixedSize(5, 5)
                # dot.setStyleSheet("background-color: transparent; color: green")
                # dot.move(320 - self.dot_x_offset, 240 - self.dot_y_offset)
                # self.dots.append(dot)

            self.toggle_button.clicked.connect(self.toggle)
            self.toggle_button.move(10, 471)
            self.webcam_button.move(120, 471)

            # self.window.show()

            # Start the timer
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.process_2d_point_cloud)
            self.timer.start(100)
        except Exception as e:
            logging.error(f"Error in __init__: {e} {traceback.format_exc()}")

    @pyqtSlot()
    def open_webcam(self):
        """Open an ffplay window"""
        try:
            subprocess.Popen(["ffplay", "-x", "480", "-y", "320", "-f", "mjpeg", f"http://{self.robot.address}:8080"])
        except Exception as e:
            logging.error(f"Error in open_webcam: {e} {traceback.format_exc()}")

    def process_cloud(self, cloud: list):
        try:
            # Move each dot to a location on the screen
            dot_num = 0
            for point in cloud:
                # Values are in meters from the center of the robot, so we need to convert them to pixels
                # Max range is 5 meters, so we need to scale the values to fit on the screen
                # raw_x = point["y"] - 0.5 if point["y"] > 0 else point["y"] + 0.5
                raw_y = point["x"] + 0.2 if point["x"] > 0 else point["x"] - 0.2
                x = (round(-point["y"] * 40) + 320) - self.dot_x_offset
                y = (round(-raw_y * 40) + 240) - self.dot_y_offset

                # calculate the distance from the center of the robot
                distance = np.sqrt(point["x"] ** 2 + point["y"] ** 2)
                if distance > 5:
                    self.dots[dot_num] = (x, y, 0)
                    # self.dots[dot_num].setStyleSheet("background-color: transparent; color: red")
                elif distance < 1:
                    self.dots[dot_num] = (x, y, 2)
                    # self.dots[dot_num].setStyleSheet("background-color: transparent; color: darkorange")
                else:
                    self.dots[dot_num] = (x, y, 1)
                    # self.dots[dot_num].setStyleSheet("background-color: transparent; color: green")

                # dot = self.dots[dot_num]

                # Move the dot to the correct location
                # dot.move(x, y)
                dot_num += 1

        except Exception as e:
            logging.error(f"Error in process_cloud: {e} {traceback.format_exc()}")

    def draw_lines(self, qp):
        """Draw lines inbetween each adjacent point"""

        for dot in self.dots:
            if dot[2] == 0:
                qp.setBrush(QtGui.QColor(255, 0, 0))
            elif dot[2] == 1:
                qp.setBrush(QtGui.QColor(0, 255, 0))
            elif dot[2] == 2:
                qp.setBrush(QtGui.QColor(255, 165, 0))
            qp.drawEllipse(dot[0], dot[1], 5, 5)
            # Fill the dot with the correct color

        # last_dot = self.dots[-1]  # Grab the last dot that is not red
        for dot in self.dots:
            # if dot.styleSheet() == "background-color: transparent; color: red":
            #     continue
            if dot[2] == 0:
                continue
            last_dot = dot

        if not self.point_cloud_topic.has_data:
            qp.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.SolidLine))
        elif self.point_cloud_topic._last_update < time.time() - 5 or not self.point_cloud_topic._listener.is_subscribed:
            qp.setPen(QtGui.QPen(QtCore.Qt.darkYellow, 1, QtCore.Qt.SolidLine))
        else:
            qp.setPen(QtGui.QPen(QtCore.Qt.green, 1, QtCore.Qt.SolidLine))

        for dot in self.dots:
            # Draw a line from the last dot to the current dot

            # If the dot is red, don't draw a line
            # if dot.styleSheet() == "background-color: transparent; color: red":
            #     continue
            if dot[2] == 0:
                continue
            # elif dot.styleSheet() == "background-color: transparent; color: darkorange"\
            #         and last_dot.styleSheet() == "background-color: transparent; color: darkorange":
            #     qp.setPen(QtGui.QPen(QtCore.Qt.darkYellow, 1, QtCore.Qt.SolidLine))

            start_x = last_dot[0] + self.dot_x_offset
            start_y = last_dot[1] + self.dot_y_offset
            end_x = dot[0] + self.dot_x_offset
            end_y = dot[1] + self.dot_y_offset
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
        else:
            super().update()

    def paintGL(self) -> None:
        try:
            # Clear the previous image
            # self.label.clear()
            qp = QtGui.QPainter()
            qp.begin(self)
            self.draw_lines(qp)
            qp.end()
        except Exception as e:
            logging.error(f"Error in paintEvent: {e} {traceback.format_exc()}")
        # else:
        #     print("Painted")
