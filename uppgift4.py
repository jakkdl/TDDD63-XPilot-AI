
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
            danger = ai.shotAlert(0)
            # Add more sensors readings here if they are needed
            
            ai.setTurnSpeed(64.0)

            print(self.mode, x, ai.shotX(0), "-", y, ai.shotY(0), "-", danger)
            # avoid strange sensor values when starting by waiting
            # three ticks until we go to ready 
            
            if self.count == 3:
                self.mode = "Ready"
            
            elif self.mode == "Ready":
                if danger != -1:   
                    self.mode = "Dodge"
                else: 
                    ai.thrust(0)
            
            elif self.mode == "Dodge":
                    ai.turn(int(dodge(ai.shotX(0), ai.shotY(0), x, y)))
                    ai.thrust(1)
                    if danger == -1:
                        self.mode = "Ready"
                    else: 
                        pass
      
        except:
            e = sys.exc_info()
            print ("ERROR: ", e)

def dodge(targetX, targetY, selfX, selfY):

        targetAngle=math.atan2(targetY-selfY,targetX-selfX)

        targetAngle=ai.radToDeg(targetAngle)

        selfAngle=int(ai.selfHeadingDeg())

        diffAngle=ai.angleDiff(selfAngle,targetAngle)
        
        diffX=selfX-targetX

        diffY=selfY-targetY
        
        if diffX < 50 and diffX >-50 or diffY < 50 and diffY >-50:
            return(-diffAngle/2)
        else:
            return(selfAngle)
        
        
        
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
