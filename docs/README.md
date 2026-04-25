# PX4-Sim

Fully containerized PX4 Autopilot simulation environment with browser-based GUI access.

## What's Included

- **ROS 2 Jazzy** - Latest ROS 2 LTS release
- **Gazebo Harmonic** - Latest Gazebo simulator
- **PX4 Autopilot** - Pre-built and ready to use
- **MAVROS** - PX4 to ROS gateway
- **TigerVNC + NoVNC** - Browser-based desktop access
- **XFCE4 Desktop** - Full desktop environment

## Quick Start

### 1. Build the Images

```bash
# Build everything
./build.sh --all

# Or build step by step
./build.sh --base  # ROS 2 + Gazebo
./build.sh --full  # PX4 Autopilot + MAVROS + NoVNC
```

### 2. Run the Container

```bash
# Interactive mode (recommended)
docker-compose up

# Or detached mode
docker-compose up -d
docker attach px4_sitl
```

### 3. Connect QGroundControl

1. Install [QGroundControl](http://qgroundcontrol.com) on your host. 
2. Create a custom communication link with the following details:
    - type: UDP
    - port: 15871
    - server: 0.0.0.0:18570
3. QGroundControl auto-connects to `udp://localhost:18570`

### 4. Access the GUI

Open your browser: **http://localhost:6080/vnc.html**

Password: `1234`

### 5. Run the Simulation

You'll be in an interactive bash shell:

```bash
docker exec -it px4_sitl bash
cd /root/PX4-Autopilot
make px4_sitl gz_x500
```

You'll see:
- Gazebo simulation with a quadcopter (in browser)
- PX4 console showing startup messages
- Drone ready for commands!

## Usage Examples

### Start/Stop

```bash
# Start (interactive)
docker-compose up

# Start (background)
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f
```

### Attach/Detach

```bash
# Attach to running container
docker attach px4_sitl

# Detach without stopping: Ctrl+P, Ctrl+Q

# Or use exec for new shell
docker exec -it px4_sitl bash
```

### Multiple Terminal Windows

```bash
# Start container
docker-compose up -d

# Terminal 1: Run PX4
docker exec -it px4_sitl bash
cd /root/PX4-Autopilot
make px4_sitl gz_x500

# Terminal 2: Run ROS packages
docker exec -it px4_sitl bash
ros2 run mavros mavros_node --ros-args -p fcu_url:=udp://:14540@14557

# Terminal 3: Monitor ROS topics
docker exec -it px4_sitl bash
ros2 topic list
ros2 topic echo /mavros/altitude

# Terminal 4: Build custom packages
docker exec -it px4_sitl bash
cd /root/ros2_ws
colcon build
```

### Try Different Vehicles

See full list of vehicles [here](https://docs.px4.io/main/en/sim_gazebo_gz/vehicles).

```bash
# X500 Quadcopter
make px4_sitl gz_x500

# RC Cessna
make px4_sitl gz_rc_cessna

# Ackermann Rover
make px4_sitl gz_rover_ackermann
```

## Network Ports

| Port | Service |
|------|---------|
| 5900 | VNC server |
| 6080 | NoVNC web interface |
| 14550/udp | PX4 MAVLink (QGroundControl) |
| 18570/udp | Local UDP port used when PX4 communicates inside container/VM setups |

## Acknowledgement

- [ROS 2 Jazzy Documentation](https://docs.ros.org/en/jazzy/)
- [Gazebo Harmonic Documentation](https://gazebosim.org/docs/harmonic/)
- [PX4 Autopilot Documentation](https://docs.px4.io/)
- [MAVROS](https://github.com/mavlink/mavros)
- [QGroundControl](http://qgroundcontrol.com)
- [TigerVNC Documentation](https://tigervnc.org/)


**Happy Simulating!** 🚁