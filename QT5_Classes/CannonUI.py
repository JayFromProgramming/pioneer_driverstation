from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout


class AirTankElement(QWidget):
    """
    Shows the pressure in a particular air tank, represented as a horizontal bar that fits inside of a horizontal rectangle
    The tank pressure is displayed in the center of the tank graphic
    """

    def __init__(self, tank_name, tank_max_pressure, tank_min_pressure, tank_pressure, tank_pressure_unit,
                 parent=None):
        super().__init__()
        super().setFixedSize(520, 100)
        super().setParent(parent)
        self.tank_name = tank_name
        self.tank_max_pressure = tank_max_pressure
        self.tank_min_pressure = tank_min_pressure
        self.tank_pressure = tank_pressure
        self.pressure_percent = 0
        self.tank_pressure_unit = tank_pressure_unit

        self.fault = True

        # Instantiate the UI graphics
        self.tank_box = QLabel()
        self.tank_box.setFixedSize(500, 60)
        self.tank_box.setStyleSheet("background-color: white; border: 1px solid black")

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

        # Instantiate the UI text
        self.tank_name_label = QLabel(self.tank_name, parent=self)
        # self.tank_name_label.setAlignment(
        self.tank_name_label.setStyleSheet("color: black")
        # Position the name text at the top and the left of the graphic
        self.tank_name_label.move(0, 60)

        # Set up the layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tank_box)
        self.layout.addWidget(self.tank_name_label, alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        super().setLayout(self.layout)

    def set(self, tank_pressure):
        self.fault = False
        self.tank_pressure = tank_pressure
        self.pressure_percent = (self.tank_pressure - self.tank_min_pressure) / (self.tank_max_pressure - self.tank_min_pressure)
        self.repaint()

    def paintEvent(self, event):
        super().paintEvent(event)

        # If the tank is in a fault state, then set the pressure bar to red

        if self.fault:
            self.tank_pressure_bar.setStyleSheet("background-color: red")
            self.tank_pressure_bar.setFixedSize(500, 60)
        else:
            self.tank_pressure_bar.setStyleSheet("background-color: green")
            self.tank_pressure_bar.setFixedSize(500 * self.pressure_percent, 60)


class CannonUI(QWidget):

    def __init__(self, robot, parent=None):
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(520, 200)
        self.parent = parent
        self.robot = robot

        self.tank1 = AirTankElement("Tank 1", 100, 0, 0, "PSI")
        self.tank2 = AirTankElement("Tank 2", 100, 0, 0, "PSI")

        # Set up the layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tank1)
        self.layout.addWidget(self.tank2)

    def set(self, tank1_pressure, tank2_pressure):
        self.tank1.set(tank1_pressure)
        self.tank2.set(tank2_pressure)

    def paintEvent(self, event):
        super().paintEvent(event)

