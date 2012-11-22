
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
                if danger != -1:    #Triggers "dodge-mode" if a shot is close
                    self.mode = "Dodge"
                else: 
                    ai.thrust(0)
            
            elif self.mode == "Dodge":
                    ai.turn(int(dodge(ai.shotX(0), ai.shotY(0), x, y)))
                    ai.thrust(1)
#Below if puts the bot back in ready mode if danger subsides (shot is no longer in the immediate viscinity of the ship).
                    if danger == -1:  
                        self.mode = "Ready"
                    else: 
                        pass
      
        except:
            e = sys.exc_info()
            print ("ERROR: ", e)

def dodge(idx):
    shotX=ai.shotX(idx)
    shotY=ai.shotY(idx)
    currentX=ai.selfX()
    currentY=ai.selfY()
    selfVelocity=ai.selfSpeed()
    enemyTracking=ai.shotVelDir(idx)
    selfVelocityX=selfVelocity*math.cos(enemyTracking)
    selfVelocityY=selfVelocity*math.sin(enemyTracking)
    bulletVelocity=10 #emptybordernofriction.xp Assumes that we stand still

    time=timeOfImpact(shotX, shotY, currentX, currentY, selfVelocityX, selfVelocityY, bulletVelocity)

    targetX=shotX+selfVelocityX*time
    targetY=shotY+selfVelocityY*time
    targetAngle=math.atan2(targetY-selfY,targetX-selfX)
    targetAngle=ai.radToDeg(targetAngle)
    ownAngle=int(ai.selfHeadingDeg())
    diffAngle=ai.angleDiff(ownAngle,targetAngle)

    return diffAngle

def timeOfImpact(selfX, selfY, targetX, targetY, targetSpeedX, targetSpeedY, bulletSpeed) #copy-pasted straight from internet: http://playtechs.blogspot.se/2007/04/aiming-at-moving-target.html
    relativeX=enemyX-ai.selfX()
    relativeY=enemyY-ai.selfY()
    a=bulletSpeed * bulletSpeed - (targetSpeedX*targetSpeedX+targetSpeedY*targetSpeedY)
    b=relativeX*targetSpeedX+relativeY*targetSpeedY
    c=relativeX*relativeX+relativeY*relativeY

    d=b*b+a*c
    
    time=0

    if d >= 0:
        time = ( b + math.sqrt(d) ) /a
        if time < 0
            time = 0

    return time
        
        
        
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
