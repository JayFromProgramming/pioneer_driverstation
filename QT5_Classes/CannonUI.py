import traceback

from PyQt5 import QtCore, Qt
from PyQt5.QtCore import pyqtSlot, QLine, QRect, QPoint, QSize
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout, QPushButton, QLineEdit

import logging
import random

from ROS.RobotState import CannonCombinedTopic

logging = logging.getLogger(__name__)


# class SolenoidGraphic(QWidget):
#
#     def __init__(self, parent=None, robot=None, cannon_number=0):
#         super().__init__()
#         super().setParent(parent)
#         super().setFixedSize(75, 50)
#
#         self.robot = robot
#         self.state_watcher = robot.robot_state_monitor
#
#         # Set up the 3 lines that will be used to graphically represent the solenoid
#         painter = QPainter(self)
#         painter.setPen(QtCore.Qt.black)
#
#         # The first line is the A side of the solenoid
#         self.line_a = painter.drawLine(0, 25, 25, 0)
#         # The second line is the B side of the solenoid
#         self.line_b = painter.drawLine(75, 25, 100, 25)
#         # The third line is the line that either connects the A and B sides or is oriented vertically
#         # depending on if the solenoid is open or closed
#         self.action_line = painter.drawLine(25, 0, 75, 25)
#
#         rand = random.randint(0, 2)
#         if rand == 0:
#             self.state = "closed"
#         elif rand == 1:
#             self.state = "open"
#         else:
#             self.state = "fault"
#
#         # Start the update loop
#         self.timer = QtCore.QTimer()
#         self.timer.timeout.connect(self.update_loop)
#         self.timer.start(100)
#
#     def update_loop(self):
#         try:
#             if self.robot is not None:
#                 if self.robot.client.is_connected:
#                     if state := self.state_watcher.get_state(self.topic_name):
#                         if self.solenoid_name in state:
#                             if state[self.solenoid_name]:  # If the solenoid is open
#                                 # Draw the action line horizontally
#                                 self.state = "open"
#                             else:  # If the solenoid is closed, draw the action line vertically
#                                 self.state = "closed"
#                         else:  # If the solenoid is not in the state, draw the action line diagonally
#                             logging.error(f"Solenoid {self.solenoid_name} not found in state")
#                             self.state = "fault"
#                     else:
#                         logging.error(f"State for topic {self.topic_name} not found")
#                         self.state = "fault"
#                 else:
#                     self.state = "fault"
#         except Exception as e:
#             logging.error(f"Error updating solenoid graphic: {e}")
#             # Set the line to be diagonal if there is an error
#             self.state = "fault"
#
#     def paintEvent(self, event):
#         try:
#             painter = QPainter(self)
#             painter.setPen(QtCore.Qt.black)
#
#             # Set the line thickness to 5px
#             # painter.lin
#
#             painter.drawLine(0, 25, 25, 25)
#             painter.drawLine(50, 25, 75, 25)
#             match self.state:
#                 case "closed":
#                     painter.drawLine(50, 0, 50, 50)
#                 case "open":
#                     painter.drawLine(25, 25, 50, 25)
#                 case "fault":
#                     painter.setPen(QtCore.Qt.red)
#                     painter.drawLine(25, 0, 50, 50)
#                 case _:
#                     painter.drawLine(25, 0, 50, 25)
#
#         except Exception as e:
#             logging.error(f"Error setting solenoid graphic: {e}")


class AirTankElement(QWidget):
    """
    Shows the pressure in a particular air tank, represented as a horizontal bar that fits inside of a horizontal rectangle
    The tank pressure is displayed in the center of the tank graphic
    """

    def __init__(self, tank_name, tank_max_pressure, tank_min_pressure, tank_pressure, tank_pressure_unit,
                 parent=None, robot=None, cannon_number=0):
        super().__init__()
        super().setFixedSize(510, 140)
        super().setParent(parent)

        self.robot = robot
        self.state_watcher = self.robot.robot_state_monitor  # type: RobotStateMonitor

        self.tank_name = tank_name

        set_pressure_topic = robot.get_state(f"cannon_{cannon_number}_target_pressure")
        get_pressure_topic = robot.get_state(f"cannon_{cannon_number}_pressure")
        set_state_topic = robot.get_state(f"cannon_{cannon_number}_set_state")
        get_state_topic = robot.get_state(f"cannon_{cannon_number}_state")
        get_auto_topic = robot.get_state(f"cannon_{cannon_number}_auto")

        self.combined_topic = CannonCombinedTopic(set_pressure_topic, get_pressure_topic,
                                                  set_state_topic, get_state_topic,
                                                  get_auto_topic)

        self.tank_max_pressure = tank_max_pressure
        self.tank_min_pressure = tank_min_pressure
        self.tank_pressure = tank_pressure
        self.pressure_percent = 0
        self.tank_pressure_unit = tank_pressure_unit

        self.fault = True
        self.status = "Initializing"

        # Instantiate the UI graphics
        self.tank_box = QLabel(self)
        self.tank_box.setFixedSize(500, 60)
        self.tank_box.setStyleSheet("background-color: white; border: 2px solid black")

        self.tank_pressure_bar = QLabel(self.tank_box)
        self.tank_pressure_bar.setFixedSize(500, 60)
        self.tank_pressure_bar.setStyleSheet("background-color: green; border")

        # Setup the tank pressure text (in the center of the tank graphic)
        self.tank_pressure_text = QLabel("Unknown", parent=self.tank_box)

        # self.tank_pressure_text.setFixedSize(500, 60)
        self.tank_pressure_text.setStyleSheet("color: black; background-color: transparent; border: 0px;"
                                              "font-size: 20px; font-weight: bold")
        self.tank_pressure_text.setText(str(self.tank_pressure) + " " + self.tank_pressure_unit)
        # Move the tank pressure text to the center of the tank graphic
        self.tank_pressure_text.move(int(self.tank_box.width() / 2 - self.tank_pressure_text.width() / 2),
                                     int(self.tank_box.height() / 2 - self.tank_pressure_text.height() / 2))
        # self.tank_pressure_text.setAlignment(QtCore.Qt.AlignCenter)

        # Setup tank buttons
        self.auto_button = QPushButton("AUTO", parent=self)
        self.auto_button.setFixedSize(50, 30)
        self.auto_button.setCheckable(True)  # Make the button toggleable
        self.auto_button.clicked.connect(self.on_auto_button_clicked)

        self.fill_button = QPushButton("FILL", parent=self)
        self.fill_button.setFixedSize(50, 30)
        self.fill_button.setCheckable(True)  # Make the button toggleable
        self.fill_button.clicked.connect(self.on_fill_button_clicked)

        self.vent_button = QPushButton("VENT", parent=self)
        self.vent_button.setFixedSize(60, 30)
        self.vent_button.setCheckable(True)  # Make the button toggleable
        self.vent_button.clicked.connect(self.on_vent_button_clicked)

        self.pressure_set_input = QLineEdit(parent=self)
        self.pressure_set_input.setFixedSize(50, 30)
        self.pressure_set_input.setText(str(self.tank_pressure))
        self.pressure_set_input.returnPressed.connect(self.on_pressure_set)

        self.pressure_set_button = QPushButton("SET", parent=self)
        self.pressure_set_button.setFixedSize(50, 30)
        self.pressure_set_button.clicked.connect(self.on_pressure_set)

        self.arm_button = QPushButton("ARM", parent=self)
        self.arm_button.setFixedSize(50, 30)
        self.arm_button.setCheckable(True)  # Make the button toggleable
        self.arm_button.clicked.connect(self.on_arm_button_clicked)

        # Setup the in-flow and out-flow solenoid graphics

        # self.inflow_solenoid = SolenoidGraphic(parent=self, robot=self.robot, solenoid_name="inflow", topic_name=self.topic)
        # self.outflow_solenoid = SolenoidGraphic(parent=self, robot=self.robot, solenoid_name="outflow", topic_name=self.topic)

        # Instantiate the UI text
        self.tank_name_label = QLabel(f"{self.tank_name}: {self.status}", parent=self)
        # self.tank_name_label.setAlignment(
        self.tank_name_label.setStyleSheet("color: black; background-color: transparent; border: 0px;"
                                           "font-size: 20px; font-weight: bold")
        # Position the name text at the top and the left of the graphic

        # Set up the layout
        self.tank_name_label.move(0, 0)
        self.tank_box.move(10, 25)
        # self.tank_pressure_bar.move(10, 10)
        self.pressure_set_input.move(10, 85)
        self.pressure_set_button.move(65, 85)
        # The buttons are placed on the bottom right side of the tank graphic
        self.arm_button.move(260, 85)
        self.auto_button.move(320, 85)
        self.fill_button.move(380, 85)
        self.vent_button.move(440, 85)
        # The solenoid graphics are placed at the very ends of the tank graphic (left and right)
        # self.inflow_solenoid.move(10, 110 - self.inflow_solenoid.height())
        # self.outflow_solenoid.move(525 - self.outflow_solenoid.width(), 110 - self.outflow_solenoid.height())

        self.set_style_sheets()

        # Start the timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(150)

    def set_style_sheets(self):

        self.auto_button.setStyleSheet("background-color: grey; font-size: 15px;")
        self.fill_button.setStyleSheet("background-color: grey; font-size: 15px;")
        self.vent_button.setStyleSheet("background-color: grey; font-size: 15px;")
        self.arm_button.setStyleSheet("background-color: grey; font-size: 15px;")
        self.pressure_set_button.setStyleSheet("background-color: grey; font-size: 15px;")

    def set(self, state):
        value = state.value
        self.fault = value["fault"]
        self.tank_pressure = value["pressure"]
        self.pressure_percent = (self.tank_pressure - self.tank_min_pressure) / (self.tank_max_pressure - self.tank_min_pressure)
        self.repaint()

    def update_loop(self):
        try:
            if self.robot is not None:
                if self.robot.is_connected:
                    self.status = self.combined_topic.get_state()
                else:
                    self.fault = True
                    self.status = "No ROS"
            else:
                self.fault = True
                self.status = "No Robot"
        except Exception as e:
            logging.error(f"{e}")

    def paintEvent(self, event):
        super().paintEvent(event)

        # If the tank is in a fault state, then set the pressure bar to red

        self.tank_name_label.setText(f"{self.tank_name}: {self.status}")

        if self.fault:
            self.tank_pressure_bar.setStyleSheet("background-color: red")
            self.tank_pressure_bar.setFixedSize(500, 60)
        else:
            self.tank_pressure_bar.setStyleSheet("background-color: green")
            self.tank_pressure_bar.setFixedSize(500 * self.pressure_percent, 60)

    @pyqtSlot()
    def on_arm_button_clicked(self):
        if self.arm_button.isChecked():
            self.arm_button.setStyleSheet("background-color: green; font-size: 15px;")
        else:
            self.arm_button.setStyleSheet("background-color: grey; font-size: 15px;")

    @pyqtSlot()
    def on_auto_button_clicked(self):
        # Deselect the other buttons as they are mutually exclusive
        try:
            if self.auto_button.isChecked():
                self.combined_topic.send_command("set_auto")
            else:
                self.combined_topic.send_command("disable_auto")
        except Exception as e:
            logging.error(f"{e}")

    @pyqtSlot()
    def on_fill_button_clicked(self):
        # Deselect the other buttons as they are mutually exclusive
        try:
            if self.fill_button.isChecked():
                self.combined_topic.send_command("fill")
            else:
                self.combined_topic.send_command("idle")
        except Exception as e:
            logging.error(f"{e}")

    @pyqtSlot()
    def on_vent_button_clicked(self):
        # Deselect the other buttons as they are mutually exclusive
        try:
            if self.vent_button.isChecked():
                self.combined_topic.send_command("vent")
            else:
                self.combined_topic.send_command("idle")
        except Exception as e:
            logging.error(f"{e}")

    @pyqtSlot()
    def on_pressure_set(self):
        # Deselect the other buttons as they are mutually exclusive
        self.combined_topic.set_pressure(float(self.pressure_set_input.text()))


class CannonUI(QWidget):

    def __init__(self, robot, parent=None):
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(700, 440)
        self.parent = parent
        self.robot = robot

        self.tank1 = AirTankElement("Tank 1", 100, 0, 0, "PSI", parent=self, robot=self.robot,
                                    cannon_number=0)
        self.tank2 = AirTankElement("Tank 2", 100, 0, 0, "PSI", parent=self, robot=self.robot,
                                    cannon_number=1)

        self.solenoid_topic = self.robot.robot_state_monitor.get_state("solenoids")
        self.solenoids = {
            "fill": False,
            "vent": False,
            "cannon_1_fill": False,
            "cannon_1_shot": False,
            "cannon_2_fill": False,
            "cannon_2_shot": False
        }

        self.tank1.move(60, 0)

        self.tank2.move(60, 130)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(150)

    def set(self, tank1_pressure, tank2_pressure):
        self.tank1.set(tank1_pressure)
        self.tank2.set(tank2_pressure)

    def update_loop(self):
        try:
            raw_solenoids = self.solenoid_topic.value if self.solenoid_topic.value is not None else 0
            # Each solenoid is a bit in a 8 bit integer, so some bit shifting is required

            self.solenoids["fill"] = (raw_solenoids & 0b00000001) > 0
            self.solenoids["vent"] = (raw_solenoids & 0b00000010) > 0
            self.solenoids["cannon_1_fill"] = (raw_solenoids & 0b00000100) > 0
            self.solenoids["cannon_1_shot"] = (raw_solenoids & 0b00001000) > 0
            self.solenoids["cannon_2_fill"] = (raw_solenoids & 0b00010000) > 0
            self.solenoids["cannon_2_shot"] = (raw_solenoids & 0b00100000) > 0

        except Exception as e:
            logging.error(f"{e} {traceback.format_exc()}")

    def paintEvent(self, event):
        super().paintEvent(event)

        try:
            qp = QPainter(self)
            qp.setPen(QPen(QtCore.Qt.black, 2, QtCore.Qt.SolidLine))
            qp.begin(self)

            # Draw the supply solenoid
            if self.solenoids["fill"]:
                qp.setBrush(QColor(0, 255, 0))
            else:
                qp.setBrush(QColor(255, 0, 0))
            qp.drawRect(QRect(QPoint(60, 260), QSize(20, 20)))

            # Draw the vent solenoid
            if self.solenoids["vent"]:
                qp.setBrush(QColor(0, 255, 0))
            else:
                qp.setBrush(QColor(255, 0, 0))
            qp.drawRect(QRect(QPoint(60, 290), QSize(20, 20)))

            # Draw the cannon 1 fill solenoid
            if self.solenoids["cannon_1_fill"]:
                qp.setBrush(QColor(0, 255, 0))
            else:
                qp.setBrush(QColor(255, 0, 0))
            qp.drawRect(QRect(QPoint(self.tank1.x() - 15, self.tank1.y() + 45), QSize(20, 20)))

            # Draw the cannon 1 shot solenoid
            if self.solenoids["cannon_1_shot"]:
                qp.setBrush(QColor(0, 255, 0))
            else:
                qp.setBrush(QColor(255, 0, 0))
            qp.drawRect(QRect(QPoint(self.tank1.x() + self.tank1.width() + 5, self.tank1.y() + 45), QSize(20, 20)))

            # Draw the cannon 2 fill solenoid
            if self.solenoids["cannon_2_fill"]:
                qp.setBrush(QColor(0, 255, 0))
            else:
                qp.setBrush(QColor(255, 0, 0))
            qp.drawRect(QRect(QPoint(self.tank2.x() - 15, self.tank2.y() + 45), QSize(20, 20)))

            # Draw the cannon 2 shot solenoid
            if self.solenoids["cannon_2_shot"]:
                qp.setBrush(QColor(0, 255, 0))
            else:
                qp.setBrush(QColor(255, 0, 0))
            qp.drawRect(QRect(QPoint(self.tank2.x() + self.tank2.width() + 5, self.tank2.y() + 45), QSize(20, 20)))

            qp.end()
        except Exception as e:
            logging.error(f"{e} {traceback.format_exc()}")
