[GitHub Repository Link](https://github.com/AnoukMartinez/px4-sim)

---

# Devops for Cyberphysical Systems, Exercise 5 (23.04.2026)
## Task 2: Local Planner, Obstacle Avoidance

### a) Create Create a 3D environment with different objects (humans, buildings, trees, vehicles etc.) in Gazebo or get one from Fuel.

(TODO from last time)

### b) Start PX4 SITL with a vehicle equipped with a depth camera or LiDAR
This step was rather straightforward as the setup was still working from the last task. The main differences:

- Starting a different suitable vehicle
    ```
    docker exec -it px4_sitl bash
    cd ~/PX4-Autopilot
    make px4_sitl gz_x500_lidar_2d
    ```
- Running a new bridge for the `/world/default/model/x500_lidar_2d_0/link/link/sensor/lidar_2d_v2/scan` topic
    ```
    ros2 run ros_gz_bridge parameter_bridge /world/default/model/x500_lidar_2d_0/link/link/sensor/lidar_2d_v2/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan
    ```

### c) Implement a ROS2 node that computes potential fields and performs local motion control
To start off, I took a look at the available mavros topics we will need to determine and control the drone's position. There was quite a lot to choose from...

```
root@823cfdfae04b:~# ros2 topic list | grep mavros
/mavros/actuator_control
/mavros/altitude
/mavros/battery
/mavros/estimator_status
/mavros/extended_state
/mavros/home_position/set
/mavros/imu/diff_pressure
/mavros/local_position/accel
/mavros/local_position/odom
...
/mavros/statustext/send
/mavros/sys_status
/mavros/target_actuator_control
/mavros/time_reference
/mavros/timesync_status
/mavros/wind_estimation
```

...but since we only need to do two things, we can reduce the services we want to focus on. To summarize, we want to:
- *get* info on the drone (position, state and LiDAR data)
- and secondly we want to *control* the drone as well (move the drone, arm and set mode so we can move it)

```sh
# Get Info
/mavros/local_position/pose
/mavros/state
/world/default/model/x500_lidar_2d_0/link/link/sensor/lidar_2d_v2/scan

# Publish commands and additionally required
/mavros/setpoint_velocity/cmd_vel_unstamped
/mavros/cmd/arming
/mavros/set_mode
```

For now, I want to implement the potential fields algorithm, since it was easy to understand in the lecture, and also noted it's easy to implement in general. So for now, if the goal is just to get something running this is where I'll start.

---

First step now, same as last week, will be to create the node and everything formal necessary to get it running.

```
cd ~/ros2_ws/src
ros2 pkg create local_planner --build-type ament_python --dependencies rclpy sensor_msgs geometry_msgs mavros_msgs
```