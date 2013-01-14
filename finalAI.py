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
    def __init__(self, mapFile, shootDistance):

        random.seed()

        ##constants (they never change)
        self.options, self.map = ParseMap(mapFile)
        self.shootDistance = int(shootDistance)
        self.mapSize = self.options['mapwidth']*35 ##Assumes it's a square
        self.radarSize = 256 #The same for all maps (No clue what happens if the map isn't a square)
        self.radarToScreen = self.mapSize / self.radarSize

        ##variables (they will change)
        self.count = 0
        self.mode = "move"
        self.ticksLeftToThrust = 0
        self.turnSpeedSet = False


    def tick(self):
        try:
            #
            # If we die then restart the state machine in the state "start"
            # The game will restart the spaceship at the base.
            #
            if not ai.selfAlive():
                self.count = 0
                self.mode = "move"
                self.wantedDirection = ""
                return

            self.count += 1

            if not self.turnSpeedSet:
                ai.setTurnSpeed(64)
                self.turnSpeedSet = True

            if self.count == 1: ##Avoid strange readings
                return

            #### Constants
            thrust = False
            minimumCheckDist = 30

            # Read the ships sensors.
            #

            #self readings
            selfX = ai.selfX()
            selfY = ai.selfY()
            selfRadarX = ai.selfRadarX()
            selfRadarY = ai.selfRadarY()
            selfVel = ai.selfSpeed()
            selfVelX = ai.selfVelX()
            selfVelY = ai.selfVelY()
            selfTracking = ai.selfTrackingDeg()
            selfHeading = ai.selfHeadingDeg()
  
            
            #enemy readings
            enemyRadarX = ai.closestRadarX()
            enemyRadarY = ai.closestRadarY()
            enemyVel = 0
            if enemyRadarX == -1:
                enemyExists = False
            else:
                enemyExists = True
            closestShip = ai.closestShipId()
            if closestShip != -1:
                enemyX = ai.screenEnemyXId(closestShip)
                enemyY = ai.screenEnemyYId(closestShip)
                enemyVel = ai.enemySpeedId(closestShip)
                enemyTracking = ai.enemyTrackingRadId(closestShip)
                enemyDistance = ai.enemyDistanceId(closestShip)

                if enemyTracking == None or math.isnan(enemyTracking):
                    enemyTracking = None
                    XComponentConst = 0
                    YComponentConst = 0
                else:
                    XComponentConst=math.cos(enemyTracking)
                    YComponentConst=math.sin(enemyTracking)

                enemyVelX = enemyVel*XComponentConst
                enemyVelY = enemyVel*YComponentConst
                if self.options['edgewrap']:
                    (enemyX, enemyY) = ClosestEnemy(selfX, selfY, enemyX, enemyY, self.mapSize)
            #
            # Done reading sensors
            #


            
            #
            # adjust sensor readings
            #
            if math.isnan(selfTracking): #cause nan is a bitch to check for, rather have None
                selfTracking = None
            checkDist = int(selfVel*20)
            if checkDist < minimumCheckDist:
                checkDist = minimumCheckDist
            
            # Fix radar readings so we go the shortest way to people when they
            # are on the other side of the edge of the map
            if self.options['edgewrap']:
                (enemyradarX, enemyRadarY)=ClosestEnemy(selfRadarX, selfRadarY,
                        enemyRadarX, enemyRadarY, self.radarSize)

            enemyRadarDistance = Distance(selfRadarX, selfRadarY, enemyRadarX, enemyRadarY)
            if not enemyExists:
                enemyRadarDistance = sys.maxsize #arbitrarily high number
            
            
            

            # At all times we want to check if we are crashing into anything,
            # unless we are already avoiding it.
            if CheckWall(checkDist, selfTracking):
                self.mode = "crashing"
                crashing = True
            else:
                crashing = False

            
            
            # If we are close to being hit, try and avoid
            # (Seldom works at final.xp's settings, where bullets are fast and
            # there are many of them, but it's worth a try!)
            
            #AttemptDodge(selfX, selfY, selfVel, selfVelX, selfVelY, selfTracking, selfHeading, self.options)
            #return
            
            
            
            if (Danger(selfX, selfY, selfVelX, selfVelY)):
                # TODO either flag mode = dodge and do something crazy if AttemptDodge() fails or just let it shoot (odds are if AttemptDodge finds nothing do it's too late)
                if (AttemptDodge(selfX, selfY, selfVel, selfVelX, selfVelY, selfTracking, selfHeading, self.options)):
                    # AttemptDodge() prints if it dodges
                    return
                else:
                    print("no direction was deemed safe")
                # else continue with what it would do otherwise

                

            print(self.count, self.mode)
            # State machine
#################################################
            if self.mode == "wait":
                thrust = False ###TODO: For some reason this doesn't go through,
                        ##after killing an enemy it thrusts like crazy. Bug in API?
                ai.setPower(5) ##Workaround so it doesn't thrust as hard
                if enemyExists:
                    self.mode = "move"
#################################################
            elif self.mode == "move":
                if enemyRadarDistance < self.shootDistance:
                    self.mode = "shoot"
                    return
                if not enemyExists:
                    self.mode = "wait"
                    return

                aimRadar = AimRadar(enemyRadarX, enemyRadarY,selfRadarX,selfRadarY)

                # Adjust course if we want to head into a wall
                avoidCrash = AvoidCrash(enemyRadarDistance*self.radarToScreen, aimRadar, 10)
                counterTracking = CounteractTracking(avoidCrash, selfTracking, self.options['friction'])
                self.wantedHeading = counterTracking
                TurnToAngle(selfHeading, self.wantedHeading)
                AdjustPower(enemyRadarDistance, selfVel)

                if AngleDiff(selfHeading, self.wantedHeading, True) < 45:
                    thrust = True
                else:
                    thrust = False


#################################################
            ##TODO: rewrite completely, checking for individual shots is kinda bad.
            ##Ideas: calculate mean mass of shots and avoid, or find "clean areas" and go to
            ##If possible check the math, sometimes we don't even dodge individual shots
            elif self.mode == "dodge":
                incAngle = Danger(selfX, selfY, selfVelX, selfVelY)
                if selfTracking == None:
                    self.mode = "move" ###Dirty fix until it's been rewritten
                    return
                if ai.angleDiff(int(incAngle), int(selfTracking+180)) < 5: ##TODO: Ugly hack
                    #print("Changing angle not to charge into shot")
                    self.wantedHeading = selfTracking+45 ###TODO doesn't work when selfTracking==None
                    self.wantedHeading = AdjustCourse(checkDist, self.wantedHeading)
                    TurnToAngle(selfHeading, self.wantedHeading)

                self.ticksLeftToThrust = 2
                self.mode = "thrust"

#################################################
            elif self.mode == "crashing":
                if not crashing:
                    self.mode = "move"
                    return
                self.wantedHeading = AvoidCrash(checkDist, selfTracking, 45)
                self.wantedHeading = CounteractTracking(self.wantedHeading, selfTracking, self.options['friction'])
                TurnToAngle(selfHeading, self.wantedHeading)
#################################################
            elif self.mode == "thrust":
                
                if self.ticksLeftToThrust > 0:
                    ai.setPower(55)
                    thrust = True
                    self.ticksLeftToThrust -= 1
                else:
                    self.wantedDirection = ""
                    self.mode = "move"
                    thrust = False
                
#################################################
            elif self.mode == "shoot":
                self.wantedHeading = 0
                if not enemyExists:
                    self.mode = "move"
                    return
                if enemyRadarDistance > self.shootDistance:
                    self.mode = "move"
                    return
                if closestShip == -1:
                    self.wantedHeading = AimRadar(enemyRadarX, enemyRadarY,selfRadarX,selfRadarY)
                else:
                    self.wantedHeading = AimScreen(selfX, selfY, selfVelX, selfVelY, enemyX, enemyY, enemyVelX, enemyVelY, self.options['shotspeed'])


                if CheckWall(enemyRadarDistance*self.radarToScreen, self.wantedHeading): ##Check if there's a wall in the way
                    self.wantedHeading = (self.wantedHeading+90)%360 ##TODO: improve, very simple atm
                    self.ticksLeftToThrust = 1
                    self.mode = "thrust"
                    return
                        ##TODO: approximate enemy velocity when on radar
                        #So the following can be used even when not on screen
                        #Use a list with past coordinates, and calculate mean velocity
                        #Use ai.closestShipId() and ai.closestRadarX/Y()
                        ##TODO: spread=1000/distance*speed*constant , figure out approximate constant
                if enemyVel == 0:
                    amountOfSpread = math.ceil(100/enemyRadarDistance)
                else:
                    amountOfSpread=math.ceil(1000/enemyRadarDistance)
                spread=random.randint(-amountOfSpread,amountOfSpread)
                TurnToAngle(selfHeading, self.wantedHeading+spread)
                ai.fireShot()
                
                ##Counteract recoil
                ai.setPower(8)
                thrust = True

#################################################

            if thrust:
                ai.thrust(1)
            else:
                ai.thrust(0)
#################################################
            #
            # End of state machine part
            #
        except:
            e = sys.exc_info()
            print("ERROR:", e[0], "\n", e[1], "\n", traceback.extract_tb(e[2]))





# This function simulates flight of 'ticks' time and returns where the ship would be after that time.
#
# 1 velocity = 0.0265472042476 squares per tick
# deduced from: 1280 squares traveled in 84 seconds at reported(api) velocity 41
#
# acceleration = 0.0191538270185 * power / mass
# deduced from: 0 to 500 reported(api) velocity in 18 seconds at 0 friction, 55 power and mass 20.0
#
# WARNING Unknown if friction or acceleration is applied first in a tick, i am assuming first for no particular reason.
# WARNING XPilot might not be following F = ma, the values here are measured using shipmass = 20.0.
def SimulateNewPosition(noOfTicks, power, mass, friction, aimDirection, selfX, selfY, selfVelX, selfVelY):
    #print()
    #print("SIMULATING", noOfTicks,power, mass, friction, aimDirection, selfX, selfY, selfVelX, selfVelY)
    velocityX = selfVelX / 35 # coords/tick
    velocityY = selfVelY / 35 # coords/tick
    accelerationX = math.cos(ai.degToRad(int(aimDirection))) * power * 0.0191538270185 / mass # sq/tick²
    accelerationY = math.sin(ai.degToRad(int(aimDirection))) * power * 0.0191538270185 / mass # sq/tick²
    posX = selfX
    posY = selfY
    #print("STARTacceleration per tick", accelerationX, accelerationY)
    #print("STARTvelocities translate into (sq/tick)", velocityX, velocityY)
    #print("STARTstartpos", posX, posY)
  
    for tickNo in range(noOfTicks):
        # Apply friction to current velocity.
        velocityX *= 1 - friction
        velocityY *= 1 - friction
        #print("applying", friction, "friction, velocities are:", velocityX, velocityY)
        # Apply 1 ticks' worth of acceleration to current velocity.
        velocityX += accelerationX
        velocityY += accelerationY
        # Apply 1 ticks' worth of velocity to position.
        posX += velocityX
        posY += velocityY
        #print("acceleration per tick", accelerationX, accelerationY)
        #print("velocities (sq/tick)", velocityX, velocityY)
        #print("pos", posX, posY)
    #print("ENDSIM")
    #print()
    return (posX, posY) # Return simulated destination.




# Returns True and dodges if it thinks it can, otherwise it does nothing and returns False.
# How it works: simulate thrusting in different angles and look for an outcome where the ship likely doesn't get shot
def AttemptDodge(selfX, selfY, selfVel, selfVelX, selfVelY, selfTracking, selfHeading, options):
    NO_OF_TICKS_TO_SIMULATE = 3
    DISTANCE_TO_CHECK_FOR_WALLS = 700
    if (selfTracking == None):
        selfTracking = 0
    selfX /= 35
    selfY /= 35
    print("requested dodge")
    
    for deviation in range(18, 181, 9):
        #print("testing deviation", deviation)
        for direction in (1, -1):
	  
            angleToTest = (selfTracking + direction * deviation) % 360
            # Hard coded value 55 power (55 is max)
            plannedCoords = SimulateNewPosition(NO_OF_TICKS_TO_SIMULATE, 55, options['shipmass'], options['friction'], angleToTest, selfX, selfY, selfVelX, selfVelY)
            # Is there a wall within 10 squares in that direction?
            distanceX = plannedCoords[0] - selfX
            distanceY = plannedCoords[1] - selfY
            plannedEffectiveDirection = (ai.radToDeg(math.atan2(distanceY, distanceX))) % 360
            #print("diff was X Y:", distanceX, distanceY, "which is a resulting angle:", plannedEffectiveDirection)
            # Hard coded value: 350, amount of pixels away from ship to test for walls.
            #print("walltest returns", CheckWall(DISTANCE_TO_CHECK_FOR_WALLS, plannedEffectiveDirection), "for direction", plannedEffectiveDirection)
            if (CheckWall(DISTANCE_TO_CHECK_FOR_WALLS, plannedEffectiveDirection) == False):
                #print("NO WALL")
                # Will any bullets hit the ship if it flies in this direction?
                # Use an average speed for bullet detection, it is not exact but hopefully good enough for a small distance.
                averageVelX = 35 * distanceX / NO_OF_TICKS_TO_SIMULATE
                averageVelY = 35 * distanceY / NO_OF_TICKS_TO_SIMULATE
                #print("average velocity for the move", averageVelX, averageVelY)
                #print("danger?", Danger(selfX * 35, selfY * 35, averageVelX, averageVelY))
                if (not Danger(selfX * 35, selfY * 35, averageVelX, averageVelY)):
                    # This is a good direction to dodge in; turn, thrust and return.
                    TurnToAngle(selfHeading, angleToTest)
                    ai.setPower(55)
                    ai.thrust(1)
                    print("accelerating towards", angleToTest, "current tracking", selfTracking, "resulting direction", plannedEffectiveDirection)
                    return True
            #else:
                #print("WALL, continuing")
            # There is no need to test these angles twice since they are the same in both directions.
            if(deviation == 0 or deviation == 180):
                break
    # No good direction to dodge found, report failure to caller.
    return False





# Returns the degree that is safest within distance, if there are several
# returns the one that is closest to direction
def AvoidCrash(distance, direction, buffer):
    if direction == None:
        return
    longestToWall = 0
    diff = sys.maxsize
    degrees = []
    #TODO: Write wrapper for CheckWall so we check the width of the ship and don't need as much buffer
    for degree in range(0, 181, 1): # Steps can be lowered for higher accuracy
        for mod in 1,-1:
            checkDirection = (direction+degree)%360
            result=CheckWall(distance, checkDirection)
            if result == False:
                if mod == 1:
                    return (direction+degree+buffer)%360
                else:
                    return (direction+degree-buffer)%360
            elif result > longestToWall:
                safestDegree = degree
    if degree >= 0:
        return (direction+degree+buffer)%360
    else:
        return (direction+degree-buffer)%360
        
# Checks if any bullet on screen is about to hit the ship (takes ship tracking into account)
# Returns the direction the bullet is coming from (in the case of multiple bullets about to hit, it only returns the direction of one of the bullets)
# Returns False if no bullets are in collision course.
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

            objectsCollide = ObjectsCollide(selfX, selfY, selfVelX, selfVelY, bulletX, bulletY, bulletVelX, bulletVelY)

            if objectsCollide:
                return True
    return False

# Returns an angle in order to aim in front of a moving enemy, taking into account its current tracking.
# Only works when an enemey is on screen because the api won't give the neccesary data otherwise.
def AimScreen(selfX, selfY, selfVelX, selfVelY, enemyX, enemyY, enemyVelX, enemyVelY, bulletVel):
# TODO: Can be improved, aim's a little bad in general. Maybe merge it with AimRadar.
    relativeX = enemyX - selfX
    relativeY = enemyY - selfY
    relativeVelX = enemyVelX - selfVelX
    relativeVelY = enemyVelY - selfVelY
    
    time = TimeOfImpact(relativeX, relativeY, relativeVelX, relativeVelY, bulletVel)

    targetX = enemyX+enemyVelX*time
    targetY = enemyY+enemyVelY*time
    targetAngle = ai.radToDeg(math.atan2(targetY-selfY,targetX-selfX))
    return targetAngle

# Calculates in which direction to thrust in order to travel in the desired direction, (compensates
# for our current tracking)
def CounteractTracking (heading, tracking, friction):
    if tracking == None:
        return heading
    pi=math.pi
    degToRad=pi/180
    radToDeg=180/pi
    headingRad = heading*degToRad # degrees->radians
    trackingRad = tracking*degToRad # degrees->radians
    resultMatrix = [math.cos(headingRad)-math.cos(trackingRad), math.sin(headingRad)-math.sin(trackingRad)]
    length = math.sqrt((resultMatrix[0]**2+resultMatrix[1]**2))
    if length == 0:
        return heading
    resultMatrix[0] /= length   # making the length of the vector 1
    resultMatrix[1] /= length

    # Two degrees (0<degree<2(pi) ) can have the same X value (x1, x2), and two
    # degrees can have the same Y value (y1, y2). We therefore have to test all
    # of them.
    x1 = ( math.acos(resultMatrix[0]) ) % ( 2 * pi )
    x2 = ( -x1 ) % ( 2 * pi )
    y1 = ( math.asin(resultMatrix[1]) ) % ( 2 * pi)
    y2 = ( pi - y1 ) % ( 2 * pi )

    resultRad = None

    for x in x1,x2:
        for y in y1,y2:
            if abs(x-y)<0.01: #x == y, due to python not having infinite decimals
                resultRad = x ## radians->degrees

    if resultRad == None:
        return heading
    result=resultRad*radToDeg
    weight=length*(1-friction*20) #TODO: Adjust constants
    avgResult=MeanDegree(heading, result, weight)
    return avgResult

# Mirror enemy on the other side of the map in order to track it across the edges.
def ClosestEnemy(selfX, selfY, enemyX, enemyY, mapConstant):
    minDistance = sys.maxsize #arbitrarily high number
    for i in range(-1, 2): #-1, 0, 1
        for j in range(-1, 2):
            x = enemyX + mapConstant * i
            y = enemyY + mapConstant * j
            distance = Distance(selfX, selfY, x, y)
            if distance < minDistance:
                minX = x
                minY = y
                minDistance = distance
    return (minX, minY)

def TimeOfImpact(relativeX, relativeY, targetSpeedX, targetSpeedY, bulletSpeed):
# Returns time until we will hit a moving target
# Used by AimScreen()
# inspired by: http://playtechs.blogspot.se/2007/04/aiming-at-moving-target.html
# WARNING This might not be correctly implemented.
    a = bulletSpeed * bulletSpeed - (targetSpeedX * targetSpeedX + targetSpeedY * targetSpeedY)
    b = relativeX * targetSpeedX + relativeY * targetSpeedY
    c = relativeX * relativeX + relativeY * relativeY
    d = b * b + a * c 
    if a == 0 or d < 0:
        return 0
    time = ( b + math.sqrt(d) ) / a
    if time < 0:
        return 0

    return time

# Returns True if two lines will cross, used by Danger()
def ObjectsCollide(x1, y1, xVel1, yVel1, x2, y2, xVel2, yVel2):
    if (xVel2-xVel1) == 0 or (yVel2-yVel1) == 0:
        return False
    timeX = (x2 - x1) / (xVel2 - xVel1)
    timeY = (y2 - y1) / (yVel2 - yVel1)
    if abs(timeX-timeY) < 2: ##One might want to adjust constant if not working
        return True
    else:
        return False

####Alternative WallFeeler
#I found out that ai.wallFeeler is much faster when you turn off the two flags
#the flags control whether it should draw lines on the map on where it is feeling
#With them turned on wallFeeler can take up to 1/10th of a second, turned off
#It takes max 5*10^-5 seconds. That makes it faster than the functions below
#and I keep them simply cause it was a lot of job to write them.
###
#def LineLineCollision(a, b):
##Returns whether line A  with line B
##all points are tuples of the format (x, y)
##And lines are tuples of points
##Taken from http://maryrosecook.com/post/how-to-do-2d-collision-detection
##I have not tried to understand how this math works
##Used my WallFeeler
#    d =  ((b[1][1] - b[0][1]) * (a[1][0] - a[0][0])) - ((b[1][0] - b[0][0]) * (a[1][1] - a[0][1]))
#    n1 = ((b[1][0] - b[0][0]) * (a[0][1] - b[0][1])) - ((b[1][1] - b[0][1]) * (a[0][0] - b[0][0]))
#    n2 = ((a[1][0] - a[0][0]) * (a[0][1] - b[0][1])) - ((a[1][1] - a[0][1]) * (a[0][0] - b[0][0]))
#
#    if d == 0:
#        if n1 == 0 and n2 == 0:
#            return False #Coincident
#        return False # Parallel
#
#    ua = n1 / d
#    ub = n2 / d
#
#    return 0 <= ua <= 1.0 and 0 <= ub <= 1.0
#
###This is a rewrite of ai.wallFeeler because it is too slow
##It takes coordinates from where we want to start looking for a wall
##As well as a direction and how far. 
#
##Returns True if there is a wall in direction, within checkDist, from coordinates on map
##edgeWrap decides whether the edges of the map should count as walls
##if returnDistance is true returns the distance to the wall, if no wall returns -1
#def WallFeeler(x, y, direction, checkDist, map, edgeWrap, returnDistance):
#    if direction==None:
#        return False
#    directionRad = direction * math.pi / 180 ##math.cos() and math.sin() uses radians
#    startPoint=(x / 35, y / 35)
#    checkDist /= 35 # pixel to square ratio
#    endPoint=(math.cos(directionRad) * checkDist + startPoint[0], math.sin(directionRad) * checkDist + startPoint[1])
#
#    
#    ## Which directions are the ship heading in?
#    # Directions are represented by values 0, 1, 2 and 3 for right, up, left and down respectively
#    # 0=right, 1=up, 2=left, 3=down
#    # Shorter than doing 8 if statements
#    if direction % 90 == 0: ##first we check for 0,90,180,270, where it only have one direction
#        directions = [direction/90]
#    else: ##And in all other cases it will have two directions, ( up or down ) and ( left or right )
#        directions = []
#        if 0 < direction < 180:
#            directions.append(1)
#        else:
#            directions.append(3)
#        if 90 < direction < 270:
#            directions.append(2)
#        else:
#            directions.append(0)
#
#    distance = CheckMap(startPoint, endPoint, directions, map, checkDist, edgeWrap)
#
#    if returnDistance:
#        if distance == -1:
#            return -1
#        else:
#            return distance*35 #squareToPixel
#    else:
#        if distance == -1:
#            return False
#        else:
#            return True
#
#
#def CheckMap(start, end, directions, map, checkDist, edgeWrap):
##This function will traverse through the same path that the ship will
##It goes to the next square by checking if the ship's trajectory
##intersects with one of the four lines around it (though which it checks
##depends on direction)
##With the lines drawn in a grid around it
##                                                                              
##        -                                                                     
##       |x|                                                                    
##        -                                                                     
## x is the current square
## Returns the incorrect distance, need another algorithm (see website)
##for that
#    cur=[math.floor(start[0]), math.floor(start[1])]
#    var=0
#    while Distance(start[0], start[1], cur[0], cur[1]) < checkDist - 1 and var < checkDist*1.5:
#        var += 1
#        if var >= checkDist*3: ##3 > sqrt(2)*2 which should be the max needed ever
#            print("Error in calculations, breaking out of endless loop")
#        for direction in directions:
#            if direction == 0: ##right
#                b=((1+(cur[0]), (cur[1])),(1+(cur[0]), 1+(cur[1])))
#                if LineLineCollision((start, end), b):
#                    cur[0] += 1
#                    break #We can only go in one direction
#            elif direction == 1: ##up
#                b=((cur[0]+1, cur[1]+1),(cur[0], cur[1]+1))
#                if LineLineCollision((start, end), b):
#                    cur[1] += 1
#                    break
#            elif direction == 2: ##left
#                b=(((cur[0]), 1+(cur[1])),((cur[0]), (cur[1])))
#                if LineLineCollision((start, end), b):
#                    cur[0] -= 1
#                    break
#            elif direction == 3: ##down
#                b=(((cur[0]), (cur[1])),(1+(cur[0]), (cur[1])))
#                if LineLineCollision((start, end), b):
#                    cur[1] -= 1
#                    break
#            else:
#                print("ERROR, invalid direction", direction)
#
#        #If there is a stone (True) in our current square
#        #Modulus to wrap around the map edges
#        if ( ( map[ cur[0] % len(map[0]) ] [ cur[1] % len(map) ] ) or
#        #If edgreWrap is turned off and current Square is not within the borders of the map
#                ( ( not edgeWrap ) and ( not 0 < cur[0] < len(map[0]) or not 0 < cur[1] < len(map) ) ) ):
#            return Distance(start[0], start[1], cur[0], cur[1])
#
#    return -1
        
# Returns distance to a wall, or False if none is found.
def CheckWall(dist, direction):
    if not dist or not direction:
        return False
    distance_to_wall = ai.wallFeeler(int(dist), int(direction), 0, 0)
    if int(dist) == distance_to_wall:
        return False
    else:
        return distance_to_wall

# ai.turnToDeg only turns counter-clockwise, this does the same thing except it turns in whichever direction is closer.
def TurnToAngle(currentDegree, targetDegree):
    if currentDegree == None or targetDegree == None:
        return
    ai.turn(int(AngleDiff(currentDegree, targetDegree)))
        # targetDegree-currentdegree%360, if < 180: +180, elif >180: -180
    return

# Returns direction to enemy based on radar readings.
def AimRadar(targetX,targetY,selfX,selfY):
    return (math.atan2(targetY-selfY,targetX-selfX))*180/math.pi
        
# Returns the distance between two coordinates, used by ClosestEnemy()
# Uses pythagoras theorem
def Distance(x0, y0, x1, y1):
    return math.sqrt((x1-x0)*(x1-x0)+(y1-y0)*(y1-y0))

def AdjustPower(dist, speed):
#TODO: Get sensible values here, also, power shouldn't only depend on ratio.
    optimalSpeed = dist/1.5
    ratio = speed/optimalSpeed
    if ratio > 2: 
        ai.setPower(5)
    elif ratio > 1:
        ai.setPower(10)
    elif ratio > 0.7:
        ai.setPower(20)
    elif ratio > 0.5:
        ai.setPower(40)
    else:
        ai.setPower(55)
    return

def ParseMap(mapFile):
    file = open(mapFile, "r")
    mapData = []
    options = {}
    readingMap = False
    for line in file:
        words = str.split(line)
        if readingMap:
            if len(words) > 0 and words[0] == "EndOfMapdata":
                break # Assume that the mapdata comes after the options
            mapData.append(line)
        elif len(words) > 0:
            w = words[0]
            if w == 'mapwidth':
                options['mapwidth'] = int(words[2])
            elif w == 'mapheight':
                options['mapheight'] = int(words[2])
            elif w == 'shipmass':
                options['shipmass'] = float(words[2])
            elif w == 'shotspeed':
                options['shotspeed'] = float(words[2])
            elif w == 'friction':
                options['friction'] = float(words[2])
            elif w == 'edgewrap':
                if words[2] == 'no':
                    options['edgewrap'] = False
                elif words[2] == 'yes':
                    options['edgewrap'] = True
            elif w == 'mapData:':
                readingMap = True
    mapList=ParseMapData(mapData)
    return options, mapList

def ParseMapData(mapData):
    mapList=[]
    lineList=[]
    for lineIndex in range(len(mapData)-1, -1, -1):
        line=mapData[lineIndex]
        for char in line:
            if char == 'x':
                lineList.append(True) # Rocks are represented with True
            elif char != '\n': # Easier than checking for ' ' and numbers (spawnpoints)
                lineList.append(False) # Space (and spawning points) are False
        mapList.append(lineList)
        lineList=[]
    
    return mapList

# Returns the mean degree of a and b, with weight applied to b
# example: meanDegree(0,90,1) returns 45
# example: meanDegree(0,90,2) returns 60
# example: meanDegree(0,90,0) returns 0
def MeanDegree(a, b, weight=1):
    mean1=(a+b*weight)/(weight+1)
    mean2=(mean1+180) % 360
    if AngleDiff(a, mean1, True) < AngleDiff(a, mean2, True):
        return mean1
    else:
        return mean2

# Same as ai.angleDiff, except it handles decimals
#Returns the absolute value if 'absolute' is set to True
def AngleDiff(angle1, angle2, absolute=False):
    diff = angle2 - angle1
    while diff < -180:
        diff += 360
    while diff > 180:
        diff -= 360
    if absolute:
        return abs(diff)
    else:
        return diff


# Parse command-line arguments.
if len(sys.argv) == 2:
    mapFile=sys.argv[1]
    shootDistance=500 #default
elif len(sys.argv) == 3:
    mapFile=sys.argv[1]
    shootDistance=sys.argv[2]
else:
    sys.exit("This AI requires that you supply the map file as the second argument, exiting.\nExample usage: $ python finalAI.py maps/final.xp")
    

bot = myai(mapFile, shootDistance)

def AI_loop():
    bot.tick()

AI_loop()


(options, args) = parser.parse_args()
port = 15345 + options.group
name = "H-CLASS_MINION-" + str(random.randint(100000, 999999))


# The command line arguments to xpilot can be given in the list in the second argument
# 
ai.start(AI_loop,[])#"-name", name, "-join", "-fuelMeter", "yes", "-showHUD", "no", "-port", str(port)])
