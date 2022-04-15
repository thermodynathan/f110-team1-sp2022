#!/usr/bin/env python
#F1/10 Team 1
from collections import deque
import math
import rospy
from race.msg import pid_input
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDrive
from std_msgs.msg import Header

class FTGController:

    car_radius = 0.15
    max_steering_angle = math.pi/4 # 45 degrees
    safe_distance = 0.4
    full_speed_distance = 5
    max_speed = 40

    def __init__(self):
        rospy.init_node('ftg_controller', anonymous=False)
        # rospy.on_shutdown(self.shutdown)
        self.command_pub = rospy.Publisher('/car_1/offboard/command', AckermannDrive, queue_size = 10)
        self.extend_pub = rospy.Publisher('extended', LaserScan, queue_size=10)
        rospy.Subscriber("/car_1/scan", LaserScan, self.scan_listener_hook)
    
    def scan_listener_hook(self, laser_scan):
        self.preprocess_and_save_scan(laser_scan)
        angle = self.disparity_extend(self.ranges)
        # self.generate_and_publish_control_message(angle, 4)
        pass

    def preprocess_and_save_scan(self, laser_scan):
        '''
        self.ranges at the end of preprocessing should be a valid array of ranges, points where nan is reported is set to range_max
        '''
        self.raw_scan = laser_scan
        self.angle_increment = laser_scan.angle_increment
        ranges = [raw if raw != float('nan') else laser_scan.range_max for raw in laser_scan.ranges]
        for index in range(len(ranges)):
            if ranges[index] < 0.05:
                ranges[index] = 0.05
        self.ranges = ranges

    def angle_to_index(self, angle):
        index = int(float(angle-self.raw_scan.angle_min)/self.raw_scan.angle_increment)
        return index

    def index_to_angle(self, index):
        # print((self.raw_scan.angle_max - self.raw_scan.angle_min) * 180 / math.pi)
        angle = index*1.0/len(self.ranges) * (self.raw_scan.angle_max - self.raw_scan.angle_min) + self.raw_scan.angle_min
        return angle

    def get_frontal_clearance(self):
        start = self.angle_to_index(-math.pi/10)
        end = self.angle_to_index(math.pi/10)
        return min(self.ranges[start:end])

    def generate_and_publish_control_message(self, target_angle, target_distance):
        angle = self.generate_steering_angle(target_angle)
        speed = self.generate_speed(target_distance)
        command = self.make_control_message(angle, 17)
        self.command_pub.publish(command)

    def generate_steering_angle(self, target_angle):
        angle = target_angle/FTGController.max_steering_angle * 100
        if angle >= 100:
            angle = 100
        if angle <= -100:
            angle = -100
        if min(self.ranges) < FTGController.car_radius:
            print("minimum range: %f" % min(self.ranges))
            angle = 0
        return angle
        
    def generate_speed(self, target_distance):
        front_margin = target_distance - FTGController.safe_distance
        if front_margin < 0:
            speed = 0
        else:
            speed = front_margin / FTGController.full_speed_distance
        if speed > FTGController.max_speed:
            speed = FTGController.max_speed
        return speed

    def make_control_message(self, angle, speed):
        command = AckermannDrive()
        command.steering_angle = angle
        command.speed = speed
        return command

    def disparity_extend(self, ranges):
        num = len(ranges)
        start_range = 0
        end_range = num
        disparity_distance = 1
        prev = ranges[start_range]
        k = start_range+1
        while k < end_range:
            try:
                curr = ranges[k]
                if abs(curr - prev) > disparity_distance:
                    angle = (FTGController.car_radius/prev)
                    num_rays = int(angle/self.raw_scan.angle_increment)
                    for i in range(k-num_rays, k+num_rays):
                        # print(angle, num_rays ,i, len(ranges))
                        if i < num and i > 0:
                            ranges[i] = 0
                    k += num_rays
                prev = curr
                k += 1
            except IndexError:
                k += 1
        return ranges
        
        new_ranges = ranges[start_range+1:end_range]
        msg = LaserScan()
        msg.angle_min = -math.pi/2
        msg.angle_max = math.pi/2
        msg.angle_increment = math.pi/len(new_ranges)
        msg.range_min = min(new_ranges)
        msg.range_max = max(new_ranges)
        msg.ranges = new_ranges
        msg.header.frame_id = "extend"
        self.extend_pub.publish(msg)

    def best_ray(self, ranges):
        self.disparity_extend(ranges)
        num = len(ranges)
        start_range = int(0.125 * num)  # ignore the first 30 degrees
        end_range = int(0.875 * num)  # ignore the last 30 degrees
        prev = ranges[start_range]
        k = start_range + 1

        best_ray = start_range
        best_distance = 0
        for k in range(start_range+1, end_range):
            if ranges[k] > best_distance+0.1:
                best_distance = ranges[k]
                best_ray = k

        # print("best ray: %f" % best_ray)
        # print("best ray: %f" % (float(best_ray)/num))
        best_angle = self.index_to_angle(best_ray) * 180/math.pi
        print("best angle: %f" % best_angle)
        return best_angle

if __name__ == '__main__':
    controller = FTGController()
    rospy.spin()
    # try:
    # except:
    #     rospy.signal_shutdown()
