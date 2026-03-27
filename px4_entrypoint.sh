#!/bin/bash

# Start supervisor in background
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf &

# Wait for VNC to start
echo "Starting VNC server..."
sleep 3

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash

echo ""
echo "==============================================================="
echo "  ROS 2 Jazzy + Gazebo Harmonic + PX4 + Mavros + NoVNC"
echo "==============================================================="
echo "  PX4 binds to port 18570 locally inside the container"
echo "  QGroundControl sends MAVLink telemetry to remote port 14550"
echo ""
echo "  VNC Access: http://localhost:6080/vnc.html"
echo "  VNC Password: 1234"
echo ""
echo "  Start PX4 SITL:"
echo "    cd /root/PX4-Autopilot"
echo "    make px4_sitl gz_x500"
echo ""
echo "  Different vehicle models to start:"
echo "    - x500 Quadrotor: make px4_sitl gz_x500"
echo "    - X500 Quadrotor with Depth Camera (Front-facing): make px4_sitl gz_x500_depth"
echo "    - X500 Quadrotor with Vision Odometry: make px4_sitl gz_x500_vision05"
echo "    - X500 Quadrotor with 1D LIDAR (Down-facing): make px4_sitl gz_x500_lidar_down"
echo "    - X500 Quadrotor with 2D LIDAR: make px4_sitl gz_x500_lidar_2d"
echo "    - X500 Quadrotor with 1D LIDAR (Front-facing): make px4_sitl gz_x500_lidar_front"
echo "    - X500 Quadrotor with gimbal (Front-facing) in Gazebo: make px4_sitl gz_x500_gimbal"
echo ""
echo "  Start Mavros:"
echo "    ros2 run mavros mavros_node --ros-args -p fcu_url:=udp://:14540@14557"
echo ""
echo "  Start ROS Gazebo Bridge:"
echo "    ros2 run ros_gz_bridge parameter_bridge \\"
echo "      /world/default/model/x500_0/link/lidar_sensor_link/sensor/lidar/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan \\"
echo "      /world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image@sensor_msgs/msg/Image@gz.msgs.Image \\"
echo "      /world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo \\"
echo "      /depth_camera@sensor_msgs/msg/Image@gz.msgs.Image \\"
echo "      /depth_camera/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked \\"
echo "      --ros-args \\"
echo "      -r /world/default/model/x500_0/link/lidar_sensor_link/sensor/lidar/scan:=/lidar/scan \\"
echo "      -r /world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/camera_info:=/camera/color/camera_info \\"
echo "      -r /world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image:=/camera/color/image \\"
echo "      -r /depth_camera:=/camera/depth/image \\"
echo "      -r /depth_camera/points:=/camera/depth/points"
echo "==============================================================="

# Drop into interactive bash shell
exec /bin/bash