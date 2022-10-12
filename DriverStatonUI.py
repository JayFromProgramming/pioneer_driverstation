import base64
import datetime
import logging
import os
import sys
import time
import threading

import roslibpy
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal

import cv2
import numpy as np

from PIL import Image
from PIL.ImageQt import ImageQt

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QMainWindow, QGridLayout
from PyQt5.QtGui import QIcon, QPixmap, QImage

import controller
from QT5_Classes.CannonUI import CannonUI
from QT5_Classes.PioneerUI import PioneerUI
from QT5_Classes.WebcamUI import WebcamWindow
from ROSInterface import ROSInterface
from RobotState import RobotState

from io import BytesIO

import logging

logging = logging.getLogger(__name__)


class DriverStationUI:

    def __init__(self, robot: ROSInterface):

        self.robot = robot
        self.last_redraw = 0  # type: int

        self.robot_state = robot.robot_state_monitor.state_watcher  # type: RobotState
        # self.xbox_controller = controller.XboxController()

        self.window = QMainWindow()
        self.window.setWindowTitle("Driver Station")
        self.window.resize(1080, 720)

        # self.layout.addWidget(WebcamWindow(self.robot))
        self.pioneer_ui = PioneerUI(self.robot, parent=self.window)
        self.cannon_ui = CannonUI(self.robot, parent=self.window)

        # Move the pioneer UI to the bottom left
        self.pioneer_ui.move(0, 480)

        # Move the cannon UI to the top left
        self.cannon_ui.move(0, 0)


        self.window.show()

    # def run(self):
    #     """Draw the HUD until the program exits"""
    #
    #     with Live(self.draw_table(), refresh_per_second=1, screen=True) as live:
    #         while self.robot.client.is_connected:
    #             if self.should_redraw():
    #                 live.update(self.draw_table())
    #             time.sleep(0.1)

    def controller_read_loop(self):
        """Loop for the joystick"""
        while self.robot.client.is_connected:
            # Apply deadbands to the joystick
            forward = self.xbox_controller.LeftJoystickY
            if abs(forward) < 0.15:
                forward = 0
            turn = self.xbox_controller.LeftJoystickX * -1
            if abs(turn) < 0.15:
                turn = 0

            self.robot.drive(forward, turn)

            if self.xbox_controller.A:
                self.robot.execute_service("my_p3at/enable_motors")
            if self.xbox_controller.B:
                self.robot.execute_service("my_p3at/disable_motors")

            time.sleep(0.2)

    # def should_redraw(self):
    #     """Check if the table has changed"""
    #     for state in self.robot_state.states():
    #         if state.has_changed():
    #             return True

    # def draw_table(self):
    #     """Draw the table"""
    #     table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    #     table.add_column("Topic", style="dim", width=24)
    #     table.add_column("Value", justify="center")
    #     for state in self.robot_state.states():
    #         # Exclude the image topic
    #         if state.name == "Img":
    #             continue
    #
    #         if not state.has_data:
    #             continue
    #         if state.not_single:  # If the value is not a single value, then make another table for it
    #             table.add_row(str(state), self.draw_sub_table(state.value))
    #         else:
    #             table.add_row(str(state), str(state.value))
    #     return table
    #
    # def draw_sub_table(self, values):
    #     """Draw a sub table"""
    #     table = Table(show_header=False, header_style="bold magenta", show_lines=True)
    #     for key, value in values.items():
    #         table.add_row(str(key), str(value))
    #     return table
