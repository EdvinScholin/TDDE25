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
coordinates = []
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
        global coordinates

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
        selfTracking = ai.selfTrackingRad()
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode", mode)


        if mode == "ready":

            ai.talk("teacherbot:start-mission 7")
            mode = "scan"
    

        elif mode == "scan":

            message = ""
            if "move-to-pass" in ai.scanTalkMsg(0):
                message = ai.scanTalkMsg(0)

            for seq in message.split():
                if seq.isdigit():
                    coordinates.append(int(seq))

            if coordinates:
                mode = "aim"

        elif mode == "aim":
            x = coordinates[0] - selfX
            y = coordinates[1] - selfY

            targetDirection = math.atan2(y, x)

            ai.turnToRad(targetDirection)

            print(angleDiff(targetDirection, ai.selfHeadingRad()))
            
            if angleDiff(targetDirection, ai.selfHeadingRad()) < 0.01:
                mode = "travel"
            

        elif mode == "travel":
            ai.setPower(10)
            if selfSpeed < 20:
                ai.thrust()


            x = coordinates[0] - selfX
            y = coordinates[1] - selfY

            targetDirection = math.atan2(y, x)
            targetDistance = math.hypot(x, y)

            print("angleDiff:", angleDiff(targetDirection, selfTracking))
            print("targetDistance:", targetDistance)
            
            if angleDiff(targetDirection, selfTracking) > 0.01:
                ai.turnToRad(selfTracking - math.pi)
                mode = "stop"
            



            print("Target:", coordinates)
            print("Ship:", selfX, selfY)


        elif mode == "stop":
            ai.setPower(30)
            ai.thrust()
            print("speed:", selfSpeed)

            
            


            

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