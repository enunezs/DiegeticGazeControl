import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32, Joy
import csv


class DataLoggerNode(Node):
    def __init__(self):
        super().__init__("data_logger_node")

        # Joy
        self.subscription1 = self.create_subscription(
            Joy, "/joy", self.topic1_callback, 10
        )
        # Robot
        self.subscription2 = self.create_subscription(
            Int32, "topic2", self.topic2_callback, 10
        )
        self.csv_file = open("data.csv", "w")
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["Topic", "Data"])

    def topic1_callback(self, msg):
        self.log_data("topic1", msg.data)

    def topic2_callback(self, msg):
        self.log_data("topic2", msg.data)

    def log_data(self, topic, data):
        self.get_logger().info(f"Received data on {topic}: {data}")
        self.csv_writer.writerow([topic, data])
        self.csv_file.flush()


def main(args=None):
    rclpy.init(args=args)
    data_logger_node = DataLoggerNode()
    rclpy.spin(data_logger_node)
    data_logger_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
