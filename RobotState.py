import base64
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

    def __init__(self, name=""):
        self.name = name
        self.value = "No update"
        self.value_changed = False
        self.not_single = False  # type: bool # If the value is not a single value, but a list of values
        self.has_data = False  # type: bool # If the value has been updated at least once
        self.reading = False  # type: bool # If the value is being read
        logging.info(f"State: {name} created")

    def callback(self, message):
        if self.reading:
            return
        self.has_data = True
        if "data" in message:
            value = message["data"]
        else:
            value = message
            self.not_single = True
        self.check_value(value)

    def get_value(self):
        self.reading = True
        value = self.value
        self.reading = False
        return value

    def check_value(self, value):
        if value != self.value:
            self.value = value
            self.value_changed = True

    def has_changed(self):
        if self.value_changed:
            self.value_changed = False
            return True
        return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"State: {self.name} = {self.value}"


class RobotState:

    def __init__(self):
        self._states = {}

    def add_watcher(self, client, name, topic, topic_type):
        state = State(name)
        roslibpy.Topic(client, topic, topic_type, queue_size=1, throttle_rate=10).subscribe(state.callback)
        if topic_type == "/camera/image/compressed":
            state = ImageHandler(name)
            client.subscribe(topic, topic_type, state.handle_image)
        else:
            state = State(name)
            client.subscribe(topic, topic_type, state.callback)
        self._states[name] = state
        logging.info(f"Added watcher for {name} on {topic} of type {topic_type}")

    def state(self, name):
        return self._states[name]

    def states(self):
        return self._states.values()
