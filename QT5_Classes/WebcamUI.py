import datetime
import logging

from PIL.ImageQt import ImageQt
from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QLabel


class ImageThread(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, robot):
        super().__init__()
        self.state = robot.robot_state_monitor.state_watcher
        self.running = True
        self.image = QImage("no_webcam.png")
        self.pixmap = QPixmap(self.image)
        self.timestamp = datetime.datetime.now()
        self.info = "No Image"

    def run(self):
        try:
            while self.running:
                if self.state.state("Img") is None:
                    self.info = "No Webcam Topic To Pull From"
                    self.image = QImage("no_webcam.png")
                    break
                if self.state.state("Img").has_changed():
                    try:
                        # Img data is pre-processed into a PIL image object
                        self.image = ImageQt(self.state.state("Img").image)
                        self.pixmap = QPixmap(self.image)
                        self.timestamp = self.state.state("Img").timestamp
                        # self.changePixmap.emit(self.image)
                        self.info = None
                    except Exception as e:
                        logging.error(f"Error converting image: {e}")
                        self.info = f"Error converting image: {e}"
        except Exception as e:
            logging.error(f"Error in ImageThread: {e}")
            self.info = f"Error in ImageThread: {e}"
            self.image = QImage("no_webcam.png")

    def stop(self):
        self.running = False


class WebcamWindow(QWidget):

    def __init__(self, robot, parent=None):
        """Is a widget within the main window that displays the webcam image"""

        super().__init__()
        super().setParent(parent)
        super().setFixedSize(640, 480)
        self.robot = robot
        self.parent = parent

        self.image_label = QLabel(self)
        self.image_label.resize(640, 480)
        self.image_label.move(0, 0)

        self.info_label = QLabel(self)
        self.info_label.setStyleSheet("QLabel { background-color : black; color : white; }")
        self.info_label.resize(640, 20)
        self.info_label.move(0, 460)

        self.thread = None
        self.initUI()

    def initUI(self):
        self.thread = ImageThread(self.robot)
        # self.thread.changePixmap.connect(self.setImage)
        # self.thread.start()
        self.repaint()

    def closeEvent(self, event):
        self.robot.stop()
        event.accept()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        self.image_label.setPixmap(self.thread.pixmap)
        if self.thread.info is not None:
            self.info_label.setText(self.thread.info)
        else:
            self.info_label.setText(f"Last Image: {self.thread.timestamp}")
