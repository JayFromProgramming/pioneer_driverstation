import ctypes
import sys
import asyncio
import threading

import roslibpy
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication

from ROS import ROSInterface
import DriverStatonUI
import logging
import paramiko

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    app = QApplication([])
    app.setStyle('Windows')
    app.setApplicationName("T-Shirt Cannon Driver Station")
    app.setApplicationVersion("1.0.0")
    app.setWindowIcon(QtGui.QIcon("resources/rse.png"))
    app.setQuitOnLastWindowClosed(True)

    myappid = 'rse.tshirt.cannon.station'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    pioneer = ROSInterface.ROSInterface()  # MAC: a0:a8:cd:be:8d:2c
    # while pioneer.client.is_connecting:
    #     pass
    gui = DriverStatonUI.DriverStationUI(pioneer)
    # threading.Thread(target=gui.run, daemon=True).start()

    app.exec_()
    # gui.run()
    # while pioneer.client.is_connected:
    #     pass
    pioneer.terminate()
    # Set qt event loop
