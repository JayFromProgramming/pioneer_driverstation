import os

from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QLabel


class ConnectionUI(QWidget):
    """
    This widget is how the target IP address is set and the connection is made and displayed
    """

    def __init__(self, robot, parent=None):
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(250, 200)
        self.robot = robot
        self.parent = parent

        if os.path.exists("configs/lastIP.txt"):
            with open("configs/lastIP.txt", "r") as f:
                last_ip = f.read()
        else:
            last_ip = ""

        self.header = QLabel("ROS Connection", self)
        self.header.setStyleSheet("font-weight: bold; font-size: 17px")
        self.header.move(int(self.width() / 2 - self.header.width() / 2) - 10, 0)
        self.ip_entry_label = QLabel("ROS HOST: ", self)
        self.ip_entry_label.setStyleSheet("font-weight: bold; font-size: 14px")
        # Create the IP address entry box and connect button
        self.ip_entry = QLineEdit(self)
        self.ip_entry.setText(last_ip)
        self.ip_entry.returnPressed.connect(self.start_connect)
        self.ip_entry.setFixedWidth(125)
        self.connect_button = QPushButton("Connect", self)
        self.connect_button.clicked.connect(self.start_connect)
        self.connect_button.setFixedWidth(100)

        # Set the layout of the UI
        self.ip_entry_label.move(0, 33)
        self.ip_entry.move(self.ip_entry_label.width() - 5, 30)
        self.connect_button.move(self.ip_entry_label.width() - 5, 60)

    def start_connect(self):
        ip = self.ip_entry.text()
        with open("configs/lastIP.txt", "w") as f:
            f.write(ip)
        # Lockout the connect button and entry box
        self.connect_button.clicked.disconnect()
        self.connect_button.clicked.connect(self.start_disconnect)
        self.connect_button.setText("Disconnect")
        self.ip_entry.setEnabled(False)
        self.robot.connect(address=self.ip_entry.text(), port=9090)

    def start_disconnect(self):
        self.robot.disconnect()
        self.ip_entry.setEnabled(True)
        self.connect_button.clicked.disconnect()
        self.connect_button.clicked.connect(self.start_connect)
        self.connect_button.setText("Connect")
        self.robot.disconnect()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
