#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import numpy as np
from sklearn.linear_model import Ridge

# Use the 'Agg' backend for non-interactive (headless) plotting
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from scipy.stats import binned_statistic_2d

import cv2
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from gaze_interaction_manager.msg import InteractionSegment, CalibrationModel


class CalibrationLearner(Node):
    def __init__(self):
        super().__init__("EX_calibration_learner")

        # --- Parameters ---
        self.declare_parameter("publish_debug_image", True)
        self.pub_enabled = self.get_parameter("publish_debug_image").value

        # --- Internal Database ---
        self.db_gaze = []
        self.db_error = []
        self.coeffs_x = None
        self.coeffs_y = None

        # --- Plotting Setup (Headless) ---
        self.x_max, self.y_max = 1600, 1200
        self.bins = 40

        # Create figure without a window
        self.fig, self.ax = plt.subplots(figsize=(10, 8), dpi=100)
        self.canvas = FigureCanvasAgg(self.fig)

        # --- ROS Setup ---
        self.bridge = CvBridge()
        self.create_subscription(
            InteractionSegment, "calibration/interaction_segment", self.segment_cb, 10
        )
        self.model_pub = self.create_publisher(
            CalibrationModel, "calibration/model_update", 10
        )
        self.image_pub = self.create_publisher(
            Image, "calibration/debug_plot_image", 10
        )

        self.get_logger().info(
            "Headless Calibration Learner initialized. Publishing to RVIZ."
        )

    def segment_cb(self, msg: InteractionSegment):
        target = msg.target_pixel
        for s in msg.samples:
            self.db_gaze.append([s.x, s.y])
            self.db_error.append([s.x - target.x, s.y - target.y])

        if len(self.db_gaze) > 10:
            self.update_quadratic_model()
            if self.pub_enabled:
                self.publish_plot_image()

    def update_quadratic_model(self):
        X = np.array(self.db_gaze)
        Y = np.array(self.db_error)

        A = np.c_[
            X[:, 0] ** 2,
            X[:, 1] ** 2,
            X[:, 0] * X[:, 1],
            X[:, 0],
            X[:, 1],
            np.ones(X.shape[0]),
        ]

        # Ridge regression for numerical stability
        model_x = Ridge(alpha=1e-3).fit(A, Y[:, 0])
        model_y = Ridge(alpha=1e-3).fit(A, Y[:, 1])

        self.coeffs_x = model_x.coef_.tolist()
        self.coeffs_x[-1] = model_x.intercept_
        self.coeffs_y = model_y.coef_.tolist()
        self.coeffs_y[-1] = model_y.intercept_

        update = CalibrationModel()
        update.model_type = CalibrationModel.TYPE_QUADRATIC
        update.coeffs_x = self.coeffs_x
        update.coeffs_y = self.coeffs_y
        self.model_pub.publish(update)

    def predict_grid(self, Xc, Yc):
        x_flat, y_flat = Xc.flatten(), Yc.flatten()
        A_grid = np.c_[
            x_flat**2, y_flat**2, x_flat * y_flat, x_flat, y_flat, np.ones_like(x_flat)
        ]
        pred_x = (A_grid @ np.array(self.coeffs_x)).reshape(Xc.shape)
        pred_y = (A_grid @ np.array(self.coeffs_y)).reshape(Yc.shape)
        return pred_x, pred_y

    def publish_plot_image(self):
        if not self.db_gaze or self.coeffs_x is None:
            return

        X_all, E_all = np.array(self.db_gaze), np.array(self.db_error)
        gaze_x, gaze_y = X_all[:, 0], X_all[:, 1]
        err_x, err_y = E_all[:, 0], E_all[:, 1]

        x_edges = np.arange(0, self.x_max + self.bins, self.bins)
        y_edges = np.arange(0, self.y_max + self.bins, self.bins)
        Xc, Yc = np.meshgrid(
            (x_edges[:-1] + x_edges[1:]) / 2, (y_edges[:-1] + y_edges[1:]) / 2
        )

        # 1. Truth Vectors
        avg_err_x, _, _, _ = binned_statistic_2d(
            gaze_x, gaze_y, err_x, "median", [x_edges, y_edges]
        )
        avg_err_y, _, _, _ = binned_statistic_2d(
            gaze_x, gaze_y, err_y, "median", [x_edges, y_edges]
        )

        # 2. Predicted Vectors
        pred_x, pred_y = self.predict_grid(Xc, Yc)

        # Draw logic
        self.ax.clear()

        # Heatmap Background
        heatmap, _, _, _ = binned_statistic_2d(
            gaze_x, gaze_y, None, "count", [x_edges, y_edges]
        )
        self.ax.imshow(
            heatmap.T < 1,
            extent=[0, self.x_max, self.y_max, 0],
            cmap="Greys",
            alpha=0.15,
        )

        # Truth Quiver
        nan_mask = np.isnan(avg_err_x.T) | np.isnan(avg_err_y.T)
        self.ax.quiver(
            Xc[~nan_mask],
            Yc[~nan_mask],
            avg_err_x.T[~nan_mask],
            avg_err_y.T[~nan_mask],
            angles="xy",
            scale_units="xy",
            scale=1,
            color="gray",
            alpha=0.4,
        )

        # Prediction Quiver (Colored by distance from truth)
        diff = np.sqrt((pred_x - avg_err_x.T) ** 2 + (pred_y - avg_err_y.T) ** 2)
        diff_clipped = np.clip(diff, 0, 50)
        self.ax.quiver(
            Xc,
            Yc,
            pred_x,
            pred_y,
            diff_clipped,
            angles="xy",
            scale_units="xy",
            scale=1,
            cmap="jet",
            alpha=0.8,
        )

        # Formatting for RVIZ
        self.ax.set_xlim(0, self.x_max)
        self.ax.set_ylim(self.y_max, 0)
        self.ax.set_axis_off()  # Optional: Remove axis completely for a cleaner RVIZ look

        # Remove white margins completely
        self.fig.tight_layout(pad=0)
        self.ax.margins(0)

        # Convert canvas to ROS Image
        self.canvas.draw()
        rgba_buffer = self.canvas.buffer_rgba()
        img_np = np.asarray(rgba_buffer)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)

        img_msg = self.bridge.cv2_to_imgmsg(img_bgr, "bgr8")
        img_msg.header.stamp = self.get_clock().now().to_msg()
        img_msg.header.frame_id = "map"
        self.image_pub.publish(img_msg)


def main(args=None):
    rclpy.init(args=args)
    node = CalibrationLearner()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
