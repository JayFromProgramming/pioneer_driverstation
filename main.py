import sys
import asyncio
import threading

import roslibpy
from PyQt5.QtWidgets import QApplication

import ROSInterface
import DriverStatonUI
import logging
import paramiko

logging.basicConfig(level=logging.INFO)


def ssh_ros_start(address="localhost", username="ubuntu", password="ubuntu"):
    logging.info("Connecting to Pioneer over SSH, checking if ROS is running")
    ssh = paramiko.SSHClient()  # type: paramiko.SSHClient
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Set policy to auto add host key
    try:
        ssh.connect(address, port=22, username=username, password=password)  # Connect to server
    except Exception as e:
        logging.error(f"SSH connection failed: {e}")
        return False
    else:
        # Execute the ros start.py script
        stdin, stdout, stderr = ssh.exec_command("python3 start.py")
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                print(stdout.channel.recv(1024).decode("utf-8"))
            if stderr.channel.recv_stderr_ready():
                print(stderr.channel.recv_stderr(1024).decode("utf-8"))

        if stdout.channel.recv_exit_status() != 0:
            logging.error("SSH command failed")
            return False

        ssh.close()
        return True


if __name__ == '__main__':

    app = QApplication([])

    address = "141.219.122.199"
    port = 9090

    # if not ssh_ros_start(address, username="ubuntu", password="ubuntu"):
    #     logging.error("ROS not started, exiting")
    #     exit(1)

    pioneer = ROSInterface.ROSInterface(address, port)
    # pioneer.connect()
    logging.info(f"Connected to ROS master at {address}:{port}")
    # while pioneer.client.is_connecting:
    #     pass
    gui = DriverStatonUI.DriverStationUI(pioneer)
    # threading.Thread(target=gui.run, daemon=True).start()

    app.exec_()
    # gui.run()
    while pioneer.client.is_connected:
        pass

    # Set qt event loop

