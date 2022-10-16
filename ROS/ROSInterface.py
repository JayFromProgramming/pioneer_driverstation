import time

import roslibpy
import threading
import logging

from ROS.RobotState import RobotState, SmartTopic

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
    "/pioneer/conn_stats": "conn_stats",
    "/camera/image/compressed": "Img",
    "/cannon/angle": "cannon_angle",
    "/cannon/tanks/0": "cannon_tank_0",
    "/cannon/tanks/1": "cannon_tank_1",
    "/cannon/pneumatics": "pnemumatics",
    "/ext/compressor/voltage": "compressor_voltage",
}

topic_targets = [
    SmartTopic("battery_voltage", "/my_p3at/battery_voltage"),
    SmartTopic("motors_state", "/my_p3at/motors_state"),
    SmartTopic("cmd_vel", "/my_p3at/cmd_vel", allow_update=True),
    SmartTopic("conn_stats", "/pioneer/conn_stats"),
    SmartTopic("Img", "/camera/image/compressed"),
    SmartTopic("cannon_angle", "/cannon/angle"),
    SmartTopic("cannon_tank_0", "/cannon/tanks/0"),
    SmartTopic("cannon_tank_1", "/cannon/tanks/1"),
    SmartTopic("pneumatics", "/cannon/pneumatics"),
    SmartTopic("compressor_voltage", "/ext/compressor/voltage"),
]


class RobotStateMonitor:

    def __init__(self, client):
        self.client = client
        self.state_watcher = RobotState()

        self.cached_topics = {}
        self.setup_watchers()

    def _load_topics(self):
        logging.info("RobotStateMonitor: Loading topics")
        topic_dict = {}
        for topic in self.client.get_topics():
            if topic in self.cached_topics:
                continue
            topic_type = self.client.get_topic_type(topic)
            topic_dict[topic] = {"name": topic, "type": topic_type}
            logging.info(f"Loaded topic {topic} of type {topic_type}")
        self.cached_topics = topic_dict
        logging.info("RobotStateMonitor: Loaded topics")

    def set_client(self, client):
        self.client = client
        for smart_topic in topic_targets:
            smart_topic.set_client(self.client)

    def setup_watchers(self):
        for smart_topic in topic_targets:
            self.state_watcher.add_watcher(smart_topic)

    # def setup_listener(self, name, topic):
    #     message_type = self.cached_topics[topic]["type"]
    #     logging.info(f"Setting up listener for {topic} of type {message_type}")
    #     self.state_watcher.add_watcher

    def get_state(self, name):
        return self.state_watcher.state(name)

    def get_states(self):
        return self.state_watcher.states()

    def is_state_available(self, name):
        return name in self.state_watcher.states()


class ROSInterface:

    def __init__(self):
        self.client = None  # type: roslibpy.Ros or None
        self.address = None
        self.port = None
        self.robot_state_monitor = RobotStateMonitor(self.client)
        self.background_thread = None  # type: threading.Thread or None

        self.target_topics = topic_to_name.keys()
        self.smart_topics = topic_targets

    @property
    def is_connected(self):
        return self.client.is_connected if self.client is not None else False

    def connect(self, address, port):
        logging.info("Connecting to ROS bridge")
        self.address = address
        self.port = port
        self.client = roslibpy.Ros(host=self.address, port=self.port)
        self.robot_state_monitor.set_client(self.client)
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
        try:
            self.client.run()
        except Exception as e:
            logging.error(f"Connection to ROS bridge failed: {e}")
            self.client.close()
        else:
            self.robot_state_monitor = RobotStateMonitor(self.client)
            print(self.get_services())

    def _setup_publisher(self, topic, message_type="std_msgs/String"):
        publisher = roslibpy.Topic(self.client, topic, message_type)
        publisher.advertise()
        logging.info(f" Publisher setup for topic: {topic}")
        return publisher

    def get_state(self, name):
        return self.robot_state_monitor.get_state(name)

    def get_smart_topics(self):
        return self.robot_state_monitor.get_states()

    def drive(self, forward=0.0, turn=0.0):
        state = self.get_state("cmd_vel")
        state.value = {"linear": {"x": forward}, "angular": {"z": turn}}

    def get_services(self):
        return self.client.get_services()

    def execute_service(self, name, *args):
        service = roslibpy.Service(self.client, name, 'std_srvs/Empty')
        request = roslibpy.ServiceRequest()
        service.call(request, *args)
