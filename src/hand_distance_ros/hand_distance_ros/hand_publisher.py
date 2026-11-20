
import os
import time
from pathlib import Path
from collections import deque

import cv2
import numpy as np
import mediapipe as mp
import pyrealsense2 as rs

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32, String

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandPublisher(Node):

    def __init__(self):
        super().__init__('hand_publisher')

        # ROS publishers
        self.distance_pub = self.create_publisher(
            Float32,
            '/hand_distance',
            10
        )

        self.command_pub = self.create_publisher(
            String,
            '/hand_command',
            10
        )

        # Distance thresholds (metres)
        self.forward_threshold = 0.55
        self.reverse_threshold = 0.40

        # Gesture stability
        self.gesture_history = deque(maxlen=5)

        # MediaPipe model
        model_path_env = os.environ.get('HAND_LANDMARKER_MODEL')
        self.model_path = (
            Path(model_path_env).expanduser()
            if model_path_env
            else Path.home() / 'internship/hand_distance/hand_landmarker.task'
        )

        if not self.model_path.exists():
            raise FileNotFoundError(
                f'MediaPipe model not found: {self.model_path}'
            )

        base_options = python.BaseOptions(
            model_asset_path=str(self.model_path)
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.detector = vision.HandLandmarker.create_from_options(
            options
        )

        # RealSense configuration
        self.pipeline = rs.pipeline()
        config = rs.config()

        config.enable_stream(
            rs.stream.color,
            640,
            480,
            rs.format.bgr8,
            30
        )

        config.enable_stream(
            rs.stream.depth,
            640,
            480,
            rs.format.z16,
            30
        )

        self.profile = self.pipeline.start(config)

        self.align = rs.align(rs.stream.color)

        self.last_timestamp = 0

        # Camera timer
        self.timer = self.create_timer(
            0.033,
            self.process_camera
        )

        self.get_logger().info(
            'Hand publisher started successfully.'
        )

        self.get_logger().info(
            'Peace sign = LEFT | Shaka sign = RIGHT'
        )

    # --------------------------------------------------
    # Publish ROS command
    # --------------------------------------------------

    def publish_command(self, command):

        msg = String()
        msg.data = command

        self.command_pub.publish(msg)

    # --------------------------------------------------
    # Get palm distance from RealSense depth
    # --------------------------------------------------

    def get_hand_distance(self, depth_frame, landmarks):

        palm_ids = [0, 5, 9, 13, 17]

        height = depth_frame.get_height()
        width = depth_frame.get_width()

        x_values = []
        y_values = []

        for landmark_id in palm_ids:

            landmark = landmarks[landmark_id]

            x = int(landmark.x * width)
            y = int(landmark.y * height)

            x = max(0, min(width - 1, x))
            y = max(0, min(height - 1, y))

            x_values.append(x)
            y_values.append(y)

        center_x = int(np.mean(x_values))
        center_y = int(np.mean(y_values))

        depth_values = []

        for dy in range(-5, 6):
            for dx in range(-5, 6):

                px = center_x + dx
                py = center_y + dy

                if 0 <= px < width and 0 <= py < height:

                    distance = depth_frame.get_distance(px, py)

                    if 0.15 < distance < 3.0:
                        depth_values.append(distance)

        if not depth_values:
            return None, (center_x, center_y)

        distance = float(np.median(depth_values))

        return distance, (center_x, center_y)

    # --------------------------------------------------
    # Detect peace and shaka gestures
    # --------------------------------------------------

    def detect_hand_gesture(self, landmarks):

        index_up = landmarks[8].y < landmarks[6].y
        middle_up = landmarks[12].y < landmarks[10].y

        ring_up = landmarks[16].y < landmarks[14].y
        pinky_up = landmarks[20].y < landmarks[18].y

        thumb_tip = np.array([
            landmarks[4].x,
            landmarks[4].y
        ])

        index_mcp = np.array([
            landmarks[5].x,
            landmarks[5].y
        ])

        wrist = np.array([
            landmarks[0].x,
            landmarks[0].y
        ])

        middle_mcp = np.array([
            landmarks[9].x,
            landmarks[9].y
        ])

        palm_size = np.linalg.norm(
            wrist - middle_mcp
        )

        if palm_size < 0.001:
            return None

        thumb_distance = np.linalg.norm(
            thumb_tip - index_mcp
        )

        thumb_extended = (
            thumb_distance > 0.45 * palm_size
        )

        # Peace sign: index and middle fingers up
        if (
            index_up
            and middle_up
            and not ring_up
            and not pinky_up
        ):
            return 'LEFT'

        # Shaka sign: thumb and pinky extended
        if (
            thumb_extended
            and pinky_up
            and not index_up
            and not middle_up
            and not ring_up
        ):
            return 'RIGHT'

        return None

    # --------------------------------------------------
    # Stabilize gesture detection
    # --------------------------------------------------

    def stable_gesture(self, gesture):

        self.gesture_history.append(gesture)

        if gesture is None:
            return None

        if self.gesture_history.count(gesture) >= 3:
            return gesture

        return None

    # --------------------------------------------------
    # Select movement command
    # --------------------------------------------------

    def get_distance_command(self, distance):

        if distance is None:
            return 'STOP'

        if distance > self.forward_threshold:
            return 'FORWARD'

        if distance < self.reverse_threshold:
            return 'REVERSE'

        return 'STOP'

    # --------------------------------------------------
    # Draw hand landmarks
    # --------------------------------------------------

    def draw_hand(self, image, landmarks):

        height, width, _ = image.shape

        connections = (
            vision.HandLandmarksConnections.HAND_CONNECTIONS
        )

        for connection in connections:

            start = connection.start
            end = connection.end

            x1 = int(landmarks[start].x * width)
            y1 = int(landmarks[start].y * height)

            x2 = int(landmarks[end].x * width)
            y2 = int(landmarks[end].y * height)

            cv2.line(
                image,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

        for landmark in landmarks:

            x = int(landmark.x * width)
            y = int(landmark.y * height)

            cv2.circle(
                image,
                (x, y),
                4,
                (0, 0, 255),
                -1
            )

    # --------------------------------------------------
    # Main camera processing
    # --------------------------------------------------

    def process_camera(self):

        try:

            frames = self.pipeline.wait_for_frames(
                timeout_ms=1000
            )

            aligned_frames = self.align.process(frames)

            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()

            if not color_frame or not depth_frame:
                self.publish_command('STOP')
                self.gesture_history.clear()
                return

            image = np.asanyarray(
                color_frame.get_data()
            )

            rgb_image = cv2.cvtColor(
                image,
                cv2.COLOR_BGR2RGB
            )

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_image
            )

            timestamp_ms = int(time.monotonic() * 1000)

            if timestamp_ms <= self.last_timestamp:
                timestamp_ms = self.last_timestamp + 1

            self.last_timestamp = timestamp_ms

            results = self.detector.detect_for_video(
                mp_image,
                timestamp_ms
            )

            command = 'STOP'
            distance = None

            if results.hand_landmarks:

                landmarks = results.hand_landmarks[0]

                distance, center = self.get_hand_distance(
                    depth_frame,
                    landmarks
                )

                if distance is not None:

                    self.draw_hand(image, landmarks)

                    cv2.circle(
                        image,
                        center,
                        8,
                        (255, 0, 0),
                        -1
                    )

                    distance_command = (
                        self.get_distance_command(distance)
                    )

                    gesture = self.detect_hand_gesture(
                        landmarks
                    )

                    gesture_command = self.stable_gesture(
                        gesture
                    )

                    # Gestures override distance control
                    if gesture_command is not None:
                        command = gesture_command
                    else:
                        command = distance_command

                    cv2.putText(
                        image,
                        f'Distance: {distance:.2f} m',
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2
                    )

                else:

                    self.gesture_history.clear()
                    command = 'STOP'

            else:

                self.gesture_history.clear()
                command = 'STOP'

            # Publish distance
            if distance is not None:

                distance_msg = Float32()
                distance_msg.data = float(distance)

                self.distance_pub.publish(distance_msg)

            # Publish command
            self.publish_command(command)

            # Display command
            cv2.putText(
                image,
                f'Command: {command}',
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            cv2.imshow(
                'Hand Distance Control',
                image
            )

            cv2.waitKey(1)

        except Exception as error:

            self.get_logger().error(
                f'Camera processing error: {error}'
            )

            self.gesture_history.clear()
            self.publish_command('STOP')

    # --------------------------------------------------
    # Shutdown
    # --------------------------------------------------

    def destroy_node(self):

        try:
            self.publish_command('STOP')
            self.pipeline.stop()
            self.detector.close()
            cv2.destroyAllWindows()

        except Exception as error:
            self.get_logger().warning(
                f'Shutdown warning: {error}'
            )

        super().destroy_node()


def main(args=None):

    rclpy.init(args=args)

    node = None

    try:

        node = HandPublisher()

        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    except Exception as error:
        print(f'Publisher error: {error}')

    finally:

        if node is not None:
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

