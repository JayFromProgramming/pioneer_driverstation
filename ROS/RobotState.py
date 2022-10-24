import base64
import random
import threading
import time
from io import BytesIO

import cv2
import numpy as np
import roslibpy
import logging
from PIL import Image

logging = logging.getLogger(__name__)


class SmartTopic:

    def __init__(self, disp_name, topic_name, *args, **kwargs):
        logging.info(f"Initializing {disp_name} on topic {topic_name}")
        self.disp_name = disp_name
        self.topic_name = topic_name

        self.exists = False
        self.has_data = False
        self.is_single = True
        self._has_changed = False

        self._update_interval = []  # Used to calculate the update rate over the last 10 updates

        self.client = kwargs.get("client", None)
        self.topic_type = kwargs.get("topic_type", None)
        self.throttle_rate = kwargs.get("throttle_rate", 0)
        self.queue_size = kwargs.get("queue_size", 5)
        self.auto_reconnect = kwargs.get("auto_reconnect", True)
        self.allow_update = kwargs.get("allow_update", False)
        self.hidden = kwargs.get("hidden", False)
        self._compression = kwargs.get("compression", None)

        self._value = None
        self._lock = threading.Lock()
        self._last_update = 0
        self._listener = None  # type: roslibpy.Topic or None
        self._publisher = None  # type: roslibpy.Topic or None
        logging.info(f"{self.disp_name} created and initialized... Waiting for connection")
        if self.client is not None:
            self.client.on_ready(self.connect, run_in_thread=True)

    def set_client(self, client):
        try:
            self.client = client
            self.client.on_ready(self.connect, run_in_thread=True)
        except Exception as e:
            logging.error(f"Error setting client for {self.disp_name}: {e}")

    def set_type(self, topic_type):
        self.topic_type = topic_type

    def _topic_type_callback(self, topic_type):
        if topic_type == "":
            self.exists = False
            logging.debug(f"Topic {self.topic_name} does not exist")
            thread = threading.Thread(target=self._recheck_exists, daemon=True)
            thread.start()
        else:
            logging.info(f"Acquired type {topic_type} for topic {self.topic_name}")
            self.connect()

    def _recheck_exists(self):
        """If the topic didn't exist at ready this loop runs to try to see if it has appeared"""
        return
        time.sleep(5 + random.randint(0, 5))
        if not self.exists and self.client.is_connected:
            self.client.get_topic_type(self.topic_name, self._topic_type_callback)
        else:
            logging.info(f"Topic recheck has been cancelled for {self.topic_name}")

    def connect(self):
        if self.topic_type is None:
            # Get the type of the topic from the ROS master
            self.topic_type = self.client.get_topic_type(self.topic_name)
            if self.topic_type == "":
                self.exists = False
                logging.error(f"Topic {self.topic_name} does not exist")
                threading.Thread(target=self._recheck_exists, daemon=True).start()
                return
            else:
                logging.info(f"Acquired type {self.topic_type} for topic {self.topic_name}")
                self.exists = True

        self._listener = roslibpy.Topic(self.client, self.topic_name, self.topic_type, queue_size=5,
                                        throttle_rate=self.throttle_rate, reconnect_on_close=self.auto_reconnect,
                                        compression=self._compression)
        self._listener.subscribe(self._update)
        if self.allow_update:
            self._publisher = roslibpy.Topic(self.client, self.topic_name, self.topic_type)
            # self._publisher.advertise()
            logging.info(f"{self.disp_name} connected to {self.topic_name} of type {self.topic_type}, publishing enabled")
        else:
            logging.info(f"{self.disp_name} connected to {self.topic_name} of type {self.topic_type}, publishing disabled")

    def _update(self, message):
        """
        :param message:
        :return:
        """
        self._lock.acquire()
        self.has_data = True
        if "data" in message:
            value = message["data"]
        else:
            value = message
            self.not_single = True
        if self._value != value:
            self._value = value
            self._has_changed = True
        self._lock.release()

        self._last_update = time.time()
        self._update_interval.append(self._last_update)
        if len(self._update_interval) > 10:
            self._update_interval.pop(0)

    def has_changed(self):
        """Returns None if the value hasn't changed and the new value if it has"""
        self._lock.acquire()
        if self._has_changed:
            self._has_changed = False
            self._lock.release()
            return self._value
        self._lock.release()
        return None

    @property
    def value(self):
        self._lock.acquire()
        value = self._value
        self._lock.release()
        return value

    @value.setter
    def value(self, updated_values):
        if self.allow_update:
            # logging.info(f"Updating {self.disp_name} with {updated_values} -> {self.value}")
            if not self.exists:
                # logging.error(f"Topic {self.topic_name} does not exist")
                return
            if self.is_single and self.topic_type != "geometry_msgs/Twist":
                msg = roslibpy.Message({"data": updated_values})
                logging.debug(f"Publishing {updated_values} to {self.topic_name}")
            else:
                # If the value is not a single value, but a list of values or a dictionary
                # Then we need to update the values in the dictionary and publish the entire dictionary
                # Generate an instance of the message type
                if self.has_data:
                    # If we have data, then we can use the current value as a template
                    msg = roslibpy.Message(self.value)
                else:
                    # Otherwise, we need to create a blank message
                    msg = roslibpy.Message({})
                # Update the values in the message
                for key, value in updated_values.items():
                    msg[key] = value

            self._publisher.publish(msg)
        else:
            raise Exception("This topic is not allowed to be updated")

    def get_update_rate(self) -> float:
        """Returns the current update rate of the topic in Hz"""
        if len(self._update_interval) > 1:
            try:
                return 1 / ((self._update_interval[-1] - self._update_interval[0]) / len(self._update_interval))
            except ZeroDivisionError:
                return 0
        else:
            return 0

    def get_status(self):
        """Returns the current state of the topic, and that states associated color"""
        if self.exists:
            if self.has_data:
                if self._listener.is_subscribed:
                    if self._last_update > time.time() - 5:
                        return f"{round(self.get_update_rate())}Hz: OK", "green"
                    else:
                        return "STALE", "darkorange"
                else:
                    return "UNSUBED", "darkorange"
            else:
                return "NO DATA", "red"
        elif not self.client:
            return "NO CLIENT", "red"
        elif not self.client.is_connected:
            return "NO CONN", "red"
        else:
            return "MISSING", "red"

    def unsub(self):
        if self._listener:
            self._listener.unsubscribe()
        if self._publisher:
            self._publisher.unadvertise()

        self.exists = False
        self.has_data = False
        self._value = None
        self._has_changed = False
        self._last_update = 0
        logging.info(f"{self.disp_name} unsubscribed from {self.topic_name}")

    def unsubscribe(self):
        self._listener.unsubscribe()

    def resubscribe(self):
        self._listener.subscribe(self._update)

    def is_stale(self):
        if self._last_update > time.time() - 5:
            return False
        else:
            return True


# class ImageHandler(SmartTopic):
#     """Processes /camera/image/compressed messages"""
#
#     def __init__(self, client, topic_name, disp_name=None, throttle_rate=0, auto_reconnect=True, allow_update=False):
#         super().__init__(client, topic_name, disp_name, throttle_rate, auto_reconnect, allow_update,
#                          compression="png")
#         self.image = None
#         self.timestamp = None
#         self.has_changed = False
#         self._last_image = None
#
#         # Set the frame rate to 10 fps via the ros parameter server
#
#         # self.client.set_param("framerate", 10)
#
#     def connect(self):
#         print("Connecting to image topic")
#         super().connect()
#         self.client.set_param("/usb_cam/framerate", 1)
#
#     def _update(self, message):
#         """Handle a message from the topic"""
#         # self.timestamp = message["timestamp"]
#         # dict_keys(['encoding', 'height', 'header', 'step', 'data', 'width', 'is_bigendian'])
#         print(message["encoding"])
#         base64_bytes = message['data'].encode('ascii')
#         image_bytes = base64.b64decode(base64_bytes)
#         if message["encoding"] == "rgb8":
#             # print("RGB8")
#             image = np.frombuffer(image_bytes, dtype=np.uint8).reshape((message["height"], message["width"], 3))
#             self.image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
#         elif message["encoding"] == "png":
#             # print("PNG")
#             self.image = Image.open(BytesIO(image_bytes))
#
#         self.has_data = True
#         self.has_changed = True
#
#         # self.image = Image.open(BytesIO(image_bytes))
#         # self._lock.release()
#         # self.image = rgb
#
#         self._last_update = time.time()
#         self._update_interval.append(self._last_update)
#         if len(self._update_interval) > 10:
#             self._update_interval.pop(0)
#         # self.unsubscribe()


# class State:
#     """Processes and stores the data from each topic"""
#
#     def __init__(self, name="", topic=None, allow_setting=False):
#         self.name = name
#         self._value = None
#
#         self.topic = topic
#         self.allow_setting = allow_setting
#         if self.topic is None and self.allow_setting:
#             raise ValueError("Cannot allow setting without a topic to publish to")
#         if self.topic is not None:
#             self._subscribe(self.topic)
#
#         if self.allow_setting:
#             self.topic.advertise()
#
#         self.value_changed = False
#         self.not_single = False  # type: bool # If the value is not a single value, but a list of values
#         self.has_data = False  # type: bool # If the value has been updated at least once
#         self.read_lock = threading.Lock()  # type: threading.Lock # Lock for reading the value
#
#         self.last_update = None  # type: float or None # The time of the last update
#         self.update_frequency = None  # type: float or None # The frequency of updates
#
#         logging.info(f"State: {name} created")
#
#     def callback(self, message):
#         """Callback for the topic, when a message is received"""
#
#         self.read_lock.acquire()  # Lock the value, so it can't be read while it is being updated
#
#         self.last_update = time.time()
#         self.has_data = True
#         if "data" in message:
#             value = message["data"]
#         else:
#             value = message
#             self.not_single = True
#         if self._value != value:
#             self.value_changed = True
#         self._value = value
#         self.read_lock.release()  # Release the lock
#
#     @property
#     def value(self):
#         self.read_lock.acquire()
#         value = self._value
#         self.read_lock.release()
#         return value
#
#     @value.setter
#     def value(self, changed_values):
#         if self.allow_setting:
#             if self.not_single:
#
#             else:
#                 self.topic.publish(changed_values)
#         else:
#             raise ValueError(f"Cannot set value of {self.name} as it is not allowed")
#
#     def has_changed(self):
#         if self.value_changed:
#             self.value_changed = False
#             return True
#         return False
#
#     def _subscribe(self, topic):
#         self.topic = topic
#         self.topic.subscribe(self.callback)
#
#     def __str__(self):
#         return self.name
#
#     def __repr__(self):
#         return f"State: {self.name} = {self.value}"

class CannonCombinedTopic:
    state_enums = {
        "UNKNOWN": 0,
        "Emergency Stopped": 254,
        "Idle": 1,
        "Waiting for pressure": 2,
        "Pressurizing": 3,
        "Venting": 4,
        "Ready": 5,
        "Armed": 6,
        "Firing": 7
    }

    action_enums = {
        "clear_input": 0,
        "vent": 1,
        "set_auto": 2,
        "disable_auto": 3,
        "fill": 4,
        "arm": 5,
        "disarm": 6,
        "idle": 7
    }

    def __init__(self, set_pressure_topic, get_pressure_topic,
                 set_state_topic, get_state_topic,
                 get_auto_topic):
        self.set_pressure_topic = set_pressure_topic
        self.get_pressure_topic = get_pressure_topic
        self.set_state_topic = set_state_topic
        self.get_state_topic = get_state_topic
        self.get_auto_topic = get_auto_topic

    def set_pressure(self, pressure):
        try:
            self.set_pressure_topic.value = pressure
        except Exception as e:
            logging.error(f"Error setting pressure: {e}")

    def get_pressure(self):
        if self.get_pressure_topic.has_data:
            return self.get_pressure_topic.value
        else:
            return 0

    def send_command(self, state: str):
        if not self.set_state_topic.exists:
            raise ValueError("Cannot send command as the topic does not exist")
        if self.set_state_topic.value is None:
            self.set_state_topic.value = self.action_enums["clear_input"]
            self.set_state_topic.value = self.action_enums[state]
            self.set_state_topic.value = self.action_enums["clear_input"]
            return
        if self.set_state_topic.value != self.action_enums["clear_input"]:
            raise ValueError(f"Cannot set state while setting state, current state is {self.set_state_topic.value}")
        if state not in self.action_enums:
            raise ValueError(f"Invalid state: {state}")
        self.set_state_topic.value = self.action_enums[state]
        for _ in range(4):
            self.set_state_topic.value = self.action_enums["clear_input"]
            time.sleep(0.05)

    def get_state(self):
        if self.get_state_topic.value is None:
            return "No data"
        if self.get_state_topic.value not in self.state_enums.values():
            return f"Unknown state: {self.get_state_topic.value}"
        return list(self.state_enums.keys())[list(self.state_enums.values()).index(self.get_state_topic.value)]

    def get_auto(self):
        return self.get_auto_topic.value if self.get_auto_topic.has_data else False

    def is_stale(self):
        for topic in [self.get_pressure_topic, self.get_state_topic, self.get_auto_topic]:
            if topic.is_stale():
                return True
        return False

    def has_data(self):
        for topic in [self.get_pressure_topic, self.get_state_topic, self.get_auto_topic]:
            if not topic.has_data:
                return False
        return True


class RobotState:

    def __init__(self):
        self._topics = {}

    # def add_watcher(self, client, name, topic, topic_type, allow_setting=False):
    #     topic = roslibpy.Topic(client, topic, topic_type, reconnect_on_close=True)
    #     if topic_type == "/camera/image/compressed":
    #         state = ImageHandler(name)
    #         topic.subscribe(state.handle_image)
    #     else:
    #         state = State(name, topic, allow_setting)
    #     self._topics[name] = state
    #     logging.info(f"Added watcher for {name} on {topic} of type {topic_type}")

    def add_watcher(self, smart_topic):
        self._topics[smart_topic.disp_name] = smart_topic

    def state(self, name):
        for smart_topic in self.states():
            if smart_topic.disp_name == name or smart_topic.topic_name == name:
                return smart_topic
        return None

    def states(self):
        return self._topics.values()
