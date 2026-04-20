import rclpy
from rclpy.node import Node
from pupil_neon_ros.msg import GazeData
from gaze_interaction_manager.msg import ButtonStatus

class ArrivalDeltaMonitor(Node):
    def __init__(self):
        super().__init__('arrival_delta_monitor')
        
        self.gaze_sub = self.create_subscription(GazeData, 'pupil_glasses/gaze_data', self.gaze_cb, 10)
        self.btn_sub = self.create_subscription(ButtonStatus, 'dwell_time/active_button', self.btn_cb, 10)
        
        self.latest_gaze_hw_time = 0.0
        self.latest_gaze_arrival_time = 0.0

    def gaze_cb(self, msg):
        self.latest_gaze_hw_time = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)
        self.latest_gaze_arrival_time = self.get_clock().now().nanoseconds / 1e9

    def btn_cb(self, msg):
        btn_hw_time = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)
        btn_arrival_time = self.get_clock().now().nanoseconds / 1e9
        
        # How far behind is the button data compared to the gaze data?
        # 1. Temporal difference (should be near 0 if looking at same frame)
        hw_delta_ms = (self.latest_gaze_hw_time - btn_hw_time) * 1000
        
        # 2. Arrival difference (This is the critical pipeline delay)
        arrival_delta_ms = (btn_arrival_time - self.latest_gaze_arrival_time) * 1000
        
        self.get_logger().info(
            f"Hardware Time Delta: {hw_delta_ms:.1f}ms | "
            f"Arrival Delay (Image vs Gaze pipeline): {arrival_delta_ms:.1f}ms"
        )
        
        # If arrival delay is larger than your gaze history buffer, you are dropping matches!
        if arrival_delta_ms > 5000: # Assuming 5.0 second history_length_s
            self.get_logger().error("CRITICAL: Button data arriving after Gaze buffer has cleared!")

def main():
    rclpy.init()
    rclpy.spin(ArrivalDeltaMonitor())
    rclpy.shutdown()

if __name__ == '__main__':
    main()