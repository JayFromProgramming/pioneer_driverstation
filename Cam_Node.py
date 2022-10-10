#!/usr/bin/env python

import time

import cv2
import rospy
from std_msgs.msg import String


def get_image():
    """Fetch an image from the webcam"""
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    return frame


def encode_image(image):
    """Encode an image as a jpeg and return the raw bytes"""
    _, jpeg = cv2.imencode('.jpg', image)
    return jpeg.tobytes()


def send_image(image, pub):
    """Send an image to the ROS topic"""
    msg = encode_image(image)
    pub.publish(msg)


def cam_node():
    """Main function"""
    pub = rospy.Publisher('chatter', String, queue_size=1)
    rospy.init_node('cam_node', anonymous=True)
    rate = rospy.Rate(10)  # 10hz
    while not rospy.is_shutdown():
        image = get_image()
        send_image(image, pub)
        rate.sleep()


if __name__ == '__main__':
    try:
        cam_node()
    except rospy.ROSInterruptException:
        pass
