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
        selfSpeed = ai.selfSpeed()

        middleDisX = ai.radarWidth()/2 - ai.selfRadarX()                  
        middleDisY = ai.radarHeight()/2 - ai.selfRadarY()                  
        middleDir = math.atan2(middleDisY, middleDisX)      # Calcualtes which direction the middle is

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
 
                itemDir = math.atan2(yDist, xDist) # Calculates direction in radians to item
                
                ai.turnToRad(itemDir) # Turns ship in direction of item
                
                if angleDiff(selfHeading, itemDir) < 0.1: # Thrust if we are in a sufficient right direction
                    if selfSpeed < 7:
                        ai.setPower(12)
                    else:
                        ai.setPower(5)
                    mode = "thrust"
                
                elif angleDiff(selfHeading, itemDir) < 0.5: # Stop if we are in a sufficient wrong direction
                    mode = "stop"
                
            else:
                ai.turnToRad(middleDir) # If an item is not visible --> go to middle of map
                
                if angleDiff(selfHeading, middleDir) < 0.1: 
                    if selfSpeed < 8:
                        ai.setPower(12)
                    else:
                        ai.setPower(5)
                    mode = "thrust"
                
                elif angleDiff(selfHeading, middleDir) < 0.5:
                    mode = "stop"
    
            if 0 < ai.wallFeelerRad(1000, ai.selfTrackingRad()) < 100: # If close enough to a wall --> stop
                mode = "stop"
                    
        elif mode == "stop":   
            
            stopCount += 1
            ai.turnToRad(ai.selfTrackingRad() - math.pi)
            ai.setPower(55)
            mode = "thrust"

        elif mode == "thrust":      # We are stopping for 7 ticks
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
