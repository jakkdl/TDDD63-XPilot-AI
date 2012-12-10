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




    def tick(self):
        try:

            #
            # If we die then restart the state machine in the state "start"
            # The game will restart the spaceship at the base.
            #
            if not ai.selfAlive():
                self.count = 0
                self.mode = "init"
                self.wanted_minimal_speed = 0
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
            
            print(self.mode, self.wanted_heading)

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
            if check_wall(300) and self.mode != "turning":
                self.wanted_heading = int(ai.selfHeadingDeg()) # 0-360, 0 in x direction, positive toward y
                self.wanted_heading += 90
                self.wanted_heading %= 360
                self.mode = "turning"
            
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
                if speed < 10:
                    ai.thrust(1)
                else:
                    ai.thrust(0)
                turnThisWay=flyTo(ai.closestRadarX(), ai.closestRadarY(),ai.selfRadarX(),ai.selfRadarY())
                ai.turn(turnThisWay)
                if ai.closestShipId() != -1:
                    self.mode = "shooting"

            #
            # Wait until wanted heading is achieved. Then go to state waitnowall.
            #
            elif self.mode == "turning":
                ai.turnToDeg(self.wanted_heading)
                #if not check_wall(300):
                    #self.mode = "ready"
                print(int(heading), int(self.wanted_heading))
                if abs(ai.angleDiff (int(heading), int(self.wanted_heading))) < 20:
                    self.count = 0
                    self.mode = "waitnowall"

            #
            # Wait until we have "bounced" away from the wall.
            #
            elif self.mode == "waitnowall":
                if not check_wall(300) and self.count > 10:
                    self.mode = "ready"
                
                ai.thrust(1)

            elif self.mode == "shooting":
                ai.thrust(0)
                if ai.closestShipId() == -1:
                    self.mode = "ready"
                else:
                    #degreeDiff=
                    self.wanted_heading=shoot(ai.closestShipId())
                    ai.turnToDeg(shoot(ai.closestShipId()))
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

def shoot(id):
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
    if math.isnan(enemyTracking):
        enemyTracking=0
    enemyVelocityX=enemyVelocity*math.cos(enemyTracking)
    enemyVelocityY=enemyVelocity*math.sin(enemyTracking)
    bulletVelocity=21 #final.xp

    relativeX=enemyX-selfX
    relativeY=enemyY-selfY
    relativeVelocityX=enemyVelocityX-selfVelocityX
    relativeVelocityY=enemyVelocityY-selfVelocityY


    time=timeOfImpact(relativeX, relativeY, relativeVelocityX, relativeVelocityY, bulletVelocity)

    targetX=enemyX+enemyVelocityX*time
    targetY=enemyY+enemyVelocityY*time
    targetAngle=math.atan2(targetY-selfY,targetX-selfX)
    targetAngle=ai.radToDeg(targetAngle)




    return targetAngle+random.randint(-10,10)

def timeOfImpact(relativeX, relativeY, targetSpeedX, targetSpeedY, bulletSpeed): #inspired by: http://playtechs.blogspot.se/2007/04/aiming-at-moving-target.html

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
	
def flyTo(targetX,targetY,selfX,selfY):
    targetAngle=math.atan2(targetY-selfY,targetX-selfX)
    targetAngle=ai.radToDeg(targetAngle)
    egenAngle=int(ai.selfHeadingDeg())
    diffAngle=ai.angleDiff(egenAngle,targetAngle)
    diffX=selfX-targetX
    diffY=selfY-targetY


    return diffAngle
        


#
# Returns true if there is a wall nearer than dist in the direction the
# ship is moving (not the direction it is pointing!). Otherwise returns false.
def check_wall(dist):
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

    except:
        e = sys.exc_info()
        print ("ERROR check_wall: ", e)

    return False

bot = myai()

def AI_loop():
    bot.tick()

AI_loop()


(options, args) = parser.parse_args()
port = 15345 + options.group
name = "BurgerFan007"


# The command line arguments to xpilot can be given in the list in the second argument
# 
ai.start(AI_loop,[])#"-name", name, "-join", "-fuelMeter", "yes", "-showHUD", "no", "-port", str(port)])
