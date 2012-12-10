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
    """Simple wall avoidance"""

    #
    # This function is executed when the class instance (the object) is created.
    #
    def __init__(self):
        self.count = 0
        self.wanted_minimal_speed = 0
        self.wanted_heading = 90
        self.mode = "init"        # used to store the current state of the state machine
        random.seed()
        self.checkDist = 600




    def tick(self):
        try:

            #
            # If we die then restart the state machine in the state "start"
            # The game will restart the spaceship at the base.
            #
            if not ai.selfAlive():
                self.count = 0
                self.mode = "init"
                self.wantedMaximalSpeed = 30
                self.wanted_heading = 90   
                return

            self.count += 1


            #
            # Read the ships "sensors".
            #
            ai.setTurnSpeed(30.0)
            x = ai.selfX()
            y = ai.selfY()
            vx = ai.selfVelX()
            vy = ai.selfVelY()
            speed = ai.selfSpeed()
            selfDirection = ai.selfTrackingDeg()
            heading = ai.selfHeadingDeg()
            
            print(self.mode, selfDirection, self.wanted_heading, speed)

            # The coordinate for the ships position in the radar coordinate system, 
            # (0,0) is bottom left.
            # The radar is shown in the small black window in the top left corner
            # when you start the client.

            # read heading and compute the direction we are moving in if any
            #direction = heading
            #if vx != 0 or vy != 0:
                #direction = math.degrees (math.atan2 (vy, vx))
        
            #
            # State machine code, do different things including state 
            # transitions depending on the current state, sensor values and
            # other kind of values.
            #
            
            # At all times we want to check if we are crashing into anything, unless we are already avoiding it
            if CheckWall(self.checkDist) and self.mode != "turning":
                self.wanted_heading = int(ai.selfHeadingDeg()) # 0-360, 0 in x direction, positive toward y
                self.wanted_heading += 90
                self.wanted_heading %= 360
                self.mode = "turning"
            
            if Danger() != False:
                    self.mode = "dodge"
            
            


            # avoid strange sensor values when starting by waiting
            # three ticks until we go to fly
            if self.count == 3:
                self.mode = "ready"

            elif self.mode == "ready":
                if ai.closestShipId() == -1:
                   self.mode = "moving"
                else:
                   self.mode = "shooting"
            
            elif self.mode == "moving":
                if speed < self.wantedMaximalSpeed:
                    ai.thrust(1)
                else:
                    ai.thrust(0)
                turnThisWay=FlyTo(ai.closestRadarX(), ai.closestRadarY(),ai.selfRadarX(),ai.selfRadarY())
                ai.turn(turnThisWay)
                if ai.closestShipId() != -1:
                    self.mode = "shooting"
            
            elif self.mode == "dodge":
                if Danger() == "pos":
                    ai.turnLeft(1)
                elif Danger() == "neg":
                    ai.turnRight(1)
                elif Danger() == False:
                    self.mode = "ready"

            #
            # Wait until wanted heading is achieved. Then go to state waitnowall.
            #
            elif self.mode == "turning":
                ai.turnToDeg(self.wanted_heading)
                if abs(ai.angleDiff (int(heading), int(self.wanted_heading))) < 20:
                    self.count = 0
                    self.mode = "waitnowall"

            elif self.mode == "waitnowall":
                if not CheckWall(self.checkDist) and self.count > 20:
                    self.mode = "ready"
                
                ai.thrust(1)

            elif self.mode == "shooting":
                ai.thrust(0)
                if ai.closestShipId() == -1:
                    self.mode = "ready"
                else:
                    #degreeDiff=
                    self.wanted_heading=Shoot(ai.closestShipId())
                    if self.wanted_heading == False:
                        return
                    ai.turnToDeg(self.wanted_heading)
                    #if degreeDiff < 3:
                    ai.fireShot()
            #
            # End of state machine part
            #



            #
            # Send the needed control signals to the ship
            #

            # Turn to the wanted heading

                        


        except:
            e = sys.exc_info()
            print ("ERROR: ", e)

def Shoot(id):
    if id == -1:
        return False
    selfX=ai.selfX()
    selfY=ai.selfY()
    selfVelocity=ai.selfSpeed()
    selfTracking=ai.selfTrackingRad()
    if math.isnan(selfTracking):
        selfTracking=0
    selfVelocityX=selfVelocity*math.cos(selfTracking)
    selfVelocityY=selfVelocity*math.sin(selfTracking)




    enemyX=ai.screenEnemyXId(id)
    enemyY=ai.screenEnemyYId(id)
    enemyVelocity=ai.enemySpeedId(id)
    enemyTracking=ai.enemyTrackingRadId(id)
    if enemyTracking == None:
        return False
    if math.isnan(enemyTracking):
        enemyTracking=0
    enemyVelocityX=enemyVelocity*math.cos(enemyTracking)
    enemyVelocityY=enemyVelocity*math.sin(enemyTracking)
    bulletVelocity=21 #final.xp
    relativeX=enemyX-selfX
    relativeY=enemyY-selfY
    relativeVelocityX=enemyVelocityX-selfVelocityX
    relativeVelocityY=enemyVelocityY-selfVelocityY


    time=TimeOfImpact(relativeX, relativeY, relativeVelocityX, relativeVelocityY, bulletVelocity)

    targetX=enemyX+enemyVelocityX*time
    targetY=enemyY+enemyVelocityY*time
    targetAngle=math.atan2(targetY-selfY,targetX-selfX)
    targetAngle=ai.radToDeg(targetAngle)

    return targetAngle+random.randint(-10,10)

def TimeOfImpact(relativeX, relativeY, targetSpeedX, targetSpeedY, bulletSpeed): #inspired by: http://playtechs.blogspot.se/2007/04/aiming-at-moving-target.html

    a=bulletSpeed * bulletSpeed - (targetSpeedX*targetSpeedX+targetSpeedY*targetSpeedY)
    b=relativeX*targetSpeedX+relativeY*targetSpeedY
    c=relativeX*relativeX+relativeY*relativeY
    d=b*b+a*c
    time=0

    if d >= 0:
        time = ( b + math.sqrt(d) ) /a
        if time < 0:
            time = 0

    return time
	
def FlyTo(targetX,targetY,selfX,selfY):
    targetAngle=math.atan2(targetY-selfY,targetX-selfX)
    targetAngle=ai.radToDeg(targetAngle)
    egenAngle=int(ai.selfHeadingDeg())
    diffAngle=ai.angleDiff(egenAngle,targetAngle)
    diffX=selfX-targetX
    diffY=selfY-targetY

    return diffAngle
        
def CheckWall(dist):
    try:
        vx = ai.selfVelX()
        vy = ai.selfVelY()
        if vx != 0 or vy != 0:
            direction = math.degrees (math.atan2 (vy, vx))

            distance_to_wall = ai.wallFeeler (dist, int(direction), 1, 1)  
            # ai.wallFeller return dist if there is no wall in the direction
            # and nearer than dist. If there is a wall nearer than dist it
            # returns the actual distance to the wall.

            return dist != distance_to_wall
        else:
            return False

    except:
        e = sys.exc_info()
        print ("ERROR CheckWall: ", e)

    return False

#For a ship that is unmoving. Will the trajectory of the shot cross the location of the ship? 

def InterPointLine(x, y, returnList):
    cross = returnList[0]*x+returnList[1]
    
    if cross == y:
        return(True)
    elif (cross - y) < 25 and (cross - y) > -25:
        return(True)
    else:
        return(False)

#Calculates the straight line equation, and returns the k and m values.
def StraightLine(x, y, velX, velY):
    valueK = velY/velX
    valueM = y-x*valueK
    returnList = [valueK, valueM]
    return(returnList)


#Checks whether, and where, two straight lines will intersect. Returns a value for (x,y) where the lines cross.
def Intersection(selfLine, shotLine):
    valueX = (selfLine[1]-shotLine[1])/(shotLine[0]-selfLine[0])
    valueY = selfLine[0]*valueX+selfLine[1]
    returnList = [valueX, valueY]
    if not selfLine or not shotLine:
        return("Error, wrong input to Intersection function")
    elif selfLine == shotLine:
        return False
    else: 
        return(returnList)

#Calculates the Danger of every shot in the immediate viscinity of the ship, using above functions. If there is no Danger it will return False. If there is Danger of being hit, it will return either positive or negative depending on which direction is better to make an evasive manouver. 
def Danger():
    enId = ai.closestShipId()
    selfX = ai.selfX()
    selfY = ai.selfY()
    selfVel = ai.selfSpeed()
    selfVelX = ai.selfVelX()
    selfVelY = ai.selfVelY()
    for i in range(99):
        if ai.shotAlert(i) == -1:
            return False
        else:
            shotX = ai.shotX(i)
            shotY = ai.shotY(i)
            shotTrack = ai.shotVelDir(i)
            shotVel = 21 + ai.enemySpeedId(enId) # The 10 may vary depending on map, 21 for final.xp.
            shotVelX = shotVel*math.cos(shotTrack)
            shotVelY = shotVel*math.sin(shotTrack)
            
            if selfVel > 0 and shotVelX == 0:
                shotVelX += 0.01
            
            elif selfVel > 0 and shotVelY == 0:
                shotVelY += 0.01
                
            elif selfVel > 0 and selfVelX == 0:
                selfVelX += 0.01
            
            elif selfVel > 0 and selfVelY == 0:
                selfVelY += 0.01
                
            else:

                if ai.shotDist(i) > 200:
                    return(False)

                elif selfVel == 0 and InterPointLine(selfX, selfY, StraightLine(shotX, shotY, shotVelX, shotVelY)) == False:
                    return(False)
            
           # elif selfVel == 0 and InterPointLine(selfX, selfY, StraightLine(shotX, shotY, shotVelX, shotVelY)) == True:
                #return(5)

                elif ai.shotDist(i) < 200 and selfVel > 0:
                    intersectCoords = Intersection(StraightLine(selfX, selfY, selfVelX, selfVelY), StraightLine(shotX, shotY, shotVelX, shotVelY))
                    selfStraightLine = StraightLine(selfX, selfY, selfVelX, selfVelY)
                    shotStraightLine = StraightLine(shotX, shotY, shotVelX, shotVelY)
                    if selfX < shotX:
                        return("neg") 
                    elif selfX > shotX:
                        return("pos")
                    else:
                        if selfY < shotY: 
                            return("neg")
                        else:
                            return("pos")
                    
                elif ai.shotDist(i) < 200 and selfVel == 0:
                 
                    intersectCoords = InterPointLine(selfX, selfY, StraightLine(shotX, shotY, shotVelX, shotVelY))
                    if intersectCoords == True:
                        return("pos")
                    else:
                        pass

                break



bot = myai()

def AI_loop():
    bot.tick()

AI_loop()


(options, args) = parser.parse_args()
port = 15345 + options.group
name = "Voldemort"


# The command line arguments to xpilot can be given in the list in the second argument
# 
ai.start(AI_loop,[])#"-name", name, "-join", "-fuelMeter", "yes", "-showHUD", "no", "-port", str(port)])
