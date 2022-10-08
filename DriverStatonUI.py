import base64
import datetime
import logging
import os
import sys
import time
import threading

import rich
from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal
from rich.console import Console
from rich.table import Table
from rich import print as Print
from rich.panel import Panel
from rich.live import Live

import cv2
import numpy as np

from PIL import Image
from PIL.ImageQt import ImageQt

from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QIcon, QPixmap, QImage

import controller
from ROSInterface import ROSInterface
from RobotState import RobotState

from io import BytesIO

import logging

logging = logging.getLogger(__name__)

import roslibpy


def move(y, x):
    Print("\033[%d;%dH" % (y, x))


class ImageThread(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, robot):
        super().__init__()
        self.state = robot.robot_state_monitor.state_watcher
        self.running = True
        self.image = QImage("test.png")
        self.pixmap = QPixmap(self.image)
        self.timestamp = datetime.datetime.now()

    def run(self):

        while self.running:
            if self.state.state("Img").has_changed():
                try:
                    # Img data is pre-processed into a PIL image object
                    self.image = ImageQt(self.state.state("Img").image)
                    self.pixmap = QPixmap(self.image)
                    self.timestamp = self.state.state("Img").timestamp
                    # self.changePixmap.emit(self.image)

                except Exception as e:
                    logging.error(f"Error converting image: {e}")

    def stop(self):
        self.running = False


class WebcamWindow(QWidget):

    def __init__(self, robot):
        super().__init__()
        self.robot = robot
        self.title = f'Webcam: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.label = QLabel(self)
        self.label.move(0, 0)
        self.label.resize(640, 480)
        self.thread = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.thread = ImageThread(self.robot)
        # self.thread.changePixmap.connect(self.setImage)
        self.thread.start()
        self.repaint()
        self.show()

    def closeEvent(self, event):
        self.robot.stop()
        event.accept()

    def repaint(self) -> None:
        # Set the image to the label
        # super().repaint()
        self.label.setPixmap(self.thread.pixmap)
        self.setWindowTitle(f'Webcam: {self.thread.timestamp.strftime("%Y-%m-%d %H:%M:%S")}')

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        self.repaint()


class DriverStationUI:

    def __init__(self, robot: ROSInterface):
        self.console = Console()

        self.robot = robot
        self.last_redraw = 0  # type: int

        self.table = Table(show_header=True, header_style="bold magenta", show_lines=True)

        if self.console.is_dumb_terminal:
            self.console = Console(force_terminal=True)
            if self.console.is_dumb_terminal:
                raise RuntimeError("Terminal is not a TTY")

        self.robot_state = robot.robot_state_monitor.state_watcher  # type: RobotState
        self.xbox_controller = controller.XboxController()

        self.webcam_window = WebcamWindow(robot)
        self.joy_thread = threading.Thread(target=self.joystick_loop, daemon=True)
        self.joy_thread.start()
        self.webcam_threads = threading.Thread(target=self.webcam_thread, daemon=True)
        self.webcam_threads.start()

    def webcam_thread(self):
        """Thread for displaying the webcam"""
        while self.robot.client.is_connected:
            self.webcam_window.update()
            time.sleep(0.01)

    def build_up(self):
        """Build up the table"""
        for state in self.robot_state.states():
            self.table.add_row(str(state), str(state.value))

    def run(self):
        """Draw the HUD until the program exits"""

        with Live(self.draw_table(), refresh_per_second=1, screen=True) as live:
            while self.robot.client.is_connected:
                if self.should_redraw():
                    live.update(self.draw_table())
                time.sleep(0.1)

    def joystick_loop(self):
        """Loop for the joystick"""
        while self.robot.client.is_connected:
            # Apply deadbands to the joystick
            forward = self.xbox_controller.LeftJoystickY
            if abs(forward) < 0.1:
                forward = 0
            turn = self.xbox_controller.LeftJoystickX
            if abs(turn) < 0.1:
                turn = 0

            self.robot.key_board_publisher.publish(
                roslibpy.Message({"linear": {"x": forward * 1},
                                  "angular": {"z": turn * -1}}))
            time.sleep(0.2)

    def should_redraw(self):
        """Check if the table has changed"""
        for state in self.robot_state.states():
            if state.has_changed():
                return True

    def draw_table(self):
        """Draw the table"""
        table = Table(show_header=True, header_style="bold magenta", show_lines=True)
        table.add_column("Topic", style="dim", width=24)
        table.add_column("Value", justify="center")
        for state in self.robot_state.states():
            # Exclude the image topic
            if state.name == "Img":
                continue

            if not state.has_data:
                continue
            if state.not_single:  # If the value is not a single value, then make another table for it
                table.add_row(str(state), self.draw_sub_table(state.value))
            else:
                table.add_row(str(state), str(state.value))
        return table

    def draw_sub_table(self, values):
        """Draw a sub table"""
        table = Table(show_header=False, header_style="bold magenta", show_lines=True)
        for key, value in values.items():
            table.add_row(str(key), str(value))
        return table
