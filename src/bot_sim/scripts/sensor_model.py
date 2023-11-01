#!/usr/bin/env python3

import rospy
import raycast as rc
from geometry_msgs.msg import PoseWithCovarianceStamped, Pose
from tf.transformations import euler_from_quaternion
import numpy as np

from std_msgs.msg import Float64

class SensorModel:
    def __init__(self):
        # given location, probability of gaining the current measurement
        prob = 0
        self.rc = rc.Raycast()

        self.interval = 5
        # standard deviation of our sensor model
        self.sigma_r = 3.0 
        self.N = 1

    # robotPose: [x,y,theta]
    def CorrectionOneParticle(self,robotPose):
        rays = self.rc.RaycastDDA(robotPose,self.interval)
        total_likelihood = 1.0
        for i in range(len(rays)):
            measurement_likelihood = self.NormalPDFtimesN(rays[i],self.rc.getRanges()[i*self.interval],self.N)
            total_likelihood *= measurement_likelihood
        return total_likelihood
    
    def NormalPDFtimesN(self,mu,x,N):
        denom = self.sigma_r*np.sqrt(2*np.pi)
        num = self.N*np.exp(-(x-mu)**2/(2 * (self.sigma_r**2)))
        return num/denom

pose = Pose()
clicked = False
def Clicked(msg):
    global pose
    global clicked

    pose = msg.pose.pose
    clicked = True

if __name__=="__main__":
    rospy.init_node("sensor_model_p")
    sensor_model = SensorModel()
    sub = rospy.Subscriber("/initialpose",PoseWithCovarianceStamped,Clicked,queue_size=10)

    pub = rospy.Publisher("/point_likelihood",Float64,queue_size=10)
    rate = rospy.Rate(20)
    likelihood = -1
    while not rospy.is_shutdown():
        if clicked == True:
            clicked = False
            orientation_list = [
                    pose.orientation.x,
                    pose.orientation.y,
                    pose.orientation.z,
                    pose.orientation.w]
            angular_z = euler_from_quaternion(orientation_list)[2]
            likelihood = sensor_model.CorrectionOneParticle([pose.position.x,pose.position.y,angular_z])
            pub.publish(likelihood)
        # print("point likelihood:",likelihood)
        rate.sleep()

