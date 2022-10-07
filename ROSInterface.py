import roslibpy
import threading
import logging

from RobotState import RobotState

logging = logging.getLogger(__name__)

topic_to_value = {
    # "/usb_cam/camera_info": "camera_info",
    # '/my_p3at/pose': 'pose',
    # '/my_p3at/parameter_updates': 'param',
    # '/my_p3at/parameter_descriptions': 'param',
    "/my_p3at/battery_voltage": "battery_voltage",
    # "/joint_states": "joint_states",
    "/my_p3at/motors_state": "motors_state",
    "/my_p3at/cmd_vel": "cmd_vel",
    # "/image_view/output": "Img"
}

acceleration = 100
turn_speed = 0.5


class RobotStateMonitor:

    def __init__(self, client):
        self.client = client
        self.state_watcher = RobotState()
        self._load_topics()
        self.setup_watchers()
        self.cached_topics = None  # type: dict or None

    def _load_topics(self):
        logging.info("RobotStateMonitor: Loading topics")
        topic_dict = {}
        for topic in self.client.get_topics():
            topic_type = self.client.get_topic_type(topic)
            topic_dict[topic] = {"name": topic, "type": topic_type}
            logging.info(f"Loaded topic {topic} of type {topic_type}")
        self.cached_topics = topic_dict
        logging.info("RobotStateMonitor: Loaded topics")

    def setup_watchers(self):
        logging.info("RobotStateMonitor: Setting up watchers")
        if self.cached_topics is None:
            self._load_topics()
        for val, name in topic_to_value.items():
            if val in self.cached_topics:
                self.setup_listener(name, val)
        logging.info("RobotStateMonitor: Set up watchers")

    def setup_listener(self, name, topic):
        message_type = self.cached_topics[topic]["type"]
        logging.info(f"Setting up listener for {topic} of type {message_type}")
        self.state_watcher.add_watcher(self.client, name, topic, message_type)


class ROSInterface:

    def __init__(self, address="localhost", port=9090, controller=None):
        self.client = None  # type: roslibpy.Ros or None
        self.address = address
        self.port = int(port)
        self.controller = controller
        self.robot_state_monitor = None  # type: RobotStateMonitor or None
        self.publisher = None  # type: roslibpy.Topic or None
        self.key_board_publisher = None  # type: roslibpy.Topic or None

    def connect(self):
        self.client = roslibpy.Ros(host=self.address, port=self.port)
        try:
            self.client.run()
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
        else:
            self.publisher = self._setup_publisher("/driver_station")
            self.key_board_publisher = self._setup_publisher("/my_p3at/cmd_vel", message_type="geometry_msgs/Twist")
            self.robot_state_monitor = RobotStateMonitor(self.client)

            return True

    def _setup_publisher(self, topic, message_type="std_msgs/String"):
        publisher = roslibpy.Topic(self.client, topic, message_type)
        publisher.advertise()
        logging.info(f" Publisher setup for topic: {topic}")
        return publisher

    def get_state(self) -> RobotStateMonitor:
        return self.robot_state_monitor

    def drive(self, forward=0.0, turn=0.0):
        logging.info(f"Driving forward: {forward} turn: {turn}")
        message = roslibpy.Message({"linear": {"x": forward}, "angular": {"z": turn}})
        self.key_board_publisher.publish(message)
