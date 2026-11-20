# Hand Gesture Controlled Virtual Vehicle (ROS 2 + Gazebo)

A two-computer ROS 2 project that uses a RealSense depth camera and MediaPipe hand tracking to control a virtual vehicle in Gazebo.

## Project overview

The camera computer detects the user's hand, estimates the palm distance from the RealSense depth image, recognizes selected hand gestures, and publishes a text command. The Gazebo computer receives that command and converts it into a `geometry_msgs/Twist` message for the simulated vehicle.

### ROS 2 communication

```text
Computer 1: RealSense D435i
        |
        v
OpenCV + MediaPipe hand landmarks
        |
        +---- palm distance ----> /hand_distance (std_msgs/Float32)
        |
        +---- gesture/distance -> /hand_command (std_msgs/String)
                                      |
                         ROS 2 network / DDS
                                      |
                                      v
Computer 2: hand_command_receiver
                                      |
                                      v
                               /cmd_vel
                                      |
                                      v
                           Gazebo diff-drive plugin
                                      |
                                      v
                              Virtual vehicle
```

## Packages

| Package | Purpose |
|---|---|
| `hand_distance_ros` | Reads RealSense color/depth frames, detects hand landmarks, estimates palm distance, recognizes Peace and Shaka gestures, and publishes `/hand_command` and `/hand_distance`. |
| `hand_vehicle_control` | Subscribes to `/hand_command`, applies a command timeout, and publishes `/cmd_vel`. |
| `virtual_vehicle_description` | Contains the vehicle Xacro, Gazebo world, and simulation launch file. |

## Gesture and distance behavior

- Peace sign: `LEFT`
- Shaka sign: `RIGHT`
- Hand farther than 0.55 m: `FORWARD`
- Hand closer than 0.40 m: `REVERSE`
- Intermediate distance, missing hand, or unavailable depth: `STOP`
- A recognized stable gesture takes priority over distance-based movement.
- The receiver stops the vehicle if it does not receive a fresh command for 0.75 seconds.

The gesture detector stabilizes recognition using a short history of recent detections.

## Requirements

This repository targets **Ubuntu 22.04 + ROS 2 Humble + Gazebo Classic**.

### Gazebo / ROS 2 computer

Install the ROS packages used by the simulation:

```bash
sudo apt update
sudo apt install -y \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-xacro \
  ros-humble-robot-state-publisher \
  ros-humble-geometry-msgs \
  ros-humble-std-msgs
```

### Camera computer

The camera computer needs:

- Intel RealSense D435i and the RealSense SDK / Python bindings (`pyrealsense2`)
- OpenCV (`cv2`)
- NumPy
- MediaPipe Tasks
- ROS 2 Humble Python packages

Install the Python packages in the Python environment used by ROS 2:

```bash
python3 -m pip install numpy opencv-python mediapipe pyrealsense2
```

Install the MediaPipe Hand Landmarker task model and set its path as described below. The model file is not included in this repository.

## Build

Clone the repository, then build all three packages from the repository root:

```bash
source /opt/ros/humble/setup.bash
cd hand_gesture_vehicle_github
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

If `rosdep` reports dependencies that are not available through rosdep, install the corresponding ROS/Python dependencies using the instructions above.

## Configure the two-computer ROS 2 network

On **both computers**, use the same ROS domain and middleware settings in every terminal:

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=25
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
unset ROS_LOCALHOST_ONLY
```

Both computers should be connected to the same reachable network. Network/firewall settings must allow ROS 2 DDS discovery and traffic between the computers.

## Run the project

### Computer 2 — Gazebo vehicle

Terminal 1:

```bash
source /opt/ros/humble/setup.bash
cd ~/hand_gesture_vehicle_github
source install/setup.bash
export ROS_DOMAIN_ID=25
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
unset ROS_LOCALHOST_ONLY

ros2 launch virtual_vehicle_description vehicle_simulation.launch.py
```

Terminal 2:

```bash
source /opt/ros/humble/setup.bash
cd ~/hand_gesture_vehicle_github
source install/setup.bash
export ROS_DOMAIN_ID=25
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
unset ROS_LOCALHOST_ONLY

ros2 run hand_vehicle_control hand_receiver
```

### Computer 1 — RealSense hand publisher

First, place the MediaPipe `hand_landmarker.task` model on the camera computer. Then set the environment variable to its full path:

```bash
export HAND_LANDMARKER_MODEL="$HOME/path/to/hand_landmarker.task"
```

Run the publisher:

```bash
source /opt/ros/humble/setup.bash
cd ~/hand_gesture_vehicle_github
source install/setup.bash
export ROS_DOMAIN_ID=25
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
unset ROS_LOCALHOST_ONLY

ros2 run hand_distance_ros hand_publisher
```

`HAND_LANDMARKER_MODEL` is optional if the model is already located at:

```text
~/internship/hand_distance/hand_landmarker.task
```

## Verify topics

On either computer:

```bash
ros2 topic list
ros2 topic echo /hand_command
ros2 topic echo /cmd_vel
```

To inspect the measured distance:

```bash
ros2 topic echo /hand_distance
```

## Safety and limitations

- This repository is configured for a **Gazebo virtual vehicle**. It is not a validated controller for a real vehicle or motorized platform.
- Test in simulation first. Do not connect this software to real vehicle actuators without a separate engineering safety review, hardware emergency stop, and appropriate safeguards.
- Camera operation requires the RealSense device to be connected and accessible.
- The MediaPipe `.task` model is intentionally not bundled; provide your own downloaded model file and set `HAND_LANDMARKER_MODEL`.
- The current hand publisher uses the camera computer's local model path and the current ROS 2 domain settings shown above.

## Repository layout

```text
hand_gesture_vehicle_github/
├── README.md
├── .gitignore
└── src/
    ├── hand_distance_ros/
    ├── hand_vehicle_control/
    └── virtual_vehicle_description/
```

## License

The package metadata in this project declares Apache-2.0. Add the full Apache 2.0 license text and confirm the licensing of any third-party assets/models before publishing a public repository.
