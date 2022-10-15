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

        self.header = QLabel("ROS Connection", self)
        # Create the IP address entry box and connect button
        self.ip_entry = QLineEdit(self)
        self.ip_entry.setText(last_ip)
        self.ip_entry.returnPressed.connect(self.start_connect)
        self.ip_entry.setFixedWidth(125)
        self.connect_button = QPushButton("Connect", self)
        self.connect_button.clicked.connect(self.start_connect)
        self.connect_button.setFixedWidth(100)

        # Set the layout of the UI
        self.ip_entry.move(20, 20)
        self.connect_button.move(20, 50)

    def start_connect(self):
        ip = self.ip_entry.text()
        with open("configs/lastIP.txt", "w") as f:
            f.write(ip)
        # Lockout the connect button and entry box
        self.connect_button.setEnabled(False)
        self.ip_entry.setEnabled(False)
        self.robot.connect(address=self.ip_entry.text(), port=9090)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
