import time

import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from geometry_msgs.msg import Twist


class HandCommandReceiver(Node):

    def __init__(self):
        super().__init__('hand_command_receiver')

        self.forward_speed = 0.15
        self.reverse_speed = 0.10
        self.turn_speed = 0.5

        self.timeout = 0.75

        self.last_command_time = None
        self.current_command = 'STOP'

        self.subscription = self.create_subscription(
            String,
            '/hand_command',
            self.command_callback,
            10
        )

        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.timer = self.create_timer(
            0.1,
            self.control_callback
        )

        self.get_logger().info('Hand receiver started')

    def command_callback(self, msg):

        command = msg.data.strip().upper()

        valid_commands = [
            'FORWARD',
            'REVERSE',
            'LEFT',
            'RIGHT',
            'STOP'
        ]

        if command not in valid_commands:
            self.current_command = 'STOP'
            self.last_command_time = None
            self.get_logger().warning('Invalid command')
            return

        self.current_command = command
        self.last_command_time = time.monotonic()

        self.get_logger().info(f'Received: {command}')

    def control_callback(self):

        velocity = Twist()

        if (
            self.last_command_time is None
            or time.monotonic() - self.last_command_time > self.timeout
        ):
            self.current_command = 'STOP'

        if self.current_command == 'FORWARD':
            velocity.linear.x = self.forward_speed

        elif self.current_command == 'REVERSE':
            velocity.linear.x = -self.reverse_speed

        elif self.current_command == 'LEFT':
            velocity.angular.z = self.turn_speed

        elif self.current_command == 'RIGHT':
            velocity.angular.z = -self.turn_speed

        else:
            velocity.linear.x = 0.0
            velocity.angular.z = 0.0

        self.cmd_pub.publish(velocity)


def main(args=None):

    rclpy.init(args=args)
    node = HandCommandReceiver()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        stop = Twist()
        node.cmd_pub.publish(stop)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()