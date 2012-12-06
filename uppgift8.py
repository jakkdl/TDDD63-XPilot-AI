#
# This is the file stub.py that can be used as a starting point for the bots
#
import time
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

            heading = ai.selfHeadingDeg() 
        
            ai.setTurnSpeed(64.0)
            speed = ai.selfSpeed()
            x = ai.selfX()
            y = ai.selfY()
            vx = ai.selfVelX()
            vy = ai.selfVelY()
            # Add more sensors readings here if they are needed
            self.wanted_heading = flyTo(ai.closestRadarX(), ai.closestRadarY(),ai.selfRadarX(),ai.selfRadarY())

            


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
                
                    if ai.selfSpeed() < 2:
                        ai.thrust(1)
                    elif a.selfSpeed() >= 2:
                        ai.thrust(0)
                    elif self.check_wall(200):
                        self.mode = "turning"
                    elif ai.closestShipId() != -1:
                        self.mode = "shooting"
            
            elif self.mode == "turning":
                self.wanted_heading += 180
                self.wanted_heading %= 360
                ai.thrust(0)
                if abs (ai.angleDiff (int(heading), int(self.wanted_heading))) < 2:
                    self.mode = "waitnowall"
                    
            # Wait until wanted heading is achieved. Then go to state waitnowall.
            

            elif self.mode == "waitnowall":
                ai.thrust(1)
                if not self.check_wall(200):
                    self.mode = "moving"


            elif self.mode == "shooting":
                ai.thrust(0)
                if ai.closestShipId() == -1:
                    self.mode = "ready"
                else:
                    #degreeDiff=
                    shoot(ai.closestShipId())
                    #if degreeDiff < 3:
                    ai.fireShot()
                    
                
      
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
        bulletVelocity=10 #emptybordernofriction.xp

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

    def timeOfImpact(relativeX, relativeY, targetSpeedX, targetSpeedY, bulletSpeed): #inspired by http://playtechs.blogspot.se/2007/04/aiming-at-moving-target.html

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

        return(diffAngle)


 
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
name = "Voldemort"

#
# Start the main loop. Callback are done to AI_loop.
#

ai.start(AI_loop,["-name", name, 
                  "-join", 
                  #"-fuelMeter", "yes", 
                  #"-showHUD", "no",
                  "-port", str(port)])
