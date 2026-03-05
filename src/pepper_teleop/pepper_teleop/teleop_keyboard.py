#!/usr/bin/env python3

import sys
import select
import termios
import tty
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

msg = """
Pepper Keyboard Teleop
---------------------------
Moving around:
   u    w    o
   a    k    d
   m    s    .

u/o : increase/decrease linear velocity (forward/backward)
a/d : turn left/right
k : stop
q/y : increase/decrease linear velocity by 10%
w/x : increase/decrease angular velocity by 10%

CTRL-C to quit
"""

moveBindings = {
    'w': (1, 0, 0), #forward
    'o': (1, 0, -1),
    'a': (0, 0, 1), #left 
    'd': (0, 0, -1), #right
    'u': (1, 0, 1),
    's': (-1, 0, 0), #backward
    '.': (-1, 0, 1),
    'm': (-1, 0, -1),
}

speedBindings = {
    'q': (1.1, 1), #increase speed
    'y': (0.9, 1), #decrease speed
    'w': (1, 1.1),
    'x': (1, 0.9),
}


class TeleopKeyboard(Node):
    def __init__(self):
        super().__init__('teleop_keyboard')
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)  # 10Hz
        self.velocity = Twist()
        self.key = None
        self.settings = termios.tcgetattr(sys.stdin)
        
        # Default speeds
        self.speed = 0.2  # Linear velocity in m/s
        self.turn = 0.5   # Angular velocity in rad/s
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        
        self.get_logger().info(msg)

    def get_key(self):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def timer_callback(self):
        key = self.get_key()
        if key in moveBindings.keys():
            self.x = moveBindings[key][0]
            self.y = moveBindings[key][1]
            self.th = moveBindings[key][2]
        elif key in speedBindings.keys():
            self.speed = self.speed * speedBindings[key][0]
            self.turn = self.turn * speedBindings[key][1]
            self.get_logger().info(f'Speed: {self.speed:.2f} m/s, Turn: {self.turn:.2f} rad/s')
        elif key == 'k':
            self.x = 0.0
            self.y = 0.0
            self.th = 0.0
        elif key == '\x03':  # CTRL+C
            self.stop_robot()
            raise KeyboardInterrupt
            
        # Update twist message
        twist = Twist()
        twist.linear.x = self.x * self.speed
        twist.linear.y = self.y * self.speed
        twist.angular.z = self.th * self.turn
        self.publisher.publish(twist)

    def stop_robot(self):
        twist = Twist()
        twist.linear.x = 0.0
        twist.linear.y = 0.0
        twist.angular.z = 0.0
        self.publisher.publish(twist)
        self.get_logger().info('Stopping robot')


def main(args=None):
    rclpy.init(args=args)
    
    teleop_keyboard = TeleopKeyboard()
    
    try:
        rclpy.spin(teleop_keyboard)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)
    
    teleop_keyboard.stop_robot()
    teleop_keyboard.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
