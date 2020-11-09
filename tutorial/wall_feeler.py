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
        itemCount = ai.itemCountScreen()
        if itemCount > 0:
            for item in range(itemCount):
                itemId = item
        else: 
            return # This evades IndexError: No item with that id

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

        selfHeading = ai.selfHeadingRad() 
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode", mode)
        
        if mode != "stop":
            mode = "travel"
        
        if mode == "travel":
            """ai.turnToRad(itemDir)
            dist = distance(xDis, yDis)
            dire = direction(xDis, yDis)
            alpha = math.pi + dire - ai.itemTrackingRad(itemId)

            a = selfSpeed**2 - itemSpeed**2
            b =  2 * dist * itemSpeed * math.cos(alpha)
            c = -dist**2
            disc = (b**2 - 4) * a * c
            if disc < 0: return None
            time = (math.sqrt(disc) - b) / (2 * a)
            print(time)
            x = itemX + itemSpeed * time * math.cos(ai.itemTrackingRad(itemId))
            y = itemY + itemSpeed * time * math.sin(ai.itemTrackingRad(itemId))

            selfDir = direction(x, y)"""

            
            #if ai.wallFeelerRad(100, ai.selfTrackRad()) == -1: 
            if itemDist > 40:
                ai.turnToRad(itemDir) # Turns ship in direction of item
            else:
                ai.turnToRad(itemDir + ai.itemTrackingRad(itemId) - math.pi)
            ai.setPower(5)
            ai.thrust()
 
            if 0 < ai.wallFeelerRad(70, ai.selfTrackingRad()) < 70: #or itemDist < 90:
                ai.turnToRad(ai.selfTrackingRad() - math.pi) # Rotates the ship 180 degrees
                mode = "stop" 
                    
        if mode == "stop":   
            stopCount += 1
            ai.setPower(45)
            ai.thrust()

            if stopCount > 6:
                if ai.wallFeelerRad(1000, ai.selfTrackingRad()) > 70: # is 1000 a good value?
                    stopCount = 0
                    mode = "travel"

        if mode == "ready":
            pass
        print(stopCount)
        print(itemDir) 

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
