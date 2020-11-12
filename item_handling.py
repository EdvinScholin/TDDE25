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
prevTrackRad = 0
mode = "ready"
# add more if needed

def tick():
    #
    # The API won't print out exceptions, so we have to catch and print them ourselves.
    #
    try:

        #
        # Declare global variables so we have access to them in the function
        #
        global tickCount
        global mode
        global prevTrackRad

        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
            tickCount = 0
            mode = "ready"
            return

        tickCount += 1

        #
        # Read some "sensors" into local variables, to avoid excessive calls to the API
        # and improve readability.
        #

        selfX = ai.selfX()
        selfY = ai.selfY()
        selfVelX = ai.selfVelX()
        selfVelY = ai.selfVelY()
        selfSpeed = ai.selfSpeed()

        selfHeading = ai.selfHeadingRad() 
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here
        itemCountScreen = ai.itemCountScreen()
        previousItemDist = 1000

        for index in range(itemCountScreen):
            itemDist = ai.itemDist(index)
            if itemDist < previousItemDist:
                previousItemDist = itemDist
                itemId = index
        
        # Calcualtes which direction the middle is 
        middleDisX = ai.radarWidth()/2 - ai.selfRadarX()                  
        middleDisY = ai.radarHeight()/2 - ai.selfRadarY()                 
        middleDir = math.atan2(middleDisY, middleDisX)

        itemCount = ai.itemCountScreen()

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)                 

        selfHeading = ai.selfHeadingRad() 

        print ("tick count:", tickCount, "mode", mode)

        if mode == "ready":
            if itemCountScreen > 0:
                mode = "aim"
            '''
            else:
                ai.turnToRad(middleDir)
                
                if angleDiff(selfHeading, middleDir) < 0.1: 
                    if selfSpeed < 8:
                        ai.setPower(12)
                    else:
                        ai.setPower(5)
                    mode = "thrust"
                
                elif angleDiff(selfHeading, middleDir) < 0.5:
                    mode = "stop"
            '''
        if mode == "aim":
            if itemCountScreen == 0:
                mode == "ready"
                return
            
            # Items X and Y coordinate.
            itemX = ai.itemX(itemId)
            itemY = ai.itemY(itemId)
        
            # X and Y coordinates relative to self
            xDist = itemX - selfX                  
            yDist = itemY - selfY

            # Calculates direction in radians to item
            itemDir = math.atan2(yDist, xDist)
            
            # Turns ship in direction of item
            ai.turnToRad(itemDir) 
            
            # Thrust if we are in a sufficient right direction
            if angleDiff(selfHeading, itemDir) < 0.1:
                
                # Stops accelerating
                if selfSpeed < 7:
                    ai.setPower(12)
                else:
                    ai.setPower(5)
                mode = "thrust"
            
            # Stop if we are in a sufficient wrong direction
            elif angleDiff(selfHeading, itemDir) < 0.5:
                ai.turnToRad(ai.selfTrackingRad() - math.pi)
                prevTrackRad = ai.selfTrackingRad()

                mode = "stop"
        
        if mode == "stop":
            
            if ai.selfTrackingRad() == prevTrackRad - math.pi:
                mode = "stop"
            else:
                mode = "ready"

            ai.setPower(30)
            ai.thrust()
            print(ai.selfTrackingRad())

        if mode == "thrust": 
            mode = "ready"
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
