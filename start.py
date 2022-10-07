
import subprocess
# Runs on pioneer to start ROS with rosbridge without using nohup
# All subprocess calls should be non-blocking

# Check if ROS is running, if not start it


# Run command "rosnode list" and get the string output
def rosnode_list():
    return subprocess.check_output("rosnode list", shell=True).decode("utf-8")

# Check if stout says "ERROR: Unable to communicate with master!"

print(rosnode_list())

if rosnode_list() == "ERROR: Unable to communicate with master!":
    print("ROS is not running, starting it")
    subprocess.Popen(["roscore"], start_new_session=True)
    subprocess.Popen(["roslaunch", "rosbridge_server", "rosbridge_websocket.launch"], start_new_session=True)
    subprocess.Popen(["roslaunch", "nre_p3at", "complete.launch"], start_new_session=True)
    print("ROS started")
else:
    print("ROS is already running")
