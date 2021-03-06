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

            print (self.mode, x, y, vx, vy, speed, heading)


            # avoid strange sensor values when starting by waiting
            # three ticks until we go start aiming
            if self.count == 3:
                self.mode = "ready"
            elif self.mode == "ready":
                if ai.closestShipId() != -1:
                    self.mode = "aiming"
                    print(self.mode)
            elif self.mode == "aiming":
                diffAngle=aim(ai.closestShipId())
                if diffAngle == None:
                    self.mode == ready
                elif diffAngle > 3:
                    ai.turn(diffAngle)
                else:
                    ai.turn(diffAngle)
                    ai.fireShot()
                    
        except:
            e = sys.exc_info()
            print ("ERROR: ", e)

def aim(id):
    if id == -1:
        return None
    targetAngle=ai.radToDeg(math.atan2(ai.screenEnemyYId(id)-ai.selfY(),ai.screenEnemyXId(id)-ai.selfX()))
    selfAngle=int(ai.selfHeadingDeg())
    diffAngle=ai.angleDiff(selfAngle, targetAngle)
    return diffAngle
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
                  "-fuelMeter", "yes", 
                  "-showHUD", "no",
                  "-port", str(port)])
