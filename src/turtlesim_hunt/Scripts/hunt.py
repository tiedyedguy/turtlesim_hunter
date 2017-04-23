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

#Variables to change
huntMethod = 1 #Which method to use, [0 .. 2] inclusive
targetHuntedTurtles = 2000 #How many turtles to hunt until the script ends
tolerance = 1 #The distance until we say the hunter finds the hunted.


#Global Variables I need elsewhere, don't change.
lastDistance = 1000000
timeToFind = 0
huntedTurtles = 0
totalHuntTime = 0


#Gets the Hunter's Pose, this is a subscriber call back
def hunterPose(data):
    global turtle1x, turtle1y, turtle1theta
    turtle1x = data.x
    turtle1y = data.y
    turtle1theta = data.theta

#Gets the Hunted's Pose, this is a subscriber call back
def huntedPose(data):
    global turtleTargetx, turtleTargety
    turtleTargetx = data.x
    turtleTargety = data.y


#Makes the hunting turtle's pen rainbowed.
def rainbowTrail():

    currentR = random.randint(0,255)
    currentG = random.randint(0,255)
    currentB = random.randint(0,255)
    setPen(currentR, currentG, currentB, 3, 0)

#Create a new Turtle to Hunt
def spawnNewTurtle():
    global turtleTargetx, turtleTargety
    turtleTargetx = random.randint(0, 11)
    turtleTargety = random.randint(0, 11)
    spawnTurtle(turtleTargetx,turtleTargety,0,"turtleTarget")
    #print "Target Spawned at (" + str(turtleTargetx) + "," + str(turtleTargety) + ") Distance: " + str(getDistance(turtle1x, turtle1y, turtleTargetx, turtleTargety))


#After finding a turtle, reset the stage for the next turtle
def resetHunt():
    global timeToFind, lastDistance
    try:
        killTurtle("turtleTarget")
    except:
        pass
    lastDistance = 1000000
    clearStage()
    spawnNewTurtle()
    timeToFind = time()

#Get the distance between two points on a plane.
def getDistance(x1, y1, x2, y2):
    return sqrt(pow((x2-x1),2) + pow((y2-y1),2))

#Method 0: My first idea, just spin the turtle until it is pointing at the target, then go get it.
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

#Method 1: From http://wiki.ros.org/turtlesim/Tutorials/Go%20to%20Goal, important to note, doesn't always reach the target!
def tutorialMethod():
    global motion
    targetTheta = atan2(turtleTargety - turtle1y, turtleTargetx - turtle1x)
    motion.linear.x = 1.5*getDistance(turtle1x, turtle1y, turtleTargetx, turtleTargety)
    motion.angular.z = 4 * (targetTheta - turtle1theta) 
    pub.publish(motion)


#Method 2, This is the Tutorial's Version, but I fixed the issue of the turtle hugging the wall and never making it to the target
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


#Found all the Turtles we wanted to find.
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
        pass
    clearStage()
    sys.exit()

#Main Function, sets up first hunt then loops.
def hunt():
    global totalHuntTime, huntedTurtles, turtle1x, turtle1y, turtleTargetx, turtleTargety

    #Set up board for first hunt.
    resetHunt()
    
    #Main Loop
    while not rospy.is_shutdown():

        #See how far away hunter is from hunted
        distance = getDistance(turtle1x, turtle1y, turtleTargetx, turtleTargety)
        #If <= tolerance then it is found
        if (distance <= tolerance):
            finalTime = time() - timeToFind
            totalHuntTime += finalTime
            huntedTurtles += 1
            print "Found #" + str(huntedTurtles) + " after " + str(finalTime) + " Current Avg: " + str(totalHuntTime / huntedTurtles)
            if (huntedTurtles == targetHuntedTurtles):
                finishHunt()
            resetHunt()   
        else: #Didn't find the target, time to use one of the methods!
            rainbowTrail()
            if (huntMethod == 0):
                findThetaMethod()
            if (huntMethod == 1):
                tutorialMethod()
            if (huntMethod == 2):
                tutorialMethodPlus()

        #Sleep to our publish rate       
        rate.sleep()
        


#Entry Point, sets up the ROS globals then calls hunt()
if __name__ == '__main__':
    try:
        global pub, rate, motion
        rospy.init_node('turtleHunt', anonymous=True)
        pub = rospy.Publisher('/turtle1/cmd_vel', Twist, queue_size = 10)
        rospy.Subscriber("/turtle1/pose", Pose, hunterPose) #Getting the hunter's Pose
        rospy.Subscriber("/turtleTarget/pose", Pose, huntedPose) #Getting the hunted's Pose
        rate = rospy.Rate(30) #The rate of our publishing
        clearStage = rospy.ServiceProxy('/clear', Empty) #Blanks the Stage
        spawnTurtle = rospy.ServiceProxy('/spawn', Spawn) #Can spawn a turtle
        killTurtle = rospy.ServiceProxy('/kill', Kill) #Delets a turtle
        setPen = rospy.ServiceProxy('/turtle1/set_pen', SetPen) #Sets the pen color of the hunter
        motion = Twist() #The variable we send out to publish

        hunt()

    except rospy.ROSInterruptException:
        pass
