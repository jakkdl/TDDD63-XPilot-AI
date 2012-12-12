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
                closestEnemyScreen=ClosestEnemyScreen(closestShip, selfX, selfY, enemyX, enemyY)
                enemyX=closestEnemyScreen[0]
                enemyY=closestEnemyScreen[1]
            #
            # Done reading sensors
            #


            
            
            
            #ai.setTurnSpeed(64.0) ## uncomment if running on xpilot-ai
            ai.setTurnSpeed(32)
            bulletVel=21
            if math.isnan(selfTracking): #cause nan is a bitch to check for
                selfTracking=0
            self.checkDist=int(selfVel*30)
            if self.checkDist < 100:
                self.checkDist = 100
            
            closestEnemyRadar=ClosestEnemyRadar(selfRadarX, selfRadarY, enemyRadarX, enemyRadarY)
            enemyRadarX=closestEnemyRadar[0]
            enemyradarY=closestEnemyRadar[1]
            
        except:
            e = sys.exc_info()
            print ("ERROR in Sensor readings: ", e)

        try:

            #print(self.count, self.mode)

            # Adjust course if we want to head into a wall
            self.wantedHeading=AdjustCourse(self.checkDist, self.wantedHeading)
                                
                

            
            # At all times we want to check if we are crashing into anything, unless we are already avoiding it
            if CheckWall(self.checkDist, selfTracking) and self.mode != "thrust":
                if self.wantedDirection == "": #If we haven't yet decided in what direction to turn to avoid the wall, test the different directions and decide
                    distPositive=CheckWall(self.checkDist, selfTracking+45)
                    distNegative=CheckWall(self.checkDist, selfTracking-45)
                    if distPositive < distNegative:
                        self.wantedDirection = "positive"
                    else:
                        self.wantedDirection = "negative"
                
                if self.wantedDirection == "positive": #Now we have decided and stick to it until the wall is no longer a danger
                    self.wantedHeading = selfTracking+90%360
                elif self.wantedDirection == "negative":
                    self.wantedHeading = selfTracking-90%360

                self.mode = "turn"
            
            # If we are close to being hit, try and avoid (Seldom works at final.xp's settings, but it's worth a try!)
            if Danger(selfX, selfY, selfVelX, selfVelY) != False and self.mode != "turn":
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
                TurnToAngle(selfHeading, self.wantedHeading) # We turn before calculating at what angle the opponent is as to not overwrite the changes done by CourseAdjuster
                self.wantedHeading=FlyTo(enemyRadarX, enemyRadarY,selfRadarX,selfRadarY)
                if selfVel < self.wantedMaximalSpeed and ai.angleDiff(int(selfHeading), int(self.wantedHeading)) < 90:
                    ai.thrust(1)
                else:
                    ai.thrust(0)

#################################################
            elif self.mode == "dodge":
                incAngle=Danger(selfX, selfY, selfVelX, selfVelY)
                if ai.angleDiff(int(incAngle), int(selfTracking+180)) < 5:
                    ai.turnToDeg(int(selfTracking+90))

                self.ticksLeftToThrust=2
                self.mode = "thrust"

#################################################
            elif self.mode == "turn":
                ai.thrust(0)
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


def ClosestEnemyRadar(selfX, selfY, enemyX, enemyY):
    try:
        minDistance=256 #arbitrarily high number
        for i in range(-1, 2):
            for j in range(-1, 2):
                x=enemyX+256*i
                y=enemyY+265*j
                distance=Distance(selfX, selfY, x, y)
                if distance < minDistance:
                    minX=x
                    minY=y
                    minDistance=distance
        return (minX, minY)
    except:
        e = sys.exc_info()
        print ("ERROR in function ClosestEnemyRadar: ", e)

def ClosestEnemyScreen(closestShip, selfX, selfY, enemyX, enemyY):
    try:
        minDistance=100000000000000000000 #arbitrary high number
        for i in range(-1, 2):
            for j in range(-1, 2):
                x=enemyX+2240*i
                y=enemyY+2240*j
                distance=Distance(selfX, selfY, x, y)
                if distance < minDistance:
                    minX=x
                    minY=y
                    minDistance=distance
        return (minX, minY)
    except:
        e = sys.exc_info()
        print ("ERROR in function ClosestEnemyScreen: ", e)

def Distance(x0, y0, x1, y1):
    return math.sqrt((x1-x0)*(x1-x0)+(y1-y0)*(y1-y0))

def TurnToAngle(currentDegree, targetDegree):
    ai.turn(ai.angleDiff(int(currentDegree), int(targetDegree))) #targetDegree-currentdegree%360, if < 180: +180, elif >180: -180
    return

def Shoot(id, selfX, selfY, selfVelX, selfVelY, enemyX, enemyY, enemyVelX, enemyVelY, enemyTracking, bulletVel):
    try:
        if id == -1:
            return False

        if enemyTracking == None:
            return False
        
        relativeX=enemyX-selfX
        relativeY=enemyY-selfY
        relativeVelX=enemyVelX-selfVelX
        relativeVelY=enemyVelY-selfVelY


        time=TimeOfImpact(relativeX, relativeY, relativeVelX, relativeVelY, bulletVel)

        targetX=enemyX+enemyVelX*time
        targetY=enemyY+enemyVelY*time
        targetAngle=math.atan2(targetY-selfY,targetX-selfX)
        targetAngle=ai.radToDeg(targetAngle)

        return targetAngle+random.randint(-30,30)
    except:
        e = sys.exc_info()
        print ("ERROR in function Shoot: ", e)

def TimeOfImpact(relativeX, relativeY, targetSpeedX, targetSpeedY, bulletSpeed): #inspired by: http://playtechs.blogspot.se/2007/04/aiming-at-moving-target.html
    try:
        a=bulletSpeed * bulletSpeed - (targetSpeedX*targetSpeedX+targetSpeedY*targetSpeedY)
        b=relativeX*targetSpeedX+relativeY*targetSpeedY
        c=relativeX*relativeX+relativeY*relativeY
        d=b*b+a*c
        time=0

        if a == 0:
            return 0

        if d >= 0:
            time = ( b + math.sqrt(d) ) /a
            if time < 0:
                time = 0

        return time
    except:
        e = sys.exc_info()
        print ("ERROR in function TimeOfImpact: ", e)
	
def FlyTo(targetX,targetY,selfX,selfY):
    try:
        targetAngle=math.atan2(targetY-selfY,targetX-selfX)
        targetAngle=ai.radToDeg(float(targetAngle))

        return targetAngle+random.randint(-10,10)
    except:
        e = sys.exc_info()
        print ("ERROR in function FlyTo: ", e)
        
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



def LinesCross(x1, y1, xVel1, yVel1, x2, y2, xVel2, yVel2):
    try: 
        timeX=(x2-x1)/(xVel2-xVel1)
        timeY=(y2-y1)/(yVel2-yVel1)
        if abs(timeX-timeY) < 2:
            return True
        else:
            return False
    except:
        e = sys.exc_info()
        print ("ERROR in function LinesCross: ", e)

#Calculates the Danger of every shot in the immediate viscinity of the ship, using above functions. If there is no Danger it will return False. If there is Danger of being hit, it will return either positive or negative depending on which direction is better to make an evasive manouver. 
def Danger(selfX, selfY, selfVelX, selfVelY):
    try:
        for i in range(99):
            if ai.shotAlert(i) == -1:
                return False
            else:
                shotX = ai.shotX(i)
                shotY = ai.shotY(i)
                shotTrack = ai.shotVelDir(i)
                shotVel = ai.shotVel(i)
                shotVelX = shotVel*math.cos(shotTrack)
                shotVelY = shotVel*math.sin(shotTrack)

                linesCross=LinesCross(selfX, selfY, selfVelX, selfVelY, shotX, shotY, shotVelX, shotVelY)

                if linesCross==False:
                    return False
                else:
                    return math.atan2(shotX-selfX, shotY-selfY)
    except:
        e = sys.exc_info()
        print ("ERROR in function Danger: ", e)

            



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
