import time

import cv2
import roslibpy

client = roslibpy.Ros(host='localhost', port=9090)

publisher = roslibpy.Topic(client, '/camera/image/compressed', 'sensor_msgs/CompressedImage',
                           queue_size=1, throttle_rate=100, latch=True, reconnect_on_close=True)
publisher.advertise()


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


def send_image(image):
    """Send an image to the ROS topic"""
    msg = roslibpy.Message({
        'format': 'jpeg',
        'timestamp': round(time.time(), 3),
        'data': encode_image(image)
    })
    publisher.publish(msg)


def camera_loop():
    """Continuously fetch and send images"""
    image = get_image()
    send_image(image)


client.on_ready(camera_loop)
client.run_forever()
