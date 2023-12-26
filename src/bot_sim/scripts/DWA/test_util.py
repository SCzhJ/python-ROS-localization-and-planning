#!/usr/bin/env python3

import rospy
from visualization_msgs.msg import Marker
from tf.transformations import euler_from_quaternion
from geometry_msgs.msg import PoseStamped, PointStamped, Twist
from nav_msgs.msg import Path
from tf.transformations import quaternion_from_euler
from nav_msgs.msg import Odometry
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class OdomSubscriber:
    def __init__(self):
        self.odom_sub = rospy.Subscriber('/odom', Odometry, self.odom_callback)
        self.robot_pose = None

    def odom_callback(self, msg):
        self.robot_pose = msg.pose.pose

    def get_pose(self):
        if self.robot_pose is None:
            return None, None, None
        x = self.robot_pose.position.x
        y = self.robot_pose.position.y
        theta = euler_from_quaternion([self.robot_pose.orientation.x, 
                                       self.robot_pose.orientation.y, 
                                       self.robot_pose.orientation.z, 
                                       self.robot_pose.orientation.w])[2]
        return x, y, theta

class PointListPublisher:
    def __init__(self, marker_id: int = 5, topic_name: str = 'point_list_marker'):
        self.marker_pub = rospy.Publisher(topic_name, Marker, queue_size=10)
        self.marker = Marker()
        self.marker.header.frame_id = "map"
        self.marker.header.stamp = rospy.Time.now()
        self.marker.ns = "points"
        self.marker.id = marker_id
        self.marker.type = Marker.POINTS
        self.marker.action = Marker.ADD
        self.marker.scale.x = 0.02
        self.marker.scale.y = 0.02
        self.marker.color.r = 1.0
        self.marker.color.g = 0.0
        self.marker.color.b = 0.0
        self.marker.color.a = 1.0
        self.marker.pose.orientation.x = 0.0
        self.marker.pose.orientation.y = 0.0
        self.marker.pose.orientation.z = 0.0
        self.marker.pose.orientation.w = 1.0
        self.marker.lifetime = rospy.Duration()

    def publish_point_list(self, point_list):
        self.marker.points = point_list
        self.marker_pub.publish(self.marker)

class PathPublisher:
    def __init__(self):
        self.path_pub = rospy.Publisher('path_topic', Path, queue_size=10)
        self.path_msg = Path()
        self.path_msg.header.frame_id = "map"
    
    def calc_path_from_point_list(self, point_list):
        self.path_msg.poses = []
        for i in range(len(point_list)):
            pose_stamped = PoseStamped()
            pose_stamped.header.frame_id = "map"
            pose_stamped.header.stamp = rospy.Time.now()
            pose_stamped.pose.position.x = point_list[i].x
            pose_stamped.pose.position.y = point_list[i].y
            q = quaternion_from_euler(0, 0, point_list[i].z)
            pose_stamped.pose.orientation.x = q[0]
            pose_stamped.pose.orientation.y = q[1]
            pose_stamped.pose.orientation.z = q[2]
            pose_stamped.pose.orientation.w = q[3]
            self.path_msg.poses.append(pose_stamped)

    def publish_path(self):
        self.path_msg.header.stamp = rospy.Time.now()
        self.path_pub.publish(self.path_msg)
        rospy.loginfo("path found and published")

class ClickedPointSubscriber:
    def __init__(self):
        self.clicked_point_sub = rospy.Subscriber('/clicked_point', PointStamped, self.clicked_point_callback)
        self.clicked_point = None
        self.clicked = False

    def clicked_point_callback(self, msg):
        self.clicked_point = msg.point
        self.clicked = True
        rospy.loginfo("Clicked point received: %s", self.clicked_point)
    
    def set_clicked_false(self):
        self.clicked = False
    
    def get_clicked(self):
        return self.clicked
    
    def get_clicked_point(self):
        return self.clicked_point

class PointStampedPublisher:
    def __init__(self, topic_name: str = 'point_topic'):
        self.point_pub = rospy.Publisher(topic_name, PointStamped, queue_size=10)

    def publish_point(self, point):
        point_stamped = PointStamped()
        point_stamped.header.stamp = rospy.Time.now()
        point_stamped.header.frame_id = "map"
        point_stamped.point = point
        self.point_pub.publish(point_stamped)

class CostVisualizer:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.cost_list = []

    def update(self, frame):
        self.ax.clear()
        self.ax.plot(self.cost_list)
        self.ax.set_title('Cost over time')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Cost')

    def visualize(self, cost_list):
        self.cost_list = cost_list
        ani = FuncAnimation(self.fig, self.update, frames=range(len(self.cost_list)))
        plt.show(block=False)
        plt.pause(0.1)

class CmdVelPublisher:
    def __init__(self, topic_name: str = 'cmd_vel'):
        self.cmd_vel_pub = rospy.Publisher(topic_name, Twist, queue_size=10)

    def publish_cmd_vel(self, linear_velocity, angular_velocity):
        cmd_vel = Twist()
        cmd_vel.linear.x = linear_velocity
        cmd_vel.angular.z = angular_velocity
        self.cmd_vel_pub.publish(cmd_vel)