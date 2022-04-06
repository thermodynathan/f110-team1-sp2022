#!/usr/bin/env python
#F1/10 Team 1
from collections import deque
import math
import rospy
from race.msg import pid_input
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDrive
from std_msgs.msg import Float32MultiArray

class FTGController:
    car_radius = 0.15
    
    def __init__(self):
        rospy.init_node('ftg_controller', anonymous=False)
        rospy.on_shutdown(self.shutdown)
        self.command_pub = rospy.Publisher('/car_1/offboard/command', AckermannDrive, queue_size = 10)
        rospy.Subscriber("/car_1/scan", LaserScan, self.scan_listener_hook)
    
    def scan_listener_hook(self, scan):
        pass

    def preprocess_and_save_scan(self, laser_scan):
        '''
        self.ranges at the end of preprocessing should be a valid array of ranges, points where nan is reported is set to range_max
        '''
        self.angle_increment = laser_scan.angle_increment
        ranges = [raw if raw != math.nan else laser_scan.range_max for raw in laser_scan.ranges]
        self.ranges = ranges

    def disparity_extend(self, scan):
        num = len(scan.ranges)
        start_range = int(0.125*num) # ignore the first 30 degrees
        end_range = int(0.875*num) # ignore the last 30 degrees
        prev = scan.ranges[start_range]
        for k in range(start_range+1, end_range):
            curr = scan.ranges[k]
            if curr - prev > 1:
                angle = tan-1(prev/car_radius)
            if prev - curr < 1:
                # extend to the left
            prev = curr

        best_ray = start_range
        best_distance = 0
        for k in range(start_range+1, end_range):
            if scan.ranges[k] > best_distance:
                best_distance = scan.ranges[k]
                best_ray = k

if __name__ == '__main__':
    try:
        controller = FTGController()
    except:
        rospy.signal_shutdown()