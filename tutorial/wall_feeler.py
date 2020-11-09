#
# This file can be used as a starting point for the bots.
#

import sys
import traceback
import math
import libpyAI as ai
from optparse import OptionParser

#
# Global variables that persist between ticks
#
tickCount = 0
stopCount = 0
mode = "ready"
itemId = -1
# add more if needed

def distance(xDis, yDis):
    return math.hypot(xDis, yDis)
        
def direction(xDis, yDis):
    return math.atan2(xDis, yDis)

def tick():
    #
    # The API won't print out exceptions, so we have to catch and print them ourselves.
    #
    try:

        #
        # Declare global variables so we have access to them in the function
        #
        global tickCount
        global stopCount
        global mode
        global itemId

        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
            tickCount = 0
            mode = "ready"
            return

        tickCount += 1

        # Sets the first item in itemCount as itemId which the ship will
        # focus to aquire.

        #
        # Read some "sensors" into local variables, to avoid excessive calls to the API
        # and improve readability.
        #

        selfX = ai.selfX()
        selfY = ai.selfY()
        selfVelX = ai.selfVelX()
        selfVelY = ai.selfVelY()
        selfSpeed = ai.selfSpeed()

        itemCount = ai.itemCountScreen()

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)                 

        selfHeading = ai.selfHeadingRad() 
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode", mode)

        if mode == "ready":
            mode = "aim"
        
        print(mode)

        if mode == "aim":

            if itemCount > 0:
                for item in range(itemCount):
                    itemId = item
            
                # Items X and Y coordinate.
                itemX = ai.itemX(itemId)
                itemY = ai.itemY(itemId)
            
                xDist = itemX - selfX                  
                yDist = itemY - selfY
 
                itemDist = ai.itemDist(itemId) # Calcualtes the distance to item
                itemDir = math.atan2(yDist, xDist) # Calculates direction in radians to item
 
                itemVelX = ai.itemVelX(itemId)
                itemVelY = ai.itemVelY(itemId)
                itemSpeed = ai.itemSpeed(itemId)
                
                ai.turnToRad(itemDir) # Turns ship in direction of item
                
                if angleDiff(selfHeading, itemDir) < 0.1:
                    ai.setPower(15)
                    mode = "thrust"
                elif angleDiff(selfHeading, itemDir) < 0.5:
                    mode = "stop"

            else:
                middleDisX = ai.getOption("mapWidth")/2 - selfX                  
                middleDisY = ai.getOption("mapHeight")/2 - selfY                  
                middleDistance = math.hypot(middleDisX, middleDisY) # Calcualtes the distance to checkpoint
                middleDir = math.atan2(middleDisY, middleDisX)
                ai.turnToRad(middleDir)

            if 0 < ai.wallFeelerRad(1000, ai.selfTrackingRad()) < 100: 
                mode = "stop" 

            

                    
        elif mode == "stop":   
            stopCount += 1
            ai.turnToRad(ai.selfTrackingRad() - math.pi)
            ai.setPower(55)
            mode = "thrust"

            if selfSpeed == 0:
                if ai.wallFeelerRad(1000, ai.selfTrackingRad()) > 70: # is 1000 a good value?
                    stopCount = 0
                    ai.setPower(5)
                    mode = "thrust"
            
                else:
                    mode = "aim"

        elif mode == "thrust":
            if 0 < stopCount < 8:
                mode = "stop"
            else:
                mode = "aim"
            
            ai.thrust()

    except:
        print(traceback.print_exc())
    
def angleDiff(one, two):
    """Calculates the smallest angle between two angles"""

    a1 = (one - two) % (2*math.pi)
    a2 = (two - one) % (2*math.pi)
    return min(a1, a2)

#
# Parse the command line arguments
#
parser = OptionParser()

parser.add_option ("-p", "--port", action="store", type="int", 
                   dest="port", default=15348, 
                   help="The port number. Used to avoid port collisions when" 
                   " connecting to the server.")

(options, args) = parser.parse_args()

name = "Stub"

#
# Start the AI
#

ai.start(tick,["-name", name, 
               "-join",
               "-turnSpeed", "64",
               "-turnResistance", "0",
               "-port", str(options.port)])
