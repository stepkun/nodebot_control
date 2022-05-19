
from cmath import pi
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from geometry_msgs.msg import Quaternion

from PySide2.QtCore import QThreadPool, QRunnable, Slot


class DataPublisher(Node):
    '''
    ROS2 publisher node
    Inherits from ROS2's class Node.

    '''
    def __init__(self, data_store):
        super().__init__('data_publisher')
        self.topic_vel = '/nodebot1/cmd_vel'
        self.topic_cam = '/nodebot1/cmd_cam'
        self.scale = [math.pi/2] * 3
        self.data = data_store
        self.cmd_vel_publisher = self.create_publisher(Twist, self.topic_vel, 10)  # command for robot speed
        self.cmd_cam_publisher = self.create_publisher(Quaternion, self.topic_cam, 10)  # command for camera orientation
        timer_period = 0.05  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        #print(self.data)
        msg_vel = Twist()
        #dict = self.data.dict.copy()
        # publish cmd_vel from right stick
        # do transformation into robot x,y,z - axis and scale with maximum possible speeed
        # TODO: make this configurable
        msg_vel.linear.x =   0.05 * self.data.dict['rightStick']['y']
        msg_vel.angular.z = -0.25 * self.data.dict['rightStick']['z']
        self.get_logger().debug('Publishing ' + self.topic_vel + ': "%s"' % msg_vel)
        self.cmd_vel_publisher.publish(msg_vel)

        msg_cam = Quaternion()
        # publish cmd_cam from left stick
        # data with respect to robot x,y,z - axis
        half_roll  = self.data.dict['leftStick']['x'] * self.scale[0] / 2
        half_pitch = self.data.dict['leftStick']['y'] * self.scale[1] / 2
        half_yaw   = self.data.dict['leftStick']['z'] * self.scale[2] / 2
        print(2 * half_roll, 2 * half_pitch, 2 * half_yaw)

        cy = math.cos(half_yaw)
        sy = math.sin(half_yaw)
        cp = math.cos(half_pitch)
        sp = math.sin(half_pitch)
        cr = math.cos(half_roll)
        sr = math.sin(half_roll)

        msg_cam.w = cr * cp * cy + sr * sp * sy
        msg_cam.x = sr * cp * cy - cr * sp * sy
        msg_cam.y = cr * sp * cy + sr * cp * sy
        msg_cam.z = cr * cp * sy - sr * sp * cy
        self.get_logger().debug('Publishing ' + self.topic_cam + ': "%s"' % msg_cam)
        self.cmd_cam_publisher.publish(msg_cam)

class RosPublisherWorker(QRunnable):
    '''
    Worker thread handling ros publishing
    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    '''
    def __init__(self, data_store):
        super(RosPublisherWorker, self).__init__()
        self.data = data_store

        self.do_run = True


    @Slot()  # QtCore.Slot
    def run(self):
        #print("publisher started")
        rclpy.init(args=None)

        publisher = DataPublisher(self.data)
 
        while self.do_run:
            rclpy.spin_once(publisher)

        #print("publisher ended")

        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        publisher.destroy_node()
        rclpy.shutdown()
 

    def stop(self):
        self.do_run = False



class RosPublisher:
    def __init__(self, data_store):
        self.threadpool = QThreadPool()
        self.publisher = RosPublisherWorker(data_store)
        self.threadpool.start(self.publisher)


    def stop(self):
        self.publisher.stop()
