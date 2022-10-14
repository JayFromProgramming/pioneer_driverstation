import os
import subprocess

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QSizePolicy
import psutil

import logging

logging = logging.getLogger(__name__)


def decode_netsh_output(output):
    output = output.decode("utf-8")
    output = output.split("\r\n")[1:]
    # Remove any empty lines
    output = [line for line in output if line]

    # First line is "There is 1 interface on the system:"
    info_dict = {}
    output = [line.split(":") for line in output]
    for line in output:
        if len(line) == 2:
            info_dict[line[0].strip()] = line[1].strip()
        else:
            info_dict[line[0].strip()] = None

    return info_dict


class PioneerConnectionWidget(QWidget):

    def __init__(self, robot, parent=None):
        """Displays info of the pioneer's connection via the ROS bridge"""
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(350, 200)

        self.robot = robot
        self.header = QLabel("Pioneer Connection", parent=self)
        self.header.setStyleSheet("color: red; font-size: 17px; font-weight: bold; alignment: center")
        self.network_name = QLabel(f"Network Name:     {['-' for _ in range(10)]}", parent=self)
        self.network_name.setStyleSheet("color: red; font-size: 14px; font-weight: bold; alignment: center")
        self.signal_strength = QLabel(f"Signal Strength: {['-' for _ in range(10)]}", parent=self)
        self.signal_strength.setStyleSheet("color: red; font-size: 14px; font-weight: bold; alignment: center")
        self.ip_address = QLabel(f"IP Address: {['-' for _ in range(10)]}", parent=self)
        self.ip_address.setStyleSheet("color: red; font-size: 14px; font-weight: bold; alignment: center")
        self.usage = QLabel(f"Usage: {['-' for _ in range(10)]}", parent=self)
        self.usage.setStyleSheet("color: red; font-size: 14px; font-weight: bold; alignment: center")

        self.network_text = "No connection"
        self.usage_text = "No connection"
        self.ip_address_text = "No connection"
        self.signal_strength_text = "No connection"

        # Move all the labels
        self.header.move(0, 0)
        self.network_name.move(0, 20)
        self.signal_strength.move(0, 35)
        self.ip_address.move(0, 50)
        self.usage.move(0, 65)

        # Setup the timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_info)
        self.timer.start(1000)

    def update_info(self):
        """Updates the info of the driver station's connection"""
        # Get the info from the command line
        try:
            if self.robot.client.is_connected:
                if client := self.robot.robot_state_monitor.state_watcher.state("pioneer_conn"):
                    info_dict = client.get_info()
                    self.set_color("black")
                    self.network_text = info_dict["SSID"]
                    self.signal_strength_text = info_dict["Signal"]
                    self.ip_address_text = info_dict["IPv4 Address"]
                    self.usage_text = info_dict["Usage"]
                else:
                    self.set_color("red")
                    self.network_text = "No topic"
                    self.signal_strength_text = "No topic"
                    self.ip_address_text = "No topic"
                    self.usage_text = "No topic"
            else:
                self.set_color("red")
                self.network_text = "No connection"
                self.signal_strength_text = "No connection"
                self.ip_address_text = "No connection"
                self.usage_text = "No connection"
        except Exception as e:
            logging.error(f"Error updating pioneer connection info: {e}")
        else:  # Format the each line so it appears like its a table with the names flush left and the values flush right

            # First get how long the longest name is
            # Then get the longest value
            longest_value = max([len(value) for value in
                                 [self.network_text, self.signal_strength_text, self.ip_address_text, self.usage_text]])
            # Then format the text
            self.network_name.setText(f"<pre>Network Name:    {self.network_text.rjust(longest_value)}</pre>")
            self.signal_strength.setText(f"<pre>Signal Strength: {self.signal_strength_text.rjust(longest_value)}</pre>")
            self.ip_address.setText(f"<pre>IP Address:      {self.ip_address_text.rjust(longest_value)}</pre>")
            self.usage.setText(f"<pre>Usage:           {self.usage_text.rjust(longest_value)}</pre>")

        self.repaint()

    def set_color(self, color):
        """Sets the color of the widget"""
        self.network_name.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; alignment: center")
        self.signal_strength.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; alignment: center")
        self.ip_address.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; alignment: center")
        self.usage.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; alignment: center")


class DriverStationConnectionWidget(QWidget):

    def __init__(self, parent=None):
        """Displays info of the driver station's connection via the ROS bridge"""
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(350, 200)

        self.header = QLabel("Driver Station Connection", parent=self)
        self.header.setStyleSheet("font-size: 17px; font-weight: bold; alignment: center")
        self.network_name = QLabel("Network Name: ", parent=self)
        self.network_name.setStyleSheet("color: black; font-size: 14px; font-weight: bold; alignment: center")
        self.sig_strength = QLabel("Signal Strength: ", parent=self)
        self.sig_strength.setStyleSheet("color: black; font-size: 14px; font-weight: bold; alignment: center")
        self.ip_address = QLabel("IP Address: ", parent=self)
        self.ip_address.setStyleSheet("color: black; font-size: 14px; font-weight: bold; alignment: center")
        self.usage = QLabel("Usage: ", parent=self)
        self.usage.setStyleSheet("color: black; font-size: 14px; font-weight: bold; alignment: center")
        self.update_info()

        self.network_name_text = "No connection"
        self.sig_strength_text = "No connection"
        self.ip_address_text = "No connection"
        self.usage_text = "No connection"

        # Set all the labels to be flush with the right side of the widget
        self.header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.network_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sig_strength.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ip_address.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.usage.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Move all the labels
        self.header.move(0, 0)
        self.network_name.move(0, 20)
        self.sig_strength.move(0, 35)
        self.ip_address.move(0, 50)
        self.usage.move(0, 65)

        # Start the timer to update the info
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_info)
        self.timer.start(1000)

    def update_info(self):
        try:
            # Get the network name (Sadly will need to use subprocess to get this)

            # Check os to see if it is windows or linux
            if os.name == 'nt':
                network = subprocess.check_output("netsh wlan show interfaces")
                network = decode_netsh_output(network)
                if "SSID" in network:
                    self.network_name_text = network["SSID"]
                    self.sig_strength_text = network["Signal"]
                    self.ip_address_text = psutil.net_if_addrs()['Wi-Fi'][1][1]
                    self.usage_text = f"{network['Receive rate (Mbps)']}\u2193/{network['Transmit rate (Mbps)']}\u2191"
                else:
                    self.network_name_text = "No connection"
                    self.sig_strength_text = "0%"
                    self.ip_address_text = "No connection"
                    self.usage_text = "0\u2193/0\u2191"

            else:
                network = subprocess.check_output("iwgetid")
                network = network.decode("utf-8")
                network = network.split("\n")

            longest_value = max([len(value) for value in
                                 [self.network_name_text, self.sig_strength_text, self.ip_address_text, self.usage_text]])
            # Then format the text
            self.network_name.setText(f"<pre>Network Name:    {self.network_name_text.rjust(longest_value)}</pre>")
            self.sig_strength.setText(f"<pre>Signal Strength: {self.sig_strength_text.rjust(longest_value)}</pre>")
            self.ip_address.setText(f"<pre>IP Address:      {self.ip_address_text.rjust(longest_value)}</pre>")
            self.usage.setText(f"<pre>Usage:           {self.usage_text.rjust(longest_value)}</pre>")

            self.repaint()
        except Exception as e:
            logging.error(f"Error updating driver station connection info: {e}")


class ConnectionUI(QWidget):
    def __init__(self, robot, parent=None):
        super().__init__()
        super().setParent(parent)
        self.robot = robot
        super().setFixedSize(500, 200)

        # Set up the info text

        # Set up the layout
        self.pioneer = PioneerConnectionWidget(self.robot, self)
        self.driver_station = DriverStationConnectionWidget(self)

        # Move the widgets to the correct position
        self.pioneer.move(0, 0)
        self.driver_station.move(0, 100)
