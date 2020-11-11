#
# This file can be used as a starting point for the bot in exercise 1
#

import sys
import traceback
import math
import os
import libpyAI as ai
from optparse import OptionParser


#
# Create global variables that persist between ticks.
#

tickCount = 0
mode = "wait"
targetId = -1

def tick():
    #
    # The API won't print out exceptions, so we have to catch and print them ourselves.
    #
    try:

        #
        # Declare global variables so we're allowed to use them in the function
        #

        global tickCount
        global mode
        global targetId

        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
            tickCount = 0
            mode = "aim"
            return

        tickCount += 1


        #
        # Read some "sensors" into local variables to avoid excessive calls to the API
        # and improve readability.
        #
        selfX = ai.selfX()
        selfY = ai.selfY()
        
        selfHeading = ai.selfHeadingRad()

        targetCount = ai.targetCountServer()
        targetCountAlive = 0

        for i in range(targetCount):
            if ai.targetAlive(i):
                targetCountAlive += 1

        print("tick count:", tickCount, "mode:", mode, "heading:",
                round(math.degrees(selfHeading)), "targets alive:", targetCountAlive)


        if mode == "wait":
            if targetCountAlive > 0:
                mode = "aim"

        elif mode == "aim":
            if targetCountAlive == 0:
                mode = "wait"
                return

            # Loop through the indexes of targets and find one that is alive,
            # save that index in targetId.
            targetCount = ai.targetCountServer()
            for target in range(targetCount):
                if ai.targetAlive(target):
                    targetId = target
                    
            # Calculate what direction the target is in, save in
            # the variable targetDirection
            x = ai.targetX(targetId) - selfX
            y = ai.targetY(targetId) - selfY

            targetDirection = math.atan2(y, x)

            # Turn to the direction of the target
            ai.turnToRad(targetDirection)
            
            # Check if you are aiming in the direction of the target,
            # if so, change mode to shoot.
            # Note that, due to how the game handles angles, the difference
            # cannot be 0 for many angles.
            if angleDiff(targetDirection, ai.selfHeadingRad()) < 0.01:
                if ai.targetAlive(targetId):
                    mode = "shoot"
                
        elif mode == "shoot":

            # Shoot the target
            ai.fireShot()

            # if the target is destroyed, change state to aim
            if not ai.targetAlive(targetId):
                mode = "aim"


    except:
        #
        # If tick crashes, print debugging information
        #
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
        help="The port to use. Used to avoid port collisions when"
        " connecting to the server.")

(options, args) = parser.parse_args()

name = "Exc. 1 skeleton" #Feel free to change this

#
# Start the main loop. Callback are done to tick.
#

ai.start(tick, ["-name", name,
    "-join",
    "-turnSpeed", "64",
    "-turnResistance", "0",
    "-port", str(options.port)])
