import robot_upstart
j = robot_upstart.Job(name="pioneer")
j.symlink = True

j.add(package="nre_p3at", filename="base.launch")
j.add(package="rosbridge_server", filename="rosbridge_websocket.launch")

j.install()
