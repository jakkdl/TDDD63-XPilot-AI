#
# This is the file stub.py that can be used as a starting point for the bots
#

import libpyAI as ai

import sys
import math

from optparse import OptionParser

parser = OptionParser()

parser.add_option ("-g", "--group", action="store", type="int", 
                   dest="group", default=0, 
                   help="The group number. Used to avoid port collisions when" 
                   " connecting to the server.")

#
# Create a class used to store the internal state of the bot
#

class myai:
    """Simple Stub for a Bot"""

    def __init__(self):
        self.count = 0
        self.mode = "init"



    def tick(self):
        try:

            #
            # If we die then restart the state machine in the state "init"
            #
            if not ai.selfAlive():
                self.count = 0
                self.mode = "init"
                return

            self.count += 1

            #
            # Read the "sensors"
            #
            radarx = ai.selfRadarX()   # Just read to demo how it works
            radary = ai.selfRadarY()   # Just read to demo how it works
            
            # read heading and compute the direction we are moving in if any
            heading = ai.selfHeadingDeg() # 0-360, 0 in x direction, positive toward y
            direction = heading
            if vx != 0 or vy != 0:
                direction = math.degrees (math.atan2 (vy, vx))

            heading = ai.selfHeadingDeg() 
            # 0-360, 0 in x direction, positive toward y

            speed = ai.selfSpeed()
            x = ai.selfX()
            y = ai.selfY()
            vx = ai.selfVelX()
            vy = ai.selfVelY()
            selfDirection = ai.selfTrackingDeg()
            # Add more sensors readings here if they are needed

            print (self.mode, ai.shotVel(0), ai.shotVelDir(0))


            # avoid strange sensor values when starting by waiting
            # three ticks until we go to ready
            if self.count == 3:
                self.mode = "ready"
            elif self.mode =="ready":
                if ai.closestShipId() == -1:
                    self.mode = "moving"
                elif ai.closestShipId() != -1:
                    self.mode = "shooting"
            elif self.mode == "moving":
                flyTo(ai.closestRadarX(), ai.closestRadarY(),ai.selfRadarX(),ai.selfRadarY())
                 elif self.mode == "fly":
                self.wanted_minimal_speed = 2
                # check if we are near walls if flying
                if self.check_wall(200):
                    print ("WALL")
                    self.wanted_heading += 180
                    self.wanted_heading %= 360
                    print ("Wanted heading:", self.wanted_heading)
                    self.mode = "turning"
                    self.wanted_minimal_speed = 0
                    
            #
            # Wait until wanted heading is achieved. Then go to state waitnowall.
            #
            elif self.mode == "turning":
                if abs (ai.angleDiff (int(heading), int(self.wanted_heading))) < 2:
                    self.mode = "waitnowall"

            elif self.mode == "waitnowall":
                if not self.check_wall(200):
                    self.mode = "moving"
                if ai.selfVelX() < 2 and ai.selfVelY() < 2 and ai.closestShipId() != -1:
                    self.mode = "shooting"
                    print(ai.closestShipId() != -1)
            elif self.mode == "shooting":
                if ai.closestShipId() == -1:
                    self.mode = "ready"
                else:
                    shoot(ai.closestShipId())
                    if shoot(ai.closestShipId()) < 3:
                        ai.fireShot()
                    
                
      
        except:
            e = sys.exc_info()
            print ("ERROR: ", e)

   
def shoot(id):
    selfX=ai.selfX()
    selfY=ai.selfY()
    currentX=ai.screenEnemyXId(id)
    currentY=ai.screenEnemyYId(id)
    enemyVelocity=ai.enemySpeedId(id)
    enemyTracking=ai.enemyTrackingRadId(id)
    enemyVelocityX=enemyVelocity*math.cos(enemyTracking)
    enemyVelocityY=enemyVelocity*math.sin(enemyTracking)
    bulletVelocity=10 #emptybordernofriction.xp Assumes that we stand still

    time=timeOfImpact(selfX, selfY, currentX, currentY, enemyVelocityX, enemyVelocityY, bulletVelocity)

    targetX=currentX+enemyVelocityX*time
    targetY=currentY+enemyVelocityY*time
    targetAngle=math.atan2(targetY-selfY,targetX-selfX)
    targetAngle=ai.radToDeg(targetAngle)
    egenAngle=int(ai.selfHeadingDeg())
    diffAngle=ai.angleDiff(egenAngle,targetAngle)

    ai.turn(diffAngle)
    return diffAngle

def timeOfImpact(selfX, selfY, targetX, targetY, targetSpeedX, targetSpeedY, bulletSpeed): #copy-pasted straight from internet: http://playtechs.blogspot.se/2007/04/aiming-at-moving-target.html

    relativeX=targetX-ai.selfX()
    relativeY=targetY-ai.selfY()
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

        #print(selfX, selfY, targetX, targetY)
        ai.turn(diffAngle)
        if ai.closestShipId() != -1:
            print("stopping")
            ai.thrust(0)
            return

        if math.fabs(ai.selfVelX()) + math.fabs(ai.selfVelY()) < 10:
            print("thrust")
            ai.thrust(1)
        else:
            ai.thrust(0)

        
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

 
#
# Create an instace of the bot class myai.
#

bot = myai()

#
# Connect the bot instance with the AI loop
#

def AI_loop():
    bot.tick()

#
# Parse the command line arguments
#

(options, args) = parser.parse_args()

port = 15345 + options.group
name = "Stub"

#
# Start the main loop. Callback are done to AI_loop.
#

ai.start(AI_loop,["-name", name, 
                  "-join", 
                  #"-fuelMeter", "yes", 
                  #"-showHUD", "no",
                  "-port", str(port)])
