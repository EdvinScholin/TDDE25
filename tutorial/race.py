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
mode = "ready"

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

        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
            tickCount = 0
            mode = "ready"
            return

        tickCount += 1
        
        print ("tick count:", tickCount, "mode", mode)

        #
        # Read some "sensors" into local variables, to avoid excessive calls to the API
        # and improve readability.
        #
        selfX = ai.selfX()
        selfY = ai.selfY()
        selfSpeed = ai.selfSpeed()
        
        # Checkpoints X and Y coordinates
        nextCheckpoint = ai.nextCheckpoint()
        checkPointY = ai.checkpointY(nextCheckpoint)
        checkPointX = ai.checkpointX(nextCheckpoint)
        
        selfHeading = ai.selfHeadingRad()
        
        # Calcualtes the distance and direction to checkpoint
        xDir = checkPointX - selfX                  
        yDir = checkPointY - selfY                 
        checkpointDistance = math.hypot(xDir, yDir) 
        checkpointDir = math.atan2(yDir, xDir)

        # Calcualtes which direction the middle is 
        middleDisX = ai.radarWidth()/2 - ai.selfRadarX()                  
        middleDisY = ai.radarHeight()/2 - ai.selfRadarY()                 
        middleDir = math.atan2(middleDisY, middleDisX)
        
        # Allows the ship to turn 360 degrees
        ai.setMaxTurnRad(2*math.pi)

        if mode == "ready":
            mode = "travel"

        elif mode == "travel":
            ai.setPower(20)
            ai.thrust()
            
            # Turns ship in direction of checkpoint
            ai.turnToRad(checkpointDir)
            
            if checkpointDistance < 200:

                mode = "adjust"
                
                # Rotates the ship 180 degrees
                #ai.turnToRad(selfHeading - math.pi)
                #mode = "stop"
        
        elif mode == "stop":
            ai.setPower(55)
            ai.thrust()

            # When ships speed is sufficiently low, 
            # we can begin to travel
            if selfSpeed < 2:
               mode = "ready"

        elif mode == "adjust":
            
            selfTrackRad = ai.selfTrackingRad()

            ai.turnToRad(middleDir)
            selfHeading = ai.selfHeadingRad()
            ai.setPower(45)
            ai.thrust()

            if angleDiff(selfTrackRad, checkpointDir) < 0.05:
                mode = "ready"

        if mode == "ready":
            pass


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
