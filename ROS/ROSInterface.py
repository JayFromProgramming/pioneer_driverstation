import time

import roslibpy
import threading
import logging

from ROS.RobotState import RobotState

logging = logging.getLogger(__name__)

topic_to_name = {
    # "/usb_cam/camera_info": "camera_info",
    # '/my_p3at/pose': 'pose',
    # '/my_p3at/parameter_updates': 'param',
    # '/my_p3at/parameter_descriptions': 'param',
    "/my_p3at/battery_voltage": "battery_voltage",
    # "/joint_states": "joint_states",
    "/my_p3at/motors_state": "motors_state",
    "/my_p3at/cmd_vel": "cmd_vel",
    # "my_p3at/sonar": "sonar",
    # "/my_p3at/sonar_pointcloud2": "sonar_pointcloud2",
    "/camera/image/compressed": "Img",
    "/cannon/angle": "cannon_angle",
    "/cannon/tanks/0": "cannon_tank_0",
    "/cannon/tanks/1": "cannon_tank_1",
    "/cannon/pneumatics": "pnemumatics"
}


class RobotStateMonitor:

    def __init__(self, client):
        self.client = client
        self.state_watcher = RobotState()

        if self.client is None:
            return

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
        for val, name in topic_to_name.items():
            if val in self.cached_topics:
                self.setup_listener(name, val)
        logging.info("RobotStateMonitor: Set up watchers")

    def setup_listener(self, name, topic):
        message_type = self.cached_topics[topic]["type"]
        logging.info(f"Setting up listener for {topic} of type {message_type}")
        self.state_watcher.add_watcher(self.client, name, topic, message_type)

    def get_state(self, name):
        return self.state_watcher.state(name)

    def get_states(self):
        return self.state_watcher.states()

    def is_state_available(self, name):
        return name in self.state_watcher.states()

    def get_topic_status(self, topic):
        return self.get_state()


class ROSInterface:

    def __init__(self):
        self.client = None  # type: roslibpy.Ros or None
        self.address = None
        self.port = None
        self.robot_state_monitor = RobotStateMonitor(self.client)
        self.publisher = None  # type: roslibpy.Topic or None
        self.key_board_publisher = None  # type: roslibpy.Topic or None
        self.background_thread = None  # type: threading.Thread or None

        self.target_topics = topic_to_name.keys()

    @property
    def is_connected(self):
        return self.client.is_connected if self.client is not None else False

    def connect(self, address, port):
        logging.info("Connecting to ROS bridge")
        self.address = address
        self.port = port
        self.background_thread = threading.Thread(target=self._connect, daemon=True)
        self.background_thread.start()

    def terminate(self):
        logging.info("Terminating ROSInterface")
        self.client.terminate()
        self.background_thread.join()

    def _maintain_connection(self):
        self._connect()
        while True:
            time.sleep(1)
            if not self.client.is_connected:
                logging.info("Connection to ROS bridge lost, reconnecting")
                self._connect()

    def _connect(self):
        self.client = roslibpy.Ros(host=self.address, port=self.port)
        try:
            self.client.run()
        except Exception as e:
            logging.error(f"Connection to ROS bridge failed: {e}")
            self.client.terminate()
        else:
            self.publisher = self._setup_publisher("/driver_station")
            self.key_board_publisher = self._setup_publisher("/my_p3at/cmd_vel", message_type="geometry_msgs/Twist")
            self.robot_state_monitor = RobotStateMonitor(self.client)
            print(self.get_services())

    def _setup_publisher(self, topic, message_type="std_msgs/String"):
        publisher = roslibpy.Topic(self.client, topic, message_type)
        publisher.advertise()
        logging.info(f" Publisher setup for topic: {topic}")
        return publisher

    def get_state(self) -> RobotStateMonitor:
        return self.robot_state_monitor

    def drive(self, forward=0.0, turn=0.0):
        message = roslibpy.Message({"linear": {"x": forward}, "angular": {"z": turn}})
        self.key_board_publisher.publish(message)

    def get_services(self):
        return self.client.get_services()

    def execute_service(self, name, *args):
        service = roslibpy.Service(self.client, name, 'std_srvs/Empty')
        request = roslibpy.ServiceRequest()
        service.call(request, *args)
