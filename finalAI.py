import libpyAI as ai

import random
import sys
import math

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
        self.wantedMaximalSpeed = 9999
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
            closestShip = ai.closestShipId()
            if closestShip != -1:
                enemyX=ai.screenEnemyXId(closestShip)
                enemyY=ai.screenEnemyYId(closestShip)
                enemyVel=ai.enemySpeedId(closestShip)
                enemyTracking=ai.enemyTrackingRadId(closestShip)
                if enemyTracking == None or math.isnan(enemyTracking):
                    enemyTracking=0
                enemyVelX=enemyVel*math.cos(enemyTracking)
                enemyVelY=enemyVel*math.sin(enemyTracking)
                closestEnemyScreen=ClosestEnemy(closestShip, selfX, selfY, enemyX, enemyY, 2240)
                enemyX=closestEnemyScreen[0]
                enemyY=closestEnemyScreen[1]
            #
            # Done reading sensors
            #


            
            
            #
            # Constants
            #
            ai.setTurnSpeed(32)
            bulletVel=21
            #
            # adjust sensor readings
            #
            if math.isnan(selfTracking): #cause nan is a bitch
                selfTracking=0
            checkDist=int(selfVel*30)
            if checkDist < 100:
                checkDist = 100
            
            # Fix radar readings so we go the shortest way to people when they are on the other side of the edge of the map
            closestEnemyRadar=ClosestEnemy(selfRadarX, selfRadarY, enemyRadarX, enemyRadarY, 256)
            enemyRadarX=closestEnemyRadar[0]
            enemyradarY=closestEnemyRadar[1]
            
        except:
            e = sys.exc_info()
            print ("ERROR in Sensor readings: ", e)

        try:

            print(self.count, self.mode)

                                

            # At all times we want to check if we are crashing into anything, unless we are already avoiding it
            if self.mode != "thrust" and CheckWall(checkDist, selfTracking):
                self.wantedDirection, self.wantedHeading = AvoidCrash(checkDist, selfTracking, self.wantedDirection)
                self.mode = "turn"
            
            
            # If we are close to being hit, try and avoid (Seldom works at final.xp's settings, but it's worth a try!)
            if self.mode != "turn" and Danger(selfX, selfY, selfVelX, selfVelY) != False:
                self.mode = "dodge"
            
            #
            # Start of state machine part
            #
#################################################
            if self.count == 2 and self.mode != "thrust":
                self.mode = "move"

#################################################
            elif self.mode == "move":
                if closestShip != -1:
                    self.mode = "shoot"
                    return
                
                ai.fireShot()
                self.wantedHeading=FlyTo(enemyRadarX, enemyRadarY,selfRadarX,selfRadarY)

                # Adjust course if we want to head into a wall
                self.wantedHeading=AdjustCourse(checkDist, self.wantedHeading)

                TurnToAngle(selfHeading, self.wantedHeading)
                if selfVel < self.wantedMaximalSpeed and ai.angleDiff(int(selfHeading), int(self.wantedHeading)) < 90:
                    ai.thrust(1)
                else:
                    ai.thrust(0)

#################################################
            elif self.mode == "dodge":
                incAngle=Danger(selfX, selfY, selfVelX, selfVelY)
                if ai.angleDiff(int(incAngle), int(selfTracking+180)) < 5: ##TODO: Works really bad
                    print("Changing angle not to charge into shot")
                    self.wantedHeading=selfTracking+45
                    self.wantedHeading=AdjustCourse(checkDist, self.wantedHeading)
                    TurnToAngle(selfHeading, self.wantedHeading)

                self.ticksLeftToThrust=2
                self.mode = "thrust"

#################################################
            elif self.mode == "turn":
                ai.thrust(0)
                self.wantedHeading=AdjustCourse(checkDist, self.wantedHeading) ##TODO: Check if this is needed or so
                TurnToAngle(selfHeading, self.wantedHeading)
                
                if abs(ai.angleDiff (int(selfHeading), int(self.wantedHeading))) < 10:
                    self.ticksLeftToThrust=5
                    self.mode = "thrust"

#################################################
            elif self.mode == "thrust":
                
                if self.ticksLeftToThrust > 0:
                    ai.thrust(1)
                    self.ticksLeftToThrust -= 1
                else:
                    self.wantedDirection = ""
                    self.mode = "move"
                    ai.thrust(0)
                
#################################################
            elif self.mode == "shoot":
                self.wantedHeading=0
                ai.thrust(0)
                if closestShip == -1:
                    self.mode = "move"
                else:
                    TurnToAngle(selfHeading, Shoot(closestShip, selfX, selfY, selfVelX, selfVelY, enemyX, enemyY, enemyVelX, enemyVelY, enemyTracking, bulletVel))
                    ai.fireShot()
#################################################
            #
            # End of state machine part
            #
        except:
            e = sys.exc_info()
            print ("ERROR in statemachine: ", e)

# Adjust the course if we want to head into a wall
def AdjustCourse(checkDist, wantedHeading):
    try:
        i=0
        degreeChange=20
        distCurrent=CheckWall(checkDist, wantedHeading)
        while distCurrent and i < 2:
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
    except:
        e = sys.exc_info()
        print ("ERROR in function AdjustCourse: ", e)

# Adjusts heading if we are crashing
def AvoidCrash(checkDist, selfTracking, wantedDirection ):
    try:
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
    except:
        e = sys.exc_info()
        print ("ERROR in function CheckCrash: ", e)

#Calculates the Danger of every bullet in the immediate viscinity of the ship, using above functions. If there is no Danger it will return False. If there is Danger of being hit, it will return either positive or negative depending on which direction is better to make an evasive manouver. 
def Danger(selfX, selfY, selfVelX, selfVelY):
    try:
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
    except:
        e = sys.exc_info()
        print ("ERROR in function Danger: ", e)

#Calculates where to shoot to hit a moving enemy, and adds some spread cause in reality the enemy will never stay on it's course.
def Shoot(id, selfX, selfY, selfVelX, selfVelY, enemyX, enemyY, enemyVelX, enemyVelY, enemyTracking, bulletVel):
    try:
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
    except:
        e = sys.exc_info()
        print ("ERROR in function Shoot: ", e)

#Creates clones of the closest enemy so we can track him through the edges of the map
def ClosestEnemy(selfX, selfY, enemyX, enemyY, mapConstant):
    try:
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
    except:
        e = sys.exc_info()
        print ("ERROR in function ClosestEnemy: ", e)

#Returns the time when we will hit a moving target, for further calculations. Used by Shoot()
def TimeOfImpact(relativeX, relativeY, targetSpeedX, targetSpeedY, bulletSpeed): #inspired by: http://playtechs.blogspot.se/2007/04/aiming-at-moving-target.html
    try:
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
    except:
        e = sys.exc_info()
        print ("ERROR in function TimeOfImpact: ", e)

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
    try:
        if not dist or not direction:
            return False
        distance_to_wall = ai.wallFeeler(int(dist), int(direction), 1, 1)
        if dist == distance_to_wall:
            return False
        else:
            return distance_to_wall
    except:
        e = sys.exc_info()
        print ("ERROR in function CheckWall: ", e)

    return False

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
