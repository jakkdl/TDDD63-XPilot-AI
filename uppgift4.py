# -*- coding:Latin-1 -*-
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

            heading = ai.selfHeadingDeg() 
            # 0-360, 0 in x direction, positive toward y

            speed = ai.selfSpeed()
            x = ai.selfX()
            y = ai.selfY()
            vx = ai.selfVelX()
            vy = ai.selfVelY()
            selfDirection = ai.selfTrackingDeg()
            # Add more sensors readings here if they are needed

            print (self.mode, x, y, ai.selfRadarX(), ai.selfRadarY(), ai.closestShipId(), ai.screenEnemyXId(ai.closestShipId()), ai.screenEnemyYId(ai.closestShipId()), ai.closestRadarX(), ai.closestRadarY())


            # avoid strange sensor values when starting by waiting
            # three ticks until we go to ready 
            if self.count == 3 and ai.shotAlert(0) == -1:
                self.mode = "moving"
            elif self.mode == "moving":
                flyTo(ai.closestRadarX(), ai.closestRadarY(),ai.selfRadarX(),ai.selfRadarY())
                if ai.selfVelX() == 0 and ai.selfVelY() == 0 and ai.closestShipId() != -1:
                    self.mode = "shooting"
                    print(ai.closestShipId() != -1)
            elif self.mode == "shooting":
                    
                if ai.closestShipId() == -1:
                    print("moving")
                    self.mode = "moving"
            else:
                    if shoot(ai.closestShipId()) < 3:
                        ai.fireShot()
            
            if self.count == 3 and ai.shotAlert(0) > -1:
                self.mode = "Flee"
            elif self.mode == "Flee":
                    dodge(ai.shotX(0), ai.shotY(0), x, y)
                
      
        except:
            e = sys.exc_info()
            print ("ERROR: ", e)

   
def shoot(id):
    selfX=ai.selfX()
    selfY=ai.selfY()
    targetX=ai.screenEnemyXId(id)
    targetY=ai.screenEnemyYId(id)
    targetAngle=math.atan2(targetY-selfY,targetX-selfX)
    targetAngle=ai.radToDeg(targetAngle)
    egenAngle=int(ai.selfHeadingDeg())
    diffAngle=ai.angleDiff(egenAngle,targetAngle)
    ai.turn(diffAngle)
    return diffAngle


    
def flyTo(targetX,targetY,selfX,selfY):

        targetAngle=math.atan2(targetY-selfY,targetX-selfX)

        targetAngle=ai.radToDeg(targetAngle)

        egenAngle=int(ai.selfHeadingDeg())

        diffAngle=ai.angleDiff(egenAngle,targetAngle)

        #print(selfX, selfY, targetX, targetY)
        ai.turn(diffAngle)
        if ai.closestShipId() != -1:
            print("stopping")
            ai.thrust(0)
            return

        if math.fabs(ai.selfVelX()) + math.fabs(ai.selfVelY()) < 5:
            print("thrust")
            ai.thrust(1)
        else:
            ai.thrust(0)

def dodge(targetX, targetY,selfX,selfY):

        targetAngle=math.atan2(targetY-selfY,targetX-selfX)

        targetAngle=ai.radToDeg(targetAngle)

        selfAngle=int(ai.selfHeadingDeg())

        diffAngle=ai.angleDiff(selfAngle,targetAngle)

        diffX=selfX-targetX

        diffY=selfY-targetY
        
        ai.turn(-diffAngle/2)

        if diffX < 50 and diffX >-50 or diffY < 50 and diffY >-50:
            ai.thrust(1) 
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
name = "PorkMonger"

#
# Start the main loop. Callback are done to AI_loop.
#

ai.start(AI_loop,["-name", name, 
                  "-join", 
                  "-fuelMeter", "yes", 
                  "-showHUD", "no",
                  "-port", str(port)])