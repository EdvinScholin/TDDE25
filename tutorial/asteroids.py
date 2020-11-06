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
mode = "wait"
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

        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
            tickCount = 0
            mode = "wait"
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

        # Determine the closest asteroid to self
        targetDistance = 1000 

        for target in range(ai.radarCount()):
            radarDistance = ai.radarDist(target)
            
            if radarDistance < targetDistance:
                targetDistance = radarDistance
                asteroidId = target

        #print(targetDistance)

        #print(asteroidId)

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode", mode)


        if mode == "wait":
            if targetDistance <= 50:
                mode = "aim"

        elif mode == "aim":
            if targetDistance > 50:
                mode = "wait"
                return
        

            # Determine target direction
            x = ai.radarX(asteroidId) - ai.selfRadarX()
            y = ai.radarY(asteroidId) - ai.selfRadarY()
            targetDirection = math.atan2(y, x)
            

            # Turn to target direction
            ai.turnToRad(targetDirection)


            # When aiming at target, change mode to shoot
            if angleDiff(targetDirection, ai.selfHeadingRad()) < 1:
                mode = "shoot"
                

        elif mode == "shoot":

            # Shoot the target
            ai.fireShot()

            # if the target is destroyed, change mode to aim
            mode = "aim"

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
