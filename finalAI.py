import libpyAI as ai

import random
import sys
import math
import time ###TODO: remove this when done testing
import traceback

from optparse import OptionParser

parser = OptionParser()

parser.add_option ("-g", "--group", action="store", type="int", 
                   dest="group", default=0, 
                   help="The group number. Used to avoid port collisions when" 
                   " connecting to the server.")


class myai:

    #
    # This function is executed when the class instance (the object) is created.
    #
    def __init__(self):
        self.count = 0
        self.wantedHeading = 90
        self.mode = "init"
        random.seed()
        self.minimumcheckDist = 100
        self.ticksLeftToThrust = 0
        self.wantedDirection=""

    def tick(self):
        try:

            #
            # If we die then restart the state machine in the state "start"
            # The game will restart the spaceship at the base.
            #
            if not ai.selfAlive():
                self.count = 0
                self.mode = "init"
                self.wantedDirection=""
                return

            self.count += 1

            #
            # Constants
            #
            ai.setTurnSpeed(32)
            bulletVel=21
            shootDistance=50
            mapSize=2240 ##Assumes it's a square
            radarSize=256 ##Same on all maps
            radarToScreen=mapSize/radarSize
            thrust=False

            #
            # Read the ships sensors.
            #

            #self readings
            selfX = ai.selfX()
            selfY = ai.selfY()
            selfRadarX = ai.selfRadarX()
            selfRadarY = ai.selfRadarY()
            selfVelX = ai.selfVelX()
            selfVelY = ai.selfVelY()
            selfVel = ai.selfSpeed()

            selfTracking = ai.selfTrackingDeg()
            selfHeading = ai.selfHeadingDeg()
  
            
            #enemy readings
            enemyRadarX=ai.closestRadarX()
            enemyRadarY=ai.closestRadarY()
            if enemyRadarX == -1:
                enemyExists=False
            else:
                enemyExists=True
            closestShip = ai.closestShipId()
            if closestShip != -1:
                enemyX=ai.screenEnemyXId(closestShip)
                enemyY=ai.screenEnemyYId(closestShip)
                enemyVel=ai.enemySpeedId(closestShip)
                enemyTracking=ai.enemyTrackingRadId(closestShip)
                if enemyTracking==None:
                    enemyVelX=0
                    enemyVelY=0
                elif math.isnan(enemyTracking):
                    enemyTracking=None
                    enemyVelX=0
                    enemyVelY=0
                else:
                    enemyVelX=enemyVel*math.cos(enemyTracking)
                    enemyVelY=enemyVel*math.sin(enemyTracking)
                (enemyX, enemyY)=ClosestEnemy(selfX, selfY, enemyX, enemyY, mapSize)
#                closestEnemyScreen=ClosestEnemy(selfX, selfY, enemyX, enemyY, mapSize)
#                enemyX=closestEnemyScreen[0]
#                enemyY=closestEnemyScreen[1]
            #
            # Done reading sensors
            #


            
            #
            # adjust sensor readings
            #
            if math.isnan(selfTracking): #cause nan is a bitch
                selfTracking=None
            checkDist=int(selfVel*40)
            if checkDist < 150:
                checkDist = 150
            
            # Fix radar readings so we go the shortest way to people when they are on the other side of the edge of the map
            (enemyradarX, enemyRadarY)=ClosestEnemy(selfRadarX, selfRadarY, enemyRadarX, enemyRadarY, radarSize)
#            closestEnemyRadar=ClosestEnemy(selfRadarX, selfRadarY, enemyRadarX, enemyRadarY, radarSize)
#            enemyRadarX=closestEnemyRadar[0]
#            enemyradarY=closestEnemyRadar[1]
            enemyRadarDistance=Distance(selfRadarX, selfRadarY, enemyRadarX, enemyRadarY)
            if not enemyExists:
                enemyRadarDistance=99999 #arbitrarily high number
            

            print(self.count, self.mode)

                                

            # At all times we want to check if we are crashing into anything, unless we are already avoiding it
            if self.mode != "thrust" and CheckWall(checkDist, selfTracking):
                self.wantedDirection, self.wantedHeading = AvoidCrash(checkDist, selfTracking, self.wantedDirection)
                crashing=True
                self.mode = "turn"
            else:
                crashing=False
            
            
            # If we are close to being hit, try and avoid (Seldom works at final.xp's settings, but it's worth a try!)
            if self.mode != "turn" and Danger(selfX, selfY, selfVelX, selfVelY) != False:
                self.mode = "dodge"
            #
            # Start of state machine part
            #
#################################################
            start=time.time()
            if self.count == 2 and self.mode != "thrust":
                self.mode = "move"

#################################################
            elif self.mode == "wait":
                thrust=False ###TODO: For some reason this doesn't go through, after killing an enemy it thrusts like crazy. Bug in API?
                ai.setPower(5)
                if enemyExists:
                    self.mode = "move"
#################################################
            elif self.mode == "move":
                if enemyRadarDistance < shootDistance:
                    self.mode = "shoot"
                    return
                if not enemyExists:
                    self.mode = "wait"
                    return

                #ai.fireShot() ######weeeelll, this was said to be ugly
                self.wantedHeading=FlyTo(enemyRadarX, enemyRadarY,selfRadarX,selfRadarY)

                # Adjust course if we want to head into a wall
                self.wantedHeading=AdjustCourse(checkDist, self.wantedHeading)
                #print(self.wantedHeading, selfTracking, CounteractTracking(self.wantedHeading, selfTracking))
                self.wantedHeading=CounteractTracking(self.wantedHeading, selfTracking)

                TurnToAngle(selfHeading, self.wantedHeading)
                AdjustPower(enemyRadarDistance)
                if selfVel < ai.angleDiff(int(selfHeading), int(self.wantedHeading)) < 90:
                    thrust=True
                else:
                    thrust=False


#################################################
            elif self.mode == "dodge": ##TODO: rewrite
                incAngle=Danger(selfX, selfY, selfVelX, selfVelY)
                if selfTracking == None:
                    return
                if ai.angleDiff(int(incAngle), int(selfTracking+180)) < 5: ##TODO: Works really bad
                    #print("Changing angle not to charge into shot")
                    self.wantedHeading=selfTracking+45 ###TODO doesn't work when selfTracking==None
                    self.wantedHeading=AdjustCourse(checkDist, self.wantedHeading)
                    TurnToAngle(selfHeading, self.wantedHeading)

                self.ticksLeftToThrust=2
                self.mode = "thrust"

#################################################
            elif self.mode == "turn":
                if crashing == False:
                    self.mode="move"
                self.wantedHeading=AdjustCourse(checkDist, self.wantedHeading) ##TODO: Check if this is needed or so
                self.wantedHeading=CounteractTracking(self.wantedHeading, selfTracking)
                TurnToAngle(selfHeading, self.wantedHeading)
                
                #AdjustPower(enemyRadarDistance, distanceToWall) ##TODO: Do some math on trackingVelocity and distance to wall and adjust power accordingly
                ai.setPower(55)
                
                if abs(ai.angleDiff (int(selfHeading), int(self.wantedHeading))) < 10:
                    thrust=True
                else:
                    thrust=False

#################################################
            elif self.mode == "thrust":
                
                if self.ticksLeftToThrust > 0:
                    ai.setPower(55)
                    #print("THRUUUUSTING")
                    thrust=True
                    self.ticksLeftToThrust -= 1
                else:
                    self.wantedDirection = ""
                    self.mode = "move"
                    thrust=False
                
#################################################
            elif self.mode == "shoot":
                self.wantedHeading=0
                if enemyRadarDistance > shootDistance:
                    self.mode = "move"
                if closestShip == -1:
                    self.wantedHeading=FlyTo(enemyRadarX, enemyRadarY,selfRadarX,selfRadarY)
                else:
                    self.wantedHeading=Shoot(closestShip, selfX, selfY, selfVelX, selfVelY, enemyX, enemyY, enemyVelX, enemyVelY, enemyTracking, bulletVel)


                if CheckWall(enemyRadarDistance*radarToScreen, self.wantedHeading): ##Check if there's a wall in the way
                    self.wantedHeading=(self.wantedHeading+90)%360
                    self.ticksLeftToThrust = 1
                    self.mode="thrust"
                    return
                
                TurnToAngle(selfHeading, self.wantedHeading)
                ai.fireShot()
                ##Counteract recoil
                ai.setPower(8)
                thrust=True
            #print(thrust)
            timeTaken=(time.time() - start)
            if timeTaken > 0.01:
                #print(self.count, self.mode, timeTaken)
                pass
            if thrust:
                ai.thrust(0)
                ai.thrust(1)
            else:
                ai.thrust(1)
                ai.thrust(0)
#################################################
            #
            # End of state machine part
            #
        except:
            e = sys.exc_info()
            print("ERROR:", e[0], ";", e[1], ";", traceback.extract_tb(e[2]))

# Adjust the course if we want to head into a wall
def AdjustCourse(checkDist, wantedHeading):
    i=0
    degreeChange=20
    distCurrent=CheckWall(checkDist, wantedHeading)
    while distCurrent and i < 4:
        distPositive=CheckWall(checkDist, wantedHeading+degreeChange)
        distNegative=CheckWall(checkDist, wantedHeading-degreeChange)
        lastOperation="plus"
        if distPositive > distNegative or distPositive == False:
            wantedHeading += degreeChange
            distCurrent=distPositive
            lastOperation="plus"
        elif distPositive < distNegative or distPositive == False:
            wantedHeading -= degreeChange
            distCurrent=distNegative
            lastOperation="minus"
        elif lastOperation=="plus":
            wantedHeading += degreeChange
        elif lastOperation=="minus":
            wantedHeading -= degreeChange
        i+=1
    return wantedHeading

# Adjusts heading if we are crashing
def AvoidCrash(checkDist, selfTracking, wantedDirection ):
    if wantedDirection == "": #If we haven't yet decided in what direction to turn to avoid the wall, test the different directions and decide
        distPositive=CheckWall(checkDist, selfTracking+45)
        distNegative=CheckWall(checkDist, selfTracking-45)
        if distPositive < distNegative:
            wantedDirection = "positive"
        else:
            wantedDirection = "negative"
    
    if wantedDirection == "positive": #Now we have decided and stick to it until the wall is no longer a danger
        wantedHeading = selfTracking+90%360
    elif wantedDirection == "negative":
        wantedHeading = selfTracking-90%360

    return wantedDirection, wantedHeading

#Calculates the Danger of every bullet in the immediate viscinity of the ship, using above functions. If there is no Danger it will return False. If there is Danger of being hit, it will return either positive or negative depending on which direction is better to make an evasive manouver. 
def Danger(selfX, selfY, selfVelX, selfVelY):
    for i in range(99):
        if ai.shotAlert(i) == -1:
            return False
        else:
            bulletX = ai.shotX(i)
            bulletY = ai.shotY(i)
            bulletTrack = ai.shotVelDir(i)
            bulletVel = ai.shotVel(i)
            bulletVelX = bulletVel*math.cos(bulletTrack)
            bulletVelY = bulletVel*math.sin(bulletTrack)

            linesCross=LinesCross(selfX, selfY, selfVelX, selfVelY, bulletX, bulletY, bulletVelX, bulletVelY)

            if linesCross==False:
                return False
            else:
                return math.atan2(bulletX-selfX, bulletY-selfY)

#Calculates where to shoot to hit a moving enemy, and adds some spread cause in reality the enemy will never stay on it's course.
def Shoot(id, selfX, selfY, selfVelX, selfVelY, enemyX, enemyY, enemyVelX, enemyVelY, enemyTracking, bulletVel):
    if id == -1 or enemyTracking == None:
        return False
    
    relativeX=enemyX-selfX
    relativeY=enemyY-selfY
    relativeVelX=enemyVelX-selfVelX
    relativeVelY=enemyVelY-selfVelY
    
    time=TimeOfImpact(relativeX, relativeY, relativeVelX, relativeVelY, bulletVel)

    targetX=enemyX+enemyVelX*time
    targetY=enemyY+enemyVelY*time
    targetAngle=ai.radToDeg(math.atan2(targetY-selfY,targetX-selfX))
    return targetAngle+random.randint(-30,30)

#Calculates in which direction to thrust to get to the wanted heading, compensating
def CounteractTracking (heading, tracking):
    if tracking==None:
        return heading
    heading=heading*math.pi/180 ##degrees->radians
    tracking=tracking*math.pi/180 ##degrees->radians
    resultMatrix=[math.cos(heading)-math.cos(tracking), math.sin(heading)-math.sin(tracking)]
    length=math.sqrt((resultMatrix[0]**2+resultMatrix[1]**2))
    if length==0:
        return heading
    resultMatrix[0]/=length
    resultMatrix[1]/=length
    a=math.acos(resultMatrix[0])
    b=-a
    c=math.asin(resultMatrix[1])
    d=c+math.pi/2

    for x in a,b:
        for y in c,d:
            if abs(x-y)<0.01:
                if abs(a-c)>0.01 and abs(a-d)>0.01 and abs(b-c)>0.01:
                    print(a,b,c,d)
                return x*180/math.pi ## radians->degrees

    #print(heading, tracking, a,b,c,d,"fail") ##Debugging
    return heading*180/math.pi

#Creates clones of the closest enemy so we can track him through the edges of the map
def ClosestEnemy(selfX, selfY, enemyX, enemyY, mapConstant):
    minDistance=1000000000000000000000 #arbitrarily high number
    for i in range(-1, 2):
        for j in range(-1, 2):
            x=enemyX+mapConstant*i
            y=enemyY+mapConstant*j
            distance=Distance(selfX, selfY, x, y)
            if distance < minDistance:
                minX=x
                minY=y
                minDistance=distance
    return (minX, minY)

#Returns the time when we will hit a moving target, for further calculations. Used by Shoot()
def TimeOfImpact(relativeX, relativeY, targetSpeedX, targetSpeedY, bulletSpeed): #inspired by: http://playtechs.blogspot.se/2007/04/aiming-at-moving-target.html
    a=bulletSpeed * bulletSpeed - (targetSpeedX*targetSpeedX+targetSpeedY*targetSpeedY)
    b=relativeX*targetSpeedX+relativeY*targetSpeedY
    c=relativeX*relativeX+relativeY*relativeY
    d=b*b+a*c
    if a == 0 or d < 0:
        return 0
    time = ( b + math.sqrt(d) ) /a
    if time < 0:
        return 0

    return time

#Returns whether two lines will cross, used by Danger()
def LinesCross(x1, y1, xVel1, yVel1, x2, y2, xVel2, yVel2):
    if (xVel2-xVel1) == 0 or (yVel2-yVel1) == 0:
        return False
    timeX=(x2-x1)/(xVel2-xVel1)
    timeY=(y2-y1)/(yVel2-yVel1)
    if abs(timeX-timeY) < 2:
        return True
    else:
        return False

#Returns whether, or how long it is to a wall
def CheckWall(dist, direction):
    if not dist or not direction:
        return False
    distance_to_wall = ai.wallFeeler(int(dist), int(direction), 1, 1)
    if int(dist) == distance_to_wall:
        return False
    else:
        return distance_to_wall

#Wrapper to make use ai.turn as simple as ai.turnToDeg.
def TurnToAngle(currentDegree, targetDegree):
    ai.turn(ai.angleDiff(int(currentDegree), int(targetDegree))) #targetDegree-currentdegree%360, if < 180: +180, elif >180: -180
    return

#Returns the angle to turn to, used in Move
def FlyTo(targetX,targetY,selfX,selfY):
    return ai.radToDeg(math.atan2(targetY-selfY,targetX-selfX))+random.randint(-10,10)
        
#returns the distance to the target, used by ClosestEnemy()
def Distance(x0, y0, x1, y1):
    return math.sqrt((x1-x0)*(x1-x0)+(y1-y0)*(y1-y0))

def AdjustPower(dist):
    if dist < 50:
        ai.setPower(5)
    elif dist < 100:
        ai.setPower(20)
    elif dist < 150:
        ai.setPower(35)
    else:
        ai.setPower(55)
    return


bot = myai()

def AI_loop():
    bot.tick()

AI_loop()


(options, args) = parser.parse_args()
port = 15345 + options.group
name = random.randint(1, 999999)


# The command line arguments to xpilot can be given in the list in the second argument
# 
ai.start(AI_loop,[])#"-name", name, "-join", "-fuelMeter", "yes", "-showHUD", "no", "-port", str(port)])
