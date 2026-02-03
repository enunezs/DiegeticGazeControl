#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import numpy as np
from sklearn.linear_model import Ridge

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
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
        self.declare_parameter("show_raw_samples", True)
        self.declare_parameter("show_binned_truth", True)
        self.declare_parameter("show_prediction", True)
        self.declare_parameter("publish_debug_image", True)

        # --- Internal Database ---
        self.db_gaze = []
        self.db_error = []
        self.coeffs_x = None
        self.coeffs_y = None

        # --- Plotting Setup ---
        self.x_max, self.y_max = 1600, 1200
        self.bins = 40  # Size of grid cells for binned/prediction plots

        # 800x600 output (1/2 scale of 1600x1200)
        self.fig, self.ax = plt.subplots(figsize=(8, 6), dpi=100)
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
            "Calibration Learner Initialized. Use 'ros2 param set' to toggle layers."
        )

    def segment_cb(self, msg: InteractionSegment):
        target = msg.target_pixel
        for s in msg.samples:
            self.db_gaze.append([s.x, s.y])
            self.db_error.append([s.x - target.x, s.y - target.y])

        if len(self.db_gaze) > 10:
            self.update_quadratic_model()
            if self.get_parameter("publish_debug_image").value:
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

    def predict_on_grid(self, Xc, Yc):
        """Helper to evaluate the current model on the visualization grid."""
        x_f, y_f = Xc.flatten(), Yc.flatten()
        A = np.c_[x_f**2, y_f**2, x_f * y_f, x_f, y_f, np.ones_like(x_f)]
        px = (A @ np.array(self.coeffs_x)).reshape(Xc.shape)
        py = (A @ np.array(self.coeffs_y)).reshape(Yc.shape)
        return px, py

    def publish_plot_image(self):
        if not self.db_gaze:
            return

        # Get current toggle states
        draw_raw = self.get_parameter("show_raw_samples").value
        draw_binned = self.get_parameter("show_binned_truth").value
        draw_pred = self.get_parameter("show_prediction").value

        # Data Prep
        gaze_pts = np.array(self.db_gaze)
        err_vecs = np.array(self.db_error)

        # Grid Prep (for Binned and Prediction layers)
        x_edges = np.arange(0, self.x_max + self.bins, self.bins)
        y_edges = np.arange(0, self.y_max + self.bins, self.bins)
        Xc, Yc = np.meshgrid(
            (x_edges[:-1] + x_edges[1:]) / 2, (y_edges[:-1] + y_edges[1:]) / 2
        )

        self.ax.clear()

        # LAYER 1: RAW SAMPLES (Colored by angle)
        if draw_raw:
            angles = np.arctan2(err_vecs[:, 1], err_vecs[:, 0])
            colors = cm.hsv((angles + np.pi) / (2 * np.pi))
            self.ax.quiver(
                gaze_pts[:, 0],
                gaze_pts[:, 1],
                err_vecs[:, 0],
                err_vecs[:, 1],
                color=colors,
                angles="xy",
                scale_units="xy",
                scale=1,
                alpha=0.4,
                width=0.0015,
            )

        # LAYER 2: BINNED TRUTH (Median vector per bin, Gray)
        avg_x, avg_y = None, None
        if draw_binned or draw_pred:
            avg_x, _, _, _ = binned_statistic_2d(
                gaze_pts[:, 0],
                gaze_pts[:, 1],
                err_vecs[:, 0],
                "median",
                [x_edges, y_edges],
            )
            avg_y, _, _, _ = binned_statistic_2d(
                gaze_pts[:, 0],
                gaze_pts[:, 1],
                err_vecs[:, 1],
                "median",
                [x_edges, y_edges],
            )

            if draw_binned:
                mask = ~np.isnan(avg_x.T)
                self.ax.quiver(
                    Xc[mask],
                    Yc[mask],
                    avg_x.T[mask],
                    avg_y.T[mask],
                    angles="xy",
                    scale_units="xy",
                    scale=1,
                    color="gray",
                    alpha=0.6,
                    width=0.003,
                )

        # LAYER 3: PREDICTION (Model output, Colored by residual vs truth)
        if draw_pred and self.coeffs_x is not None:
            px, py = self.predict_on_grid(Xc, Yc)

            # Color by distance from the binned truth (if truth exists in that cell)
            if avg_x is not None:
                diff = np.sqrt((px - avg_x.T) ** 2 + (py - avg_y.T) ** 2)
                diff_c = np.clip(diff, 0, 50)  # Max color at 50px error
                cmap = cm.jet
            else:
                diff_c = "blue"
                cmap = None

            self.ax.quiver(
                Xc,
                Yc,
                px,
                py,
                diff_c,
                angles="xy",
                scale_units="xy",
                scale=1,
                cmap=cmap,
                alpha=0.8,
                width=0.004,
            )

        # Final Render Settings
        self.ax.set_xlim(0, self.x_max)
        self.ax.set_ylim(self.y_max, 0)  # Flip for screen space
        self.ax.set_axis_off()
        self.fig.tight_layout(pad=0)

        # Publish
        self.canvas.draw()
        img_bgr = cv2.cvtColor(
            np.asarray(self.canvas.buffer_rgba()), cv2.COLOR_RGBA2BGR
        )
        msg = self.bridge.cv2_to_imgmsg(img_bgr, "bgr8")
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "gaze_debug"
        self.image_pub.publish(msg)


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
