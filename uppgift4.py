
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
            
            ai.setTurnSpeed(64.0)

            print(self.mode, x, ai.shotX(0), "-", y, ai.shotY(0), "-")
            # avoid strange sensor values when starting by waiting
            # three ticks until we go to ready 
            
            if self.count == 3:
                self.mode = "Ready"
            
            elif self.mode == "Ready":
                if danger() != False:
                    self.mode = "Dodge"
                else: 
                    pass
            
            elif self.mode == "Dodge":
                dodge(danger())
                if speed < 2:
                    ai.thrust(1)
                elif danger() == False:
                    self.mode = "Ready"
                
                
#Below if puts the bot back in ready mode if danger subsides.                                                          .
                if danger() == False:
                    self.mode = "Ready"
            
      
        except:
            e = sys.exc_info()
            print ("ERROR: ", e)

#For a ship that is unmoving. Will the trajectory of the shot cross the location of the ship? 

def interPointLine(x, y, returnList):
    cross = returnList[0]*x+returnList[1]
    
    if cross == y:
        return(True)
    elif cross - y < 10 and cross - y > -10:
        return(True)
    else:
        return(False)

def dodge(degrees):
    ai.turn(degrees)

#Calculates the straight line equation, and returns the k and m values.
def straightLine(x, y, velX, velY):
    valueK = velY/velX
    valueM = y-x*valueK
    returnList = [valueK, valueM]
    return(returnList)

#Checks whether, and where, two straight lines will intersect. Returns a value for (x,y) where the lines cross.
def intersection(selfLine, shotLine):
    valueX = (selfLine[1]-shotLine[1])/(selfLine[0]-shotLine[0])
    valueY = selfLine[0]*valueX+selfLine[1]
    returnList = [valueX, valueY]
    if not selfLine or not shotLine:
        return("Error, wrong input to intersection function")
    elif selfLine[0] == shotLine[0]:
        return(False)
    else: 
        return(returnList)

#Calculates the amount of time until the lines intercept. The straight line equations are calculated based on the directional velocity of the objects, thusly the resulting x value can be used as a measurement of time to check whether they will reach the intercept point at the same time, otherwise we are still safe on current course.
def time(intersectCoords, returnList):
    intersectY = intersectCoords[1]
    intersectTime = 0
    if not returnList:
        return("Error, incorrect input to time function")
    else: 
        intersectTime = intersectY/returnList[0] - returnList[1]
        return(intersectTime)

#Same as above, roughly, except for an unmoving ship.

def timeStill(x, y, returnList):
    time = (y-returnList[1]) / (returnList[0])
    return(time)


#Calculates the danger of every shot in the immediate viscinity of the ship, using above functions. Returns a 5 degree turn adjustment, positive or negative depending on which small evasion is needed. If this is insufficient the next tick will catch it and force another 5 degree adjustment.
def danger():
    enId = ai.closestShipId()
    selfX = ai.selfX()
    selfY = ai.selfY()
    selfVel = ai.selfSpeed()
    selfVelX = ai.selfVelX()
    selfVelY = ai.selfVelY()
    for i in range(99):
        if ai.shotAlert(i) != -1:
            shotX = ai.shotX(i)
            shotY = ai.shotY(i)
            shotTrack = ai.shotVelDir(i)
            shotVel = 10 + ai.enemySpeedId(enId) # The 10 may vary depending on map, adjust accordingly.
            shotVelX = shotVel*math.cos(shotTrack)
            shotVelY = shotVel*math.sin(shotTrack)
 
            if ai.shotDist(i) > 200:
                return(False)

            elif selfVel == 0 and intersection([selfX, selfY], straightLine(shotX, shotY, shotVelX, shotVelY)) == False:
                return(False)
            
            elif selfVel == 0 and interPointLine(selfX, selfY, straightLine(shotX, shotY, shotVelX, shotVelY)) == False:
                return(False)

            elif ai.shotDist(i) < 200 and selfVel > 0:
                intersectCoords = intersection(straightLine(selfX, selfY, selfVelX, selfVelY), straightLine(shotX, shotY, shotVelX, shotVelY))
                selfStraightLine = straightLine(selfX, selfY, selfVelX, selfVelY)
                shotStraightLine = straightLine(shotX, shotY, shotVelX, shotVelY)
                selfTimer = time(intersectCoords, selfStraightLine)
                shotTimer = time(intersectCoords, shotStraightLine)
     
                if selfTimer - shotTimer > 15 or selfTimer - shotTimer < -15: #Tentative values, to be adjusted as needed.
                    pass
               
                else:
                    if selfX < shotX:
                        return(5) 
                    elif selfX > shotX:
                        return(-5)
                    else:
                        if selfY < shotY: 
                            return(-5)
                        elif selfY > shotY:
                            return(5)

            elif ai.shotDist(i) < 200 and selfVel == 0:
                 
              intersectCoords = interPointLine(selfX, selfY, straightLine(shotX, shotY, shotVelX, shotVelY))
              if intersectCoords == True:
                  ai.thrust(1)
                  return(5)
              else:
                  pass
     
            


        elif ai.shotAlert(i) == -1:
            return(False)
            break


        
        
        
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
name = "Nemesis Divina"

#
# Start the main loop. Callback are done to AI_loop.
#

ai.start(AI_loop,["-name", name, 
                  "-join", 
                  "-fuelMeter", "yes", 
                  "-showHUD", "no",
                  "-port", str(port)])