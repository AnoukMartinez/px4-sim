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

For the implementation, I oriented myself on the yolo_node from the last assignment, starting off with the subscriptions. I also defined a callback function for each of these parameters.

For the main loop functionality, I informed myself using some seperate lecture slides ([example](https://www.cs.columbia.edu/~allen/F17/NOTES/potentialfield.pdf)), and decided which additional parameters I was going to need. In this case, I defined these in the initial setup (`current_pose` to track the position, `current_state` to make sure the robot can fly (this caused some issues for the last assignment, and I now realize why), `latest_scan`, `goal_reached` so we can know when we can finish the simulation, and lastly `offboard_set`)
TODO

For the possible states we recieve from the mavros subscribed node, looking at [this](https://docs.ros.org/en/noetic/api/mavros_msgs/html/msg/State.html) documentation was helpful. We know that we want to be in the offboard state, so we check first if that's the case and correct if necessary. If everything is ready (or still ready since we are running these computations in a loop), we can start the algorithm.

---

Running the node ws quite straightforward, but there was one big issue. The node was trying to enter the armed state, but for some reason the command ran infinitely. To troubleshoot this, I manually reset the drone values, and it displayed a message letting me know everything works now.

```
pxh> param set COM_ARM_WO_GPS 1
pxh> param set NAV_DLL_ACT 0
  NAV_DLL_ACT: curr: 2 -> new: 0
pxh> INFO  [commander] Ready for takeoff!
```

I ran the node via these commands:
```
# Building it first...
colcon build --packages-select local_planner
source install/setup.bash

# ...Then running it
ros2 run local_planner planner_node
```

I continued by finishing what should have been the first part of the exercise, which is the 3D model that the drone moves inside of.