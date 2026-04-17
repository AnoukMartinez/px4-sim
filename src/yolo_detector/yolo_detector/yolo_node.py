import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import Header
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2

from yolo_msgs.msg import Detection2D, Detection2DArray


class YoloNode(Node):
    def __init__(self):
        super().__init__('yolo_node')

        self.declare_parameter('camera_topic', '/world/default/model/x500_mono_cam_0/link/camera_link/sensor/camera/image')
        self.declare_parameter('model_path', 'yolov8n.pt')
        self.declare_parameter('confidence_threshold', 0.5)

        camera_topic = self.get_parameter('camera_topic').get_parameter_value().string_value
        model_path = self.get_parameter('model_path').get_parameter_value().string_value
        self.conf_threshold = self.get_parameter('confidence_threshold').get_parameter_value().double_value

        self.get_logger().info(f'Loading YOLO model')
        self.model = YOLO(model_path)
        self.bridge = CvBridge()

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        # subscribers and publishers
        self.sub = self.create_subscription(
            Image,
            camera_topic,
            self.callback,
            qos_profile
        )

        self.det_pub = self.create_publisher(Detection2DArray, '/yolo/detections', 10)
        self.img_pub = self.create_publisher(Image, '/yolo/annotated_image', 10)

        # for the last part of the task (latency & fps)
        self.frame_count = 0
        self.total_latency = 0.0
        self.fps_start_time = time.time()

        self.get_logger().info(f'Node started')

    def callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            if frame is None:
                return
        except Exception as e:
            self.get_logger().error(f'Failed to convert image: {str(e)}')
            return

        t_start = time.time()
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        latency = (time.time() - t_start) * 1000

        # for the last part once again (latency & fps)
        self.frame_count += 1
        self.total_latency += latency
        elapsed = time.time() - self.fps_start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0.0

        if self.frame_count % 10 == 0:
            avg_latency = self.total_latency / self.frame_count
            self.get_logger().info(
                f'FPS: {fps:.1f} | Latency: {latency:.1f}ms | Avg: {avg_latency:.1f}ms | Frames: {self.frame_count}'
            )

        # detection tasks (for the message part of the task)
        det_array = Detection2DArray()
        det_array.header = msg.header

        result = results[0]
        if result.boxes is not None:
            for box in result.boxes:
                det = Detection2D()
                det.header = msg.header
                det.class_name = self.model.names[int(box.cls[0])]
                det.confidence = float(box.conf[0])
                
                # Bounding box logic
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                det.x = float((x1 + x2) / 2)
                det.y = float((y1 + y2) / 2)
                det.width = float(x2 - x1)
                det.height = float(y2 - y1)
                det_array.detections.append(det)

        self.det_pub.publish(det_array)

        # annotating the image feed
        annotated = result.plot()
        annotated_msg = self.bridge.cv2_to_imgmsg(annotated, 'bgr8')
        annotated_msg.header = msg.header
        self.img_pub.publish(annotated_msg)

def main():
    rclpy.init()
    node = YoloNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        node.get_logger().info(
            f'Shutting down. Total frames: {node.frame_count}, '
            f'Avg latency: {node.total_latency / max(node.frame_count, 1):.1f}ms'
        )
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()