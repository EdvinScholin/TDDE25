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

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)                 

        selfHeading = ai.selfHeadingRad() 
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode", mode)
        
        if mode != "stop":
            mode = "travel"
        
        if mode == "travel":
            itemCount = ai.itemCountScreen()
            if itemCount > 0:
                for item in range(itemCount):
                    itemId = item
            else: 
                print("else")
                mode = "stop"
                return
            
            # Items X and Y coordinate.
            itemX = ai.itemX(itemId)
            itemY = ai.itemY(itemId)
        
            xDis = itemX - selfX                  
            yDis = itemY - selfY

            itemDist = ai.itemDist(itemId) # Calcualtes the distance to item
            itemDir = math.atan2(yDis, xDis) # Calculates direction in radians to item

            itemVelX = ai.itemVelX(itemId)
            itemVelY = ai.itemVelY(itemId)
            itemSpeed = ai.itemSpeed(itemId)
            
            ai.turnToRad(1.3) # Turns ship in direction of item

            ai.setPower(5)
            
            if selfSpeed < 8:
                ai.thrust()
 
            if 0 < ai.wallFeelerRad(1000, ai.selfTrackingRad()) < 70: 
                ai.turnToRad(ai.selfTrackingRad() - math.pi) # Rotates the ship 180 degrees
                mode = "stop" 
                    
        if mode == "stop":   
            stopCount += 1
            print(ai.itemCountScreen())
            if ai.itemCountScreen() == 0:
                if 
                ai.turnToRad(ai.selfTrackingRad() - math.pi)
                ai.setPower(20)
                ai.thrust()
                mode = "travel"
                return
            
            if selfSpeed < 13:
                ai.setPower(45)
            else:
                ai.setPower(55)
            
            ai.thrust()

            if stopCount > 6:
                if ai.wallFeelerRad(1000, ai.selfTrackingRad()) > 70: # is 1000 a good value?
                    stopCount = 0
                    mode = "travel"

        if mode == "ready":
            pass

    except:
        print(traceback.print_exc())

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
