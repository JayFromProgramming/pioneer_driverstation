from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QMainWindow
import logging

logging = logging.getLogger(__name__)


class CmdVelWidget(QWidget):
    """Display the X, Y values as a dot in a 1:1 window"""

    def __init__(self, size=100, expected_bounds=(-1, 1), parent=None):
        super().__init__()
        super().setParent(parent)
        # super().setFixedSize(size + 15, size + 15)

        self.size = size
        self.expected_bounds = expected_bounds

        # Set up the UI name text
        self.name = QLabel("Pioneer Vel Command", parent=self)
        self.name.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        # Position the name text at the top of the box and center it
        self.name.move(0, 0)
        # Set text color to white
        self.name.setStyleSheet("color: green")

        # Set up the value text
        self.value = QLabel("0, 0", parent=self)
        self.value.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)
        # Position the value text at the centered bottom of the widget
        self.value.move(0, size)
        # Set text color to white
        self.value.setStyleSheet("color: green")

        # Set up the background box
        self.box = QWidget(self)
        self.box.setFixedSize(size, size)
        self.box.setStyleSheet("background-color: black")

        # Set up the dot
        self.dot = QLabel(self.box)
        self.dot.setFixedSize(5, 5)
        self.dot.setStyleSheet("background-color: red")

        # Set up the layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.box)
        self.layout.addWidget(self.name)
        self.layout.addWidget(self.value)

        super().setLayout(self.layout)

        self.x = 0  # Center the dot
        self.y = 0  # Center the dot

    def set(self, x, y):
        self.x = x
        self.y = y
        self.repaint()

    def paintEvent(self, event):
        super().paintEvent(event)

        # Scale the values to the size of the box
        x = self.x * self.size
        y = self.y * self.size

        # Move the dot to where it should be
        self.dot.move(x, y)

        # Update the value text
        self.value.setText(f"{self.x}, {self.y}")


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
        self.motor_state = QLabel()
        self.battery_voltage = QLabel()

        # Set the layout of the UI
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.vel_graph)
        self.layout.addWidget(self.motor_state)
        self.layout.addWidget(self.battery_voltage)
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
                self.vel_graph.set(cmd_vel.value[0], cmd_vel.value[1])
            else:
                self.vel_graph.set(0, 0)
        except Exception as e:
            logging.error(f"Error updating velocity graph: {e}")
            self.vel_graph.set(0, 0)
