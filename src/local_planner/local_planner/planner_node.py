from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist, PoseStamped
from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, SetMode
import math
import numpy as np

goal_x = -50.0
goal_y = 0.0

ATTRACTIVE_GAIN = 0.5
REPULSIVE_GAIN  = 1.5
REPULSIVE_RANGE = 2.0
MAX_SPEED       = 1.0
GOAL_TOLERANCE  = 0.5
CRUISE_ALTITUDE = 5.0

class PlannerNode(Node):
    def __init__(self):
        super().__init__('planner_node')
        
        mavros_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # subs and pubs
        self.create_subscription(State, '/mavros/state', self.state_callback, mavros_qos)
        self.create_subscription(PoseStamped, '/mavros/local_position/pose', self.pose_callback, mavros_qos)
        self.create_subscription(LaserScan, '/world/devops_testworld/model/x500_lidar_2d_0/link/link/sensor/lidar_2d_v2/scan', self.scan_callback, 10)
        
        self.vel_pub = self.create_publisher(Twist, '/mavros/setpoint_velocity/cmd_vel_unstamped', 10)
        self.arming_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.set_mode_client = self.create_client(SetMode, '/mavros/set_mode')

        # additional params
        self.declare_parameter('goal_x', goal_x)
        self.declare_parameter('goal_y', goal_y)
        self.goal_x = self.get_parameter('goal_x').get_parameter_value().double_value
        self.goal_y = self.get_parameter('goal_y').get_parameter_value().double_value

        self.current_pose = None
        self.current_state = State()
        self.latest_scan = None
        self.goal_reached = False
        self.offboard_set = False
        
        self.arm_sent = False
        self.offboard_sent = False
        
        self.create_timer(0.05, self.loop)
        self.get_logger().info(f'Goal: ({self.goal_x}, {self.goal_y})')

    def state_callback(self, message):
        self.current_state = message

    def pose_callback(self, message):
        self.current_pose = message

    def scan_callback(self, message):
        self.latest_scan = message

    def loop(self):
        if self.current_pose is None or self.latest_scan is None:
            return

        if not self.current_state.armed:
            self.arm()
            return

        if self.current_state.mode != 'OFFBOARD':
            self.set_offboard()
            return

        if self.goal_reached:
            self.hover()
            return
        
        # all good? then start the main loop
        vx, vy = self.compute_potential_field()

        current_z = self.current_pose.pose.position.z
        vz = 0.5 * (CRUISE_ALTITUDE - current_z)
        vz = max(-1.0, min(1.0, vz))

        cmd = Twist()
        cmd.linear.x = float(vx)
        cmd.linear.y = float(vy)
        cmd.linear.z = float(vz)
        self.vel_pub.publish(cmd)

        # goal reached?
        dx = self.goal_x - self.current_pose.pose.position.x
        dy = self.goal_y - self.current_pose.pose.position.y
        if math.sqrt(dx**2 + dy**2) < GOAL_TOLERANCE:
            self.get_logger().info('Goal reached! Hovering.')
            self.goal_reached = True

    def compute_potential_field(self):
        pos = self.current_pose.pose.position

        dx = self.goal_x - pos.x
        dy = self.goal_y - pos.y
        dist_to_goal = math.sqrt(dx**2 + dy**2) + 1e-6
        att_x = ATTRACTIVE_GAIN * (dx / dist_to_goal)
        att_y = ATTRACTIVE_GAIN * (dy / dist_to_goal)

        rep_x, rep_y = 0.0, 0.0
        scan = self.latest_scan
        angle = scan.angle_min

        for r in scan.ranges:
            if scan.range_min < r < REPULSIVE_RANGE:
                ox = r * math.cos(angle)
                oy = r * math.sin(angle)
                dist = math.sqrt(ox**2 + oy**2) + 1e-6

                mag = REPULSIVE_GAIN * (1.0/dist - 1.0/REPULSIVE_RANGE) / (dist**2)

                rep_x -= mag * (ox / dist)
                rep_y -= mag * (oy / dist)

            angle += scan.angle_increment

        vx = att_x + rep_x
        vy = att_y + rep_y

        speed = math.sqrt(vx**2 + vy**2) + 1e-6
        if speed > MAX_SPEED:
            vx = vx / speed * MAX_SPEED
            vy = vy / speed * MAX_SPEED

        return vx, vy

    def arm(self):
        if self.arm_sent:
            return
        if not self.arming_client.service_is_ready():
            return
        req = CommandBool.Request()
        req.value = True
        self.arming_client.call_async(req)
        self.arm_sent = True
        self.get_logger().info('Sending arm command...')

    def set_offboard(self):
        if self.offboard_sent:
            return
        if not self.set_mode_client.service_is_ready():
            return
        self.hover()
        req = SetMode.Request()
        req.custom_mode = 'OFFBOARD'
        self.set_mode_client.call_async(req)
        self.offboard_sent = True
        self.get_logger().info('Requesting OFFBOARD mode...')

    def hover(self):
        cmd = Twist()
        cmd.linear.z = 0.5 * (CRUISE_ALTITUDE - (
            self.current_pose.pose.position.z if self.current_pose else 0.0))
        self.vel_pub.publish(cmd)


def main():
    rclpy.init()
    node = PlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        stop = Twist()
        node.vel_pub.publish(stop)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()