
import roslibpy
import cv2

client = roslibpy.Ros(host='127.0.0.1', port=9090)

publisher = roslibpy.Topic(client, '/camera/image/compressed', 'sensor_msgs/CompressedImage')
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


def send_image(image, pub):
    """Send an image to the ROS topic"""
    msg = encode_image(image)
    pub.publish(msg)


def publish_image():
    image = get_image()
    send_image(image, publisher)


client.on_ready(publish_image)
client.run_forever()



