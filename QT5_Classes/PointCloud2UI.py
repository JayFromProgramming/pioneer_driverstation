import base64
import pypcd

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
from pypcd.pypcd import PointCloud


def pointcloud2_to_array(cloud_msg, squeeze=True):
    """Convert a sensor_msgs/PointCloud2 to a numpy record array."""
    pypcd_pointcloud = PointCloud.from_msg(cloud_msg)
    return pypcd_pointcloud.pc_data


class PointCloud2UI(QWidget):

    def __init__(self, robot, parent=None):
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(640, 480)
        self.robot = robot

        self.point_cloud_topic = self.robot.robot_state_monitor.state_watcher.state("sonar_pointcloud2")

        # Start the timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.render_2d_point_cloud)
        self.timer.start(1000)

    def render_2d_point_cloud(self):
        """Renders the 2D point cloud from the robot's sonar"""
        if not self.point_cloud_topic.exists:
            return
        base64_bytes = self.point_cloud_topic.value.encode('ascii')
        message_bytes = base64.b64decode(base64_bytes)
        cloud = pointcloud2_to_array(message_bytes)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
