import robot_upstart
j = robot_upstart.Job(name="pioneer")
j.symlink = True

j.add(package="nre_p3at", filename="launch/base.launch")
j.add(package="rosbridge_server", filename="launch/rosbridge_websocket.launch")
# rosrun rosserial_python serial_node.py _port:=/dev/ttyACM0
j.add(package="rosserial_python", filename="serial_node.py", args="_port:=/dev/ttyACM0")
j.add()

j.install()
j.enable()
