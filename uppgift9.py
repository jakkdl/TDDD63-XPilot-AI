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

            print (self.mode, ai.shotVel(0), ai.shotVelDir(0))


            # avoid strange sensor values when starting by waiting
            # three ticks until we go to ready
            if self.count == 3:
                self.mode = "ready"
            elif self.mode =="ready":
                print("ready and waiting")
                ai.setTurnSpeed(64.0)
                if danger != -1 and ai.shotDist(0) < 100:
                    print("dodgeing")
                    #  Triggers "dodge-mode"  if a shot is close
                    self.mode = "Dodge"
                elif  ai.closestShipId() == -1:
                    self.mode = "moving"
                elif ai.closestShipId() != -1:
                    ai.thrust(0)
                    self.mode = "shooting"
            elif self.mode == "moving":
                flyTo(ai.closestRadarX(), ai.closestRadarY(),ai.selfRadarX(),ai.selfRadarY())
                self.mode = "ready"
            elif self.mode == "shooting":
                 shoot(ai.closestShipId())
                 self.mode="ready"  
            elif self.mode == "Dodge":
                if dodge(0) >= 0:
                    ai.turn(int(-dodge(0)+45))
                    ai.thrust(1)
                else:
                    ai.turn(int(dodge(0)-45))
                    ai.thrust(1)
#Below if puts the bot back in ready mode if danger subsides (shot is no longer in the immediate viscinity of the ship).
                    if ai.shotDist(0) > 100 or danger == -1:  
                        self.mode = "ready"
                        

            
                   
                    
                    
                    
                
      
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
    targetDist=math.sqrt((relativeX*relativeX)+(relativeY*relativeY))//1
    if diffAngle<5:
        ai.fireShot()
    elif diffAngle<20 and targetDist<5:
        ai.fireShot()
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

def bulletImpact(selfX, selfY, targetX, targetY, targetSpeedX, targetSpeedY, bulletSpeed): #copy-pasted straight from internet: http://playtechs.blogspot.se/2007/04/aiming-at-moving-target.html
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
    
def flyTo(targetX,targetY,selfX,selfY):
        targetAngle=math.atan2(targetY-selfY,targetX-selfX)
        targetAngle=ai.radToDeg(targetAngle)
        egenAngle=int(ai.selfHeadingDeg())
        diffAngle=ai.angleDiff(egenAngle,targetAngle)
        diffX=selfX-targetX
        diffY=selfY-targetY
        targetDist=math.sqrt((diffX*diffX)+(diffY*diffY))//1
        

        ai.turn(diffAngle)
      
        if ai.closestShipId() != -1:
            print("stopping")
            ai.thrust(0)
            return
            
 
        if   ai.selfSpeed()< 5 and ((diffAngle>20 and diffAngle<180)or(diffAngle<-20 and diffAngle>-180)):
            ai.thrust(1)
        elif targetDist>5:
            if diffAngle<10 and diffAngle>-10 and ai.selfSpeed()<20:
                    ai.thrust(1)
            else:
                ai.thrust(0)
        else:
            ai.thrust(0)
        
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

    time=bulletImpact(shotX, shotY, currentX, currentY, selfVelocityX, selfVelocityY, bulletVelocity)

    targetX=shotX+selfVelocityX*time
    targetY=shotY+selfVelocityY*time
    targetAngle=math.atan2(targetY-currentY,targetX-currentX)
    targetAngle=ai.radToDeg(targetAngle)
    ownAngle=int(ai.selfHeadingDeg())
    
    diffAngle=ai.angleDiff(ownAngle,targetAngle)
    
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
