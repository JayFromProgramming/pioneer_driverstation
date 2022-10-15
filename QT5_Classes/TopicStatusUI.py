import time
import traceback
import logging

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QLabel


logging = logging.getLogger(__name__)


def update_label_value(label, topic_name, value, color="black"):
    max_width = 40
    remaining_width = max_width - len(topic_name)
    # If the remaining width is negative, then we need to truncate the topic name to fit
    if remaining_width < 0:
        topic_name = topic_name[:remaining_width]

    # When setting the color only the value should be colored, not the topic name
    label.setText(f"<pre>{topic_name}: <font color={color}>{str(value).rjust(remaining_width)}</font></pre>")

    # label.setText(f"<pre>{topic_name}:{str(value).rjust(remaining_width, '*')}</pre>")
    # label.setText(f"<pre>{topic_name}: {'*' * available_chars}{value}</pre>")


class TopicUI(QWidget):
    """
    This widget is how the target IP address is set and the connection is made and displayed
    """

    def __init__(self, robot, parent=None):
        super().__init__()
        super().setParent(parent)
        super().setFixedSize(350, 200)
        self.robot = robot
        self.parent = parent

        # Create a topic status label
        self.topic_status_labels = []
        self.topic_status_header = QLabel("Topic Status", self)
        self.topic_status_header.setStyleSheet("font-weight: bold; font-size: 17px")
        self.topic_status_header.move(0, 0)
        offset_y = 20
        for topic in self.robot.target_topics:
            label = QLabel(f"<pre>{topic}:</pre>", self)
            label.move(0, offset_y)
            label.setFixedSize(350, 20)
            self.topic_status_labels.append((topic, label))
            offset_y += 15

        # Setup the timer to update the labels
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_loop)
        self.update_timer.start(1000)

    def update_loop(self):
        try:
            # The topic status's should be on the very right of the text box so we need to figure out how many characters
            # fit in the box and then subtract that from the total length of the name of the topic
            if not self.robot.is_connected:
                # Set all the labels to yellow
                for topic, label in self.topic_status_labels:
                    update_label_value(label, topic, "UNKNOWN", color="darkorange")
            else:
                for topic, label in self.topic_status_labels:
                    if state := self.robot.get_state_from_raw(topic):
                        if state.has_data:
                            if state.last_update < time.time() - 15:
                                update_label_value(label, topic, "STALE", color="darkorange")
                            else:
                                update_label_value(label, topic, "OK", color="green")
                        else:
                            update_label_value(label, topic, "NO DATA", color="red")
                    else:
                        update_label_value(label, topic, "NOT FOUND", color="red")
        except Exception as e:
            logging.error(f"Error in topicUI update: {e} {traceback.format_exc()}")
