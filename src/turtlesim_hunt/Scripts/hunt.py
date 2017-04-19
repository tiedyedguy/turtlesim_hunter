#!/usr/bin/env python


import rospy
from turtlesim.msg import *
from turtlesim.srv import *
from geometry_msgs.msg import Twist
from std_srvs.srv import *
import random
from time import time
from math import atan2,pi, sqrt, pow
import sys

def hunterPose(data):
    global turtle1x, turtle1y, turtle1theta
    turtle1x = data.x
    turtle1y = data.y
    turtle1theta = data.theta

def huntedPose(data):
    global turtleTargetx, turtleTargety
    turtleTargetx = data.x
    turtleTargety = data.y



pub = rospy.Publisher('/turtle1/cmd_vel', Twist, queue_size = 10)
rospy.init_node('turtleHunt', anonymous=True)
rospy.Subscriber("/turtle1/pose", Pose, hunterPose)
rospy.Subscriber("/turtleTarget/pose", Pose, huntedPose)

rate = rospy.Rate(30)
clearStage = rospy.ServiceProxy('/clear', Empty)
spawnTurtle = rospy.ServiceProxy('/spawn', Spawn)
killTurtle = rospy.ServiceProxy('/kill', Kill)
setPen = rospy.ServiceProxy('/turtle1/set_pen', SetPen)

tolerance = 1
huntMethod = 2


lastDistance = 1000000
motion = Twist()
timeToFind = 0
turtle1x = 0
turtle1y = 0
turtle1theta = 0
turtleTargetx = 11
turtleTargety = 11
huntedTurtles = 0
targetHuntedTurtles = 1000
totalHuntTime = 0
currentR = 0
currentG = 0
currentB = 0


def rainbowTrail():
    global currentR, currentG, currentB

    currentR = random.randint(0,255)
    currentG = random.randint(0,255)
    currentB = random.randint(0,255)

    setPen(currentR, currentG, currentB, 3, 0)

def spawnNewTurtle():
    global turtleTargetx, turtleTargety

    turtleTargetx = random.randint(0, 11)
    turtleTargety = random.randint(0, 11)
    spawnTurtle(turtleTargetx,turtleTargety,0,"turtleTarget")
    print "Target Spawned at (" + str(turtleTargetx) + "," + str(turtleTargety) + ") Distance: " + str(getDistance(turtle1x, turtle1y, turtleTargetx, turtleTargety))



def resetHunt():
    global timeToFind
    try:
        killTurtle("turtleTarget")
    except:
        print "No Turtle To Kill"

    
    
    clearStage()
    spawnNewTurtle()
    timeToFind = time()

def getDistance(x1, y1, x2, y2):
    return sqrt(pow((x2-x1),2) + pow((y2-y1),2))

def tutorialMethodPlus():
    global motion, lastDistance
    distance = getDistance(turtle1x, turtle1y, turtleTargetx, turtleTargety)
    targetTheta = atan2(turtleTargety - turtle1y, turtleTargetx - turtle1x)

    if (targetTheta<0):
       targetTheta += 2 * pi

    if (distance <= lastDistance):
        motion.linear.x = 1.5*distance
    else:
        motion.linear.x = .1
    lastDistance=distance
   
    change = 1
    if (targetTheta - turtle1theta <0):
        change = -1
    motion.angular.z = 4 * (targetTheta - turtle1theta) * change
    
        
        
    pub.publish(motion)



def tutorialMethod():
    global motion
    targetTheta = atan2(turtleTargety - turtle1y, turtleTargetx - turtle1x)


    motion.linear.x = 1.5*getDistance(turtle1x, turtle1y, turtleTargetx, turtleTargety)
   
    change = 1

    motion.angular.z = 4 * (targetTheta - turtle1theta) * change
    
        
        
    pub.publish(motion)

def findThetaMethod():
    global motion
    targetTheta = atan2(turtleTargety - turtle1y, turtleTargetx - turtle1x)
    if (targetTheta<0):
        targetTheta += 2 * pi
    
    if (abs(targetTheta - turtle1theta) < 0.1):
        motion.linear.x = 10
        motion.angular.z = 0
    else:
        motion.linear.x = 0
        motion.angular.z = 3
    
        
        
    pub.publish(motion)

    
def finishHunt():
    global motion
    motion.linear.x = 0
    motion.angular.z = 0
    pub.publish(motion)
    print "Total Turtles Hunted"
    print huntedTurtles
    print "Total Seconds"
    print totalHuntTime
    print "Average Find Time"
    print totalHuntTime / huntedTurtles
    try:
        killTurtle("turtleTarget")
    except:
        print "No Turtle To Kill"

    
    
    clearStage()
    sys.exit()


def hunt():
    global totalHuntTime, huntedTurtles, turtle1x, turtle1y, turtleTargetx, turtleTargety
    resetHunt()
    
    while not rospy.is_shutdown():
        distance = getDistance(turtle1x, turtle1y, turtleTargetx, turtleTargety)
        
        if (distance <= tolerance):
            

            finalTime = time() - timeToFind
            totalHuntTime += finalTime
            huntedTurtles += 1
            print "Found #" + str(huntedTurtles) + " after " + str(finalTime) + " Current Avg: " + str(totalHuntTime / huntedTurtles)
            

            if (huntedTurtles == targetHuntedTurtles):
                finishHunt()
            resetHunt()
            rate.sleep()

        rainbowTrail()

        if (huntMethod == 0):
            findThetaMethod()
        if (huntMethod == 1):
            tutorialMethod()
        if (huntMethod == 2):
            tutorialMethodPlus()
        


        rate.sleep()
        

        
        





if __name__ == '__main__':
    try:
        hunt()
    except rospy.ROSInterruptException:
        pass
