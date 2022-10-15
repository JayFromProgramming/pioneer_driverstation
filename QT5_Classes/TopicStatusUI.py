from PyQt5.QtWidgets import QWidget, QLabel


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
            self.topic_status_labels.append(label)
            offset_y += 15

    def update_loop(self):

        # The topic status's should be on the very right of the text box so we need to figure out how many characters
        # fit in the box and then subtract that from the total length of the name of the topic
        for i, topic in enumerate(self.robot.target_topics):


