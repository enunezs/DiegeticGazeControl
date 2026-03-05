import rclpy
from rclpy.node import Node
from std_msgs.msg import String
class ASRNode(Node):
   def __init__(self):
       super().__init__('asr_node')
       self.publisher_ = self.create_publisher(String, 'recognized_speech', 10)
       self.get_logger().info("ASR Node Started")
   def publish_text(self, text):
       msg = String()
       msg.data = text
       self.publisher_.publish(msg)
def main(args=None):
   rclpy.init(args=args)
   node = ASRNode()
   rclpy.spin(node)
   node.destroy_node()
   rclpy.shutdown()
