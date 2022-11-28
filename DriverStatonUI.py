import time
import threading

from PyQt5.QtWidgets import QMainWindow

import controller
from QT5_Classes.CannonUI import CannonUI
from QT5_Classes.ConnectionUI import ConnectionUI
from QT5_Classes.PointCloud2UI import PointCloud2UI
from QT5_Classes.SignalUI import SignalUI
from QT5_Classes.PioneerUI import PioneerUI
from QT5_Classes.TopicStatusUI import TopicUI
from QT5_Classes.WebcamUI import WebcamWindow
from ROS.ROSInterface import ROSInterface
from ROS.RobotState import RobotState

import logging

logging = logging.getLogger(__name__)


class DriverStationUI:

    def __init__(self, robot: ROSInterface):

        self.robot = robot
        self.last_redraw = 0  # type: int

        self.robot_state = robot.robot_state_monitor.state_watcher  # type: RobotState
        try:
            self.xbox_controller = controller.XboxController()
        except Exception as e:
            logging.error(f"Error initializing controller: {e}")
            self.xbox_controller = None

        self.window = QMainWindow()
        self.window.resize(1280, 720)

        self.connection_ui = ConnectionUI(self.robot, self.window)
        self.pioneer_ui = PioneerUI(self.robot, parent=self.window)
        self.cannon_ui = CannonUI(self.robot, parent=self.window)
        self.signal_info = SignalUI(self.robot, self.window)
        self.topic_info = TopicUI(self.robot, self.window)
        # self.webcam = WebcamWindow(self.robot, self.window)
        self.sonar_view = PointCloud2UI(self.robot, parent=self.window)

        # Move the pioneer UI to the bottom left
        self.pioneer_ui.move(0, 480)
        # Move the cannon UI to the top left
        self.cannon_ui.move(0, 0)
        # Move the webcam to the top right
        # self.webcam.move(640, 0)
        self.sonar_view.move(640, 0)
        # Move the signal info to the bottom right
        # self.signal_info.move(self.window.width() - self.signal_info.width(), 20 + self.webcam.height())
        self.signal_info.move(self.window.width() - self.signal_info.width(), 20 + self.sonar_view.height())

        # Move the topic UI to the left of the signal info
        self.topic_info.move(self.signal_info.x() - self.topic_info.width(), self.signal_info.y())
        # self.topic_info.move(self.window.width() - self.topic_info.width(), 20 + self.sonar_view.height())

        # Move the connection UI to left of the topic UI
        self.connection_ui.move(self.topic_info.x() - self.connection_ui.width(), self.topic_info.y())

        self.window.show()

        threading.Thread(target=self.controller_read_loop, daemon=True).start()

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
        # Read the controller while the window is open
        try:
            while True:
                # Apply deadbands to the joystick
                forward = self.xbox_controller.LeftJoystickY * -1
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
                if self.xbox_controller.X:
                    self.sonar_view.toggle()
                if self.xbox_controller.Y:
                    self.robot.execute_service("/can/fire")

                if self.xbox_controller.LeftBumper:
                    if not self.cannon_ui.tank1.cannonArmed():
                        self.cannon_ui.tank1.armDisarm(True)
                else:
                    if self.cannon_ui.tank1.cannonArmed():
                        self.cannon_ui.tank1.armDisarm(False)

                if self.xbox_controller.RightBumper:
                    if not self.cannon_ui.tank2.cannonArmed():
                        self.cannon_ui.tank2.armDisarm(True)
                else:
                    if self.cannon_ui.tank2.cannonArmed():
                        self.cannon_ui.tank2.armDisarm(False)

                time.sleep(0.1)
        except Exception as e:
            logging.error(f"Error reading controller: {e}")
            self.robot.drive(0, 0)
