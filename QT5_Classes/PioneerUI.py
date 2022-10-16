import traceback

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QMainWindow, QGridLayout
import logging

logging = logging.getLogger(__name__)


class CmdVelWidget(QWidget):
    """Display the X, Y values as a dot in a 1:1 window"""

    def __init__(self, size=100, expected_bounds=(-1, 1), parent=None):
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(size + 30, size + 30)

        self.size = size
        self.expected_bounds = expected_bounds

        # Set up the background box
        self.box = QWidget(parent=self)
        self.box.setFixedSize(size, size)
        self.box.setStyleSheet("background-color: black")

        # Set up the UI name text
        self.name = QLabel("Velocity CMD", parent=self)
        self.name.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        # Position the name text at the top of the box and center it
        # Set text color to white
        self.name.setStyleSheet("color: green; font-size: 14px; font-weight: bold; alignment: center")

        # Set up the value text
        self.value = QLabel("0, 0", parent=self)
        # Position the value text at the centered bottom of the widget
        # Set text color to white
        self.value.setStyleSheet("color: green; font-size: 14px; font-weight: bold; alignment: center")

        # Set up the dot
        self.dot = QLabel("•", parent=self.box)
        # self.dot.setFixedSize(5, 5)
        self.dot.setStyleSheet("background-color: transparent; color: green")

        # Set up the layout
        self.box.move(15, 15)
        self.name.move(15, 0)
        self.value.move(int(15 - self.value.width() / 2), self.box.height() + 15)

        self.x = 0  # Center the dot
        self.y = 0  # Center the dot

    def set(self, x, y):
        # print(f"Setting to {x}, {y}")
        self.x = int(x)
        self.y = int(y)
        # self.repaint()

    def paintEvent(self, event):
        try:
            super().paintEvent(event)

            # Make zero the center of the box not the top left
            x = (self.x * self.size / 2) + self.size / 2
            y = (self.y * self.size / 2) + self.size / 2

            # Move the dot to where it should be
            point = QtCore.QPoint(int(x - self.dot.width() / 2), int(y - self.dot.height() / 2))
            self.dot.move(point)

            # Update the value text
            self.value.setText(f"{self.x}, {self.y}")
        except Exception as e:
            logging.error(f"Error in paintEvent: {e}")


class PioneerUI(QWidget):
    """
    Holds the pioneers UI elements, is then displayed in the main window via a layout
    Elements displayed: Commanded velocity, Motor State, Battery Voltage
    Velocity is displayed as an X-Y diagram with the X axis being the forward velocity and the Y axis being the rotational velocity
    Motor State is displayed as a text box with the current state of the motors
    Battery Voltage is displayed as a text box with the current voltage of the battery
    """

    def __init__(self, robot, parent=None):
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(300, 300)

        self.robot = robot

        # Instantiate the UI graphics
        self.vel_graph = CmdVelWidget(100, (-1, 1))
        self.motor_state = QLabel("Motor State: ")
        self.battery_voltage = QLabel("Battery Voltage: ")

        # Set the layout of the UI
        self.layout = QGridLayout(self)
        self.layout.addWidget(self.vel_graph, 0, 0, 1, 2)
        self.layout.addWidget(self.motor_state, 1, 0, 1, 2)
        self.layout.addWidget(self.battery_voltage, 2, 0, 1, 2)
        self.setLayout(self.layout)

        # Set the update timer
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.updateUI)
        self.update_timer.start(1000)

    def updateUI(self):
        # Update the velocity graph with the current commanded velocity
        try:
            cmd_vel = self.robot.robot_state_monitor.state_watcher.state("cmd_vel")
            if cmd_vel is not None:
                # print(f"cmd_vel {cmd_vel.value}")
                if cmd_vel.value is not None:
                    self.vel_graph.set(cmd_vel.value['linear']['x'], cmd_vel.value['angular']['z'])
                # print(cmd_vel.value)
                else:
                    self.vel_graph.set(0, 0)
            else:
                self.vel_graph.set(0, 0)
        except Exception as e:
            logging.error(f"Error updating velocity graph: {e} {traceback.format_exc()}")
            self.vel_graph.set(0, 0)

        # Update the motor state with the current motor state
        try:
            motor_state = self.robot.robot_state_monitor.state_watcher.state("motors_state")
            if motor_state is not None:
                self.motor_state.setText(f"Motor State: {motor_state.value}")
            else:
                self.motor_state.setText("Motor State: Unknown")
        except Exception as e:
            logging.error(f"Error updating motor state: {e}")
            self.motor_state.setText("Motor State: Error")

        # Update the battery voltage with the current battery voltage
        try:
            battery_voltage = self.robot.robot_state_monitor.state_watcher.state("battery_voltage")
            if battery_voltage is not None:
                self.battery_voltage.setText(f"Battery Voltage: {battery_voltage.value}")
            else:
                self.battery_voltage.setText("Battery Voltage: Unknown")
        except Exception as e:
            logging.error(f"Error updating battery voltage: {e}")
            self.battery_voltage.setText("Battery Voltage: Error")
