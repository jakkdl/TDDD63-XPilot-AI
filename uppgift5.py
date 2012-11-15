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
        print ("INIT")
        self.count = 0
        self.wanted_minimal_speed = 0
        self.wanted_heading = random.randint(0, 360)   # just to get it to fly a bit east also
        self.mode = "start"        # used to store the current state of the state machine


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
                self.mode = "start"
                self.wanted_minimal_speed = 0
                self.wanted_heading = 80       # just to get it to fly a bit east also
                return

            self.count += 1

            #
            # Read the ships "sensors".
            #
            ai.setTurnSpeed(64.0)
            x = ai.selfX()
            y = ai.selfY()
            vx = ai.selfVelX()
            vy = ai.selfVelY()
            speed = ai.selfSpeed()
            
            # The coordinate for the ships position in the radar coordinate system, 
            # (0,0) is bottom left.
            # The radar is shown in the small black window in the top left corner
            # when you start the client.

            radarx = ai.selfRadarX()   # Just read to demo how it works
            radary = ai.selfRadarY()   # Just read to demo how it works
            
            # read heading and compute the direction we are moving in if any
            heading = ai.selfHeadingDeg() # 0-360, 0 in x direction, positive toward y
            direction = heading
            if vx != 0 or vy != 0:
                direction = math.degrees (math.atan2 (vy, vx))

            print (x, y, vx, vy, speed, " - ", radarx, radary, " - ", 
                   heading, direction, " - ", 
                   self.wanted_heading, self.wanted_minimal_speed, " - ", self.mode)

            #
            # State machine code, do different things including state 
            # transitions depending on the current state, sensor values and
            # other kind of values.
            #

            # avoid strange sensor values when starting by waiting
            # three ticks until we go to fly
            if self.mode == "start":
                if self.count == 3:
                    self.mode = "fly"

            #
            # In the fly state we make sure the ships speed is at least 2
            # and we check if we are near walls and set the wanted heading
            # in that case and go to the state turning.
            #
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



            #
            # Wait until we have "bounced" away from the wall.
            #
            elif self.mode == "waitnowall":
                if not self.check_wall(200):
                    self.mode = "fly"

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



bot = myai()

def AI_loop():
    bot.tick()

AI_loop()


(options, args) = parser.parse_args()
port = 15345 + options.group
name = "BurgerFan007"


# The command line arguments to xpilot can be given in the list in the second argument
# 
ai.start(AI_loop,["-name", name,
                  "-join", 
                  "-fuelMeter", "yes", 
                  "-showHUD", "no",
                  "-port", str(port)])