import robot_upstart
j = robot_upstart.Job(name="pioneer")
j.symlink = True

j.add(package="nre_p3at", filename="launch/base.launch")
j.add(package="rosbridge_server", filename="launch/rosbridge_websocket.launch")
j.add()

j.install()
j.enable()
