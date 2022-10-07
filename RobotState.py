import roslibpy
import logging

logging = logging.getLogger(__name__)


class State:

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
        if name == "Img":
            compression = "png"
        else:
            compression = None
        roslibpy.Topic(client, topic, topic_type, compression=compression, queue_size=10).subscribe(state.callback)
        self._states[name] = state
        logging.info(f"Added watcher for {name} on {topic} of type {topic_type}")

    def state(self, name):
        return self._states[name]

    def states(self):
        return self._states.values()
