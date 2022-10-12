from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class PioneerUI(QWidget):
    """
    Holds the pioneers UI elements, is then displayed in the main window via a layout
    Elements displayed: Commanded velocity, Motor State, Battery Voltage
    Velocity is displayed as an X-Y diagram with the X axis being the forward velocity and the Y axis being the rotational velocity
    Motor State is displayed as a text box with the current state of the motors
    Battery Voltage is displayed as a text box with the current voltage of the battery
    """

    def __init__(self, robot):
        super().__init__()
        self.robot = robot
        self.title = 'Pioneer'
        self.layout = QVBoxLayout()
        self.vel_graph = QLabel(self)
        self.vel_graph.move(0, 0)
        self.vel_graph.resize(120, 120)

        self.motor_state = QLabel(self)
        self.motor_state.move(0, 0)

        self.layout.addWidget(self.vel_graph)
        self.layout.addWidget(self.motor_state)
        self.setLayout(self.layout)

        self.initUI()
        self.robot.robot_state_monitor.state_watcher.state("Pioneer").add_callback(self.updateUI)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.show()

    def updateUI(self):
        pass



