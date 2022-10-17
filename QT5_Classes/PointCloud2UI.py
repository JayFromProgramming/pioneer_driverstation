import base64
import logging
import struct
import traceback

import numpy as np

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QLabel

logging = logging.getLogger(__name__)


def _get_numpy_dtype(param):
    if param == 7:
        return np.float32
    elif param == 8:
        return np.float64
    elif param == 9:
        return np.int8
    elif param == 10:
        return np.uint8
    elif param == 11:
        return np.int16
    elif param == 12:
        return np.uint16
    elif param == 13:
        return np.int32
    elif param == 14:
        return np.uint32
    elif param == 15:
        return np.int64
    elif param == 16:
        return np.uint64
    else:
        raise Exception("Unknown data type")


def pointcloud2_to_array(msg_bytes, last_msg):
    """Convert a sensor_msgs/PointCloud2 to a numpy record array."""
    # Cannot use external librarys due to the lack of a pypi package
    # Print the hex values of the message with a row of 16 bytes
    # for i in range(0, len(msg_bytes), 16):
    #     print(' '.join('{:02x}'.format(x) for x in msg_bytes[i:i + 16]))

    # Each point is separated by 4 bytes of padding
    # Split the message by 4 bytes and remove the last element
    msg_bytes = msg_bytes.split(b'\x00\x00\x00\x00')[0:-1]

    # for point in msg_bytes:
    # print(' '.join('{:02x}'.format(x) for x in point))

    # if last_msg:
    #     # Print which bytes changed between the last message and this one
    #     point_num = 0
    #     # for point in msg_bytes:
    #         print(' '.join('{:02x}'.format(x) for x in point))
    #         # for i in range(0, len(point)):
    #         #     if point[i] != last_msg[point_num][i]:
    #         #         print(f"Point {point_num} byte {i} changed from {last_msg[point_num][i]} to {point[i]}")
    #         #
    #         # point_num += 1

    return msg_bytes


class PointCloud2UI(QWidget):

    def __init__(self, robot, parent=None):
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(640, 480)
        self.robot = robot

        self.point_cloud_topic = self.robot.robot_state_monitor.state_watcher.state("sonar_pointcloud2")

        self.last_cloud_array = None

        self.labels = []

        self.window = QWidget()

        for i in range(0, 16):
            label = QLabel(self.window)
            label.move(0, i * 30)
            label.setFixedSize(200, 20)
            self.labels.append(label)

        self.window.show()

        # Start the timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.render_2d_point_cloud)
        self.timer.start(1000)

    def render_2d_point_cloud(self):
        """Renders the 2D point cloud from the robot's sonar"""
        try:
            if not self.point_cloud_topic.exists:
                return
            base64_bytes = self.point_cloud_topic.value.encode('ascii')
            message_bytes = base64.b64decode(base64_bytes)
            cloud = pointcloud2_to_array(message_bytes, self.last_cloud_array)
            self.last_cloud_array = cloud
            # print(cloud)
        except Exception as e:
            logging.error(f"Error in render_2d_point_cloud: {e} {traceback.format_exc()}")

    def paintEvent(self, event) -> None:
        try:
            for i in range(0, 16):
                string = f"Point {i}: " + ' '.join('{:02x}'.format(x) for x in self.last_cloud_array[i])
                self.labels[i].setText(string)
        except Exception as e:
            logging.error(f"Error in paintEvent: {e} {traceback.format_exc()}")
