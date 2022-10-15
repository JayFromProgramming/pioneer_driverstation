import base64
import time
from io import BytesIO

import roslibpy
import logging
from PIL import Image

logging = logging.getLogger(__name__)


class ImageHandler:
    """Processes /camera/image/compressed messages"""

    def __init__(self, name=""):
        self.name = name
        self.image = None
        self.timestamp = None
        self.has_changed = False
        self._last_image = None

    def handle_image(self, message):
        """Handle a message from the topic"""
        self.timestamp = message["timestamp"]
        base64_bytes = message['data'].encode('ascii')
        image_bytes = base64.b64decode(base64_bytes)
        self.image = Image.open(BytesIO(image_bytes))
        self.has_changed = True


class State:
    """Processes and stores the data from each topic"""

    def __init__(self, name="", topic=None, allow_setting=False):
        self.name = name
        self._value = None

        self.topic = topic
        self.allow_setting = allow_setting
        if self.topic is None and self.allow_setting:
            raise ValueError("Cannot allow setting without a topic to publish to")
        if self.topic is not None:
            self._subscribe(self.topic)

        if self.allow_setting:
            self.topic.advertise()

        self.value_changed = False
        self.not_single = False  # type: bool # If the value is not a single value, but a list of values
        self.has_data = False  # type: bool # If the value has been updated at least once
        self.reading = False  # type: bool # If the value is being read

        self.last_update = None  # type: float or None # The time of the last update
        self.update_frequency = None  # type: float or None # The frequency of updates

        logging.info(f"State: {name} created")

    def callback(self, message):
        """Callback for the topic, when a message is received"""
        if self.reading:
            return
        self.last_update = time.time()
        self.has_data = True
        if "data" in message:
            value = message["data"]
        else:
            value = message
            self.not_single = True
        if self._value != value:
            self.value_changed = True
        self._value = value

    @property
    def value(self):
        self.reading = True
        value = self._value
        self.reading = False
        return value

    @value.setter
    def value(self, value):
        if self.allow_setting:
            self.topic.publish(value)
        else:
            raise ValueError(f"Cannot set value of {self.name} as it is not allowed")

    def has_changed(self):
        if self.value_changed:
            self.value_changed = False
            return True
        return False

    def _subscribe(self, topic):
        self.topic = topic
        self.topic.subscribe(self.callback)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"State: {self.name} = {self.value}"


class RobotState:

    def __init__(self):
        self._states = {}

    def add_watcher(self, client, name, topic, topic_type, allow_setting=False):
        topic = roslibpy.Topic(client, topic, topic_type, reconnect_on_close=True)
        if topic_type == "/camera/image/compressed":
            state = ImageHandler(name)
            topic.subscribe(state.handle_image)
        else:
            state = State(name, topic, allow_setting)
        self._states[name] = state
        logging.info(f"Added watcher for {name} on {topic} of type {topic_type}")

    def state(self, name):
        if name in self._states:
            return self._states[name]
        return None

    def states(self):
        return self._states.values()
