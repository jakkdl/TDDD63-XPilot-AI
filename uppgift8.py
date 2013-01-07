import libpyAI as ai

import sys
import math
import random


from optparse import OptionParser

parser = OptionParser()

parser.add_option ("-g", "--group", action="store", type="int", 
                   dest="group", default=0, 
                   help="The group number. Used to avoid port collisions when" 
                   " connecting to the server.")

#
# state machine
#
# start -> fly -> turn -> waitnowall --
#           |                         |
#           ---------------------------
#
# We have here four states. The intuitive meaning of them are as follows:
#
# start      - This is the state the state machine is in when starting the program.
#              It goes from this mode to fly after the tick function have been called
#              three times. This is to avoid getting strange sensor values when starting.
#
# fly        - In this state the wanted minimal speed is set to 2. We will leave 
#              this state for the turn state when we are near a wall.
#
# turn       - We are travelling toward a wall so we turn to hit the wall with the
#              backside of the ship.
#
# waitnowall - waitnowall waits for the spaceship to bounce and change velocity 
#              direction. That means that it waits for no walls in the velocity 
#              direction.
#
# Note that an effect of how the control is done is that you cannot slow
# down. The wanted_minimal_speed is a minimal speed. If that is set to
# 0 that will not do anything. The control will only enable thrust to
# increase the speed so it is above the wanted minimal speed.
#

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


    #
    # Returns true if there is a wall nearer than dist in the direction the
    # ship is moving (not the direction it is pointing!). Otherwise returns false.
    def check_wall (self, dist):
#        print ("CHECKWALL")
        try:
            heading = ai.selfHeadingDeg() # 0-360, 0 in x direction, positive toward y
            vx = ai.selfVelX()
            vy = ai.selfVelY()
            direction = heading
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

            print(self.mode)

            #
            # Read the ships "sensors".
            #
            ai.setTurnSpeed(64.0)
            x = ai.selfX()
            y = ai.selfY()
            vx = ai.selfVelX()
            vy = ai.selfVelY()
            speed = ai.selfSpeed()
            selfDirection = ai.selfTrackingDeg()
            
            # The coordinate for the ships position in the radar coordinate system, 
            # (0,0) is bottom left.
            # The radar is shown in the small black window in the top left corner
            # when you start the client.

            # read heading and compute the direction we are moving in if any
            heading = ai.selfHeadingDeg() # 0-360, 0 in x direction, positive toward y
            direction = heading
            if vx != 0 or vy != 0:
                direction = math.degrees (math.atan2 (vy, vx))
        
            #
            # State machine code, do different things including state 
            # transitions depending on the current state, sensor values and
            # other kind of values.
            #

            # avoid strange sensor values when starting by waiting
            # three ticks until we go to fly
            if self.count == 3:
                self.mode = "ready"

            elif self.mode == "ready":
                 if ai.closestShipId() == -1:
                    self.mode = "moving"
                 elif ai.closestShipId() != -1:
                    self.mode = "shooting"
            
            elif self.mode == "moving":
                self.wanted_minimal_speed = 2
                self.wanted_heading = flyTo(ai.closestRadarX(), ai.closestRadarY(),ai.selfRadarX(),ai.selfRadarY())
                # check if we are near walls if flying
                if self.check_wall(200):
                    self.wanted_heading += 180
                    self.wanted_heading %= 360
                    self.mode = "turning"
                    self.wanted_minimal_speed = 0
                elif ai.closestShipId() != -1 and not self.check_wall(200):
                    self.mode = "shooting"

            #
            # Wait until wanted heading is achieved. Then go to state waitnowall.
            #
            elif self.mode == "turning":
                if abs (ai.angleDiff (int(heading), int(self.wanted_heading))) < 2:
                    self.mode = "waitnowall"


            #
            # Wait until we have "bounced" away from the wall.
            #
            elif self.mode == "waitnowall":
                
                if not self.check_wall(200):
                    self.mode = "ready"

            elif self.mode == "shooting":
                if ai.closestShipId() == -1:
                    self.mode = "ready"
                else:
                    #degreeDiff=
                    shoot(ai.closestShipId())
                    #if degreeDiff < 3:
                    ai.fireShot()
            #
            # End of state machine part
            #



            #
            # Send the needed control signals to the ship
            #

            # Turn to the wanted heading
            ai.turnToDeg (self.wanted_heading)

            # If the actual speed is less then the wanted mininal speed
            # then enable thruest. Otherwis disable thrust.
            if self.mode == "waitnowall":
                ai.thrust(1)
            else: 
                if speed < self.wanted_minimal_speed:
                    ai.thrust (1)
                else:
                    ai.thrust (0)
                        


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
    bulletVelocity=10 #emptybordernofriction.xp Assumes that we stand still

    relativeX=enemyX-selfX
    relativeY=enemyY-selfY
    relativeVelocityX=enemyVelocityX-selfVelocityX
    relativeVelocityY=enemyVelocityY-selfVelocityY


    time=timeOfImpact(relativeX, relativeY, relativeVelocityX, relativeVelocityY, bulletVelocity)

    targetX=enemyX+enemyVelocityX*time
    targetY=enemyY+enemyVelocityY*time
    targetAngle=math.atan2(targetY-selfY,targetX-selfX)
    targetAngle=ai.radToDeg(targetAngle)
    egenAngle=int(ai.selfHeadingDeg())
    diffAngle=ai.angleDiff(egenAngle,targetAngle)

    ai.turn(diffAngle)
    return diffAngle

def timeOfImpact(relativeX, relativeY, targetSpeedX, targetSpeedY, bulletSpeed): #copy-pasted straight from internet: http://playtechs.blogspot.se/2007/04/aiming-at-moving-target.html

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
        
def flyTo(targetX,targetY,selfX,selfY): #not used in this one
        targetAngle=math.atan2(targetY-selfY,targetX-selfX)
        targetAngle=ai.radToDeg(targetAngle)
        egenAngle=int(ai.selfHeadingDeg())
        diffAngle=ai.angleDiff(egenAngle,targetAngle)
        diffX=selfX-targetX
        diffY=selfY-targetY

        return(diffAngle)
        



bot = myai()

def AI_loop():
    bot.tick()

AI_loop()


(options, args) = parser.parse_args()
port = 15345 + options.group
name = "Voldemort"


# The command line arguments to xpilot can be given in the list in the second argument
# 
ai.start(AI_loop,["-name", name,
                  "-join", 
                  "-fuelMeter", "yes", 
                  "-showHUD", "no",
                  "-port", str(port)])
