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
        self.image = QImage("test.png")
        self.pixmap = QPixmap(self.image)
        self.timestamp = datetime.datetime.now()

    def run(self):

        while self.running:
            if self.state.state("Img").has_changed():
                try:
                    # Img data is pre-processed into a PIL image object
                    self.image = ImageQt(self.state.state("Img").image)
                    self.pixmap = QPixmap(self.image)
                    self.timestamp = self.state.state("Img").timestamp
                    # self.changePixmap.emit(self.image)

                except Exception as e:
                    logging.error(f"Error converting image: {e}")

    def stop(self):
        self.running = False


class WebcamWindow(QWidget):

    def __init__(self, robot):
        super().__init__()
        self.robot = robot
        self.title = f'Webcam: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.label = QLabel(self)
        self.label.move(0, 0)
        self.label.resize(640, 480)
        self.thread = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.thread = ImageThread(self.robot)
        # self.thread.changePixmap.connect(self.setImage)
        self.thread.start()
        self.repaint()
        self.show()

    def closeEvent(self, event):
        self.robot.stop()
        event.accept()

    def repaint(self) -> None:
        # Set the image to the label
        # super().repaint()
        self.label.setPixmap(self.thread.pixmap)
        self.setWindowTitle(f'Webcam: {self.thread.timestamp.strftime("%Y-%m-%d %H:%M:%S")}')

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        self.repaint()
