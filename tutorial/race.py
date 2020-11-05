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
        
        nextCheckpoint = ai.nextCheckpoint()
        checkPointY = ai.checkpointY(nextCheckpoint)
        checkPointX = ai.checkpointX(nextCheckpoint)
        
        selfHeading = ai.selfHeadingRad() 
        
        xDir = checkPointX - selfX                  
        yDir = checkPointY - selfY                  
        checkpointDistance = math.hypot(xDir, yDir) # Calcualtes the distance to checkpoint
        checkpointDir = math.atan2(yDir, xDir)      # Calculates direction in radians to checkpoint
        
        ai.setMaxTurnRad(2*math.pi)                 # Allows the ship to turn 360 degrees

        if mode != "stop":
            mode = "travel"

        if mode == "travel":
            ai.setPower(30)
            ai.thrust()
            ai.turnToRad(checkpointDir)             # Turns ship in direction of checkpoint
            
            if checkpointDistance < 200:
                ai.turnToRad(selfHeading - math.pi) # Rotates the ship 180 degrees
                mode = "stop"
        
        if mode == "stop":
            ai.setPower(45)
            ai.thrust()

            if selfSpeed < 2:
               mode = "travel"
     
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode", mode)


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
