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
targetId = -1

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
        global targetId

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

        # Add more sensors readings here
        targetCount = ai.targetCountServer()
        targetCountAlive = 0

        for i in range(targetCount):
            if ai.targetAlive(i):
                targetCountAlive += 1

        print ("tick count:", tickCount, "mode:", mode, "targets alive:", targetCountAlive)


        if mode == "wait":
            if targetCountAlive > 0:
                mode = "aim"

        elif mode == "aim":
            if targetCountAlive == 0:
                mode = "wait"
                return

            # Loop through the indexes of targets and find one that is alive,
            # save that index in targetId.
        
            for target in range(targetCount):
                if ai.targetAlive(target):
                    targetId = target



            # Calculate what direction the target is in, save in
            # the variable targetDirection
                                  
            x = ai.targetX(targetId) - selfX
            y = ai.targetY(targetId) - selfY
            
            targetDirection = math.atan2(y, x)
            targetDistance = math.hypot(x, y)


            # Turn to the direction of the target
            ai.turnToRad(targetDirection)

            # Check if you are aiming in the direction of the target,
            # if so, change mode to travel.
            if angleDiff(targetDirection, ai.selfHeadingRad()) < 0.03:
                if targetDistance < 500:
                    mode = "shoot"
                else:
                    mode = "travel"

        elif mode == "travel":
            
            # Sets the thrustpower to 5 and starts heading towards the target
            ai.setPower(5)
            if selfSpeed < 10:
                ai.thrust()

        

            # Calculate what direction and the distance of the target
            # save in the variable targetDirection and targetDistance

            x = ai.targetX(targetId) - selfX
            y = ai.targetY(targetId) - selfY

            targetDistance = math.hypot(x, y)
            targetDirection = math.atan2(y, x)
            

            # Calculates the angleDiff
            # save in the variable diff
            diff = angleDiff(targetDirection, ai.selfHeadingRad())

            # Check if you are aiming close enough to the target,
            # if not change mode to aim

            if diff > 0.03:
                mode = "aim"

            print(angleDiff(targetDirection, ai.selfTrackingRad()))
            if angleDiff(targetDirection, ai.selfTrackingRad()) > 2:
                mode = "stop"
            if targetDistance < 550 and diff < 0.03:
                mode = "stop"
            
            


        elif mode == "stop":

            # Sets the thrustpower to 5 and the MaxTurnRad to 2*pi
            ai.setPower(10)
            ai.setMaxTurnRad(2*math.pi)


            # Calculate what direction and the distance of the target
            # save in the variable targetDirection and targetDistance

            x = ai.targetX(targetId) - selfX
            y = ai.targetY(targetId) - selfY
            
            targetDirection = math.atan2(y, x)          
            targetDistance = math.hypot(x, y)

            
            # Calculates the angleDiff
            # save in the variable diff
            diff = angleDiff(targetDirection, ai.selfHeadingRad())


            



            if diff < 0.03:
                ai.turnToRad(ai.selfTrackingRad() + math.pi)

            if diff > 0.03:
                ai.thrust()
            
            if selfSpeed < 1:
                ai.turnToRad(selfHeading + math.pi)
                mode = "shoot"
            

            




        elif mode == "shoot":

            x = ai.targetX(targetId) - selfX
            y = ai.targetY(targetId) - selfY
            
            targetDirection = math.atan2(y, x)           
            diff = (angleDiff(targetDirection, ai.selfHeadingRad()))
            print(diff)
            if diff > 0.03:
                mode = "aim"
            if ai.targetAlive(targetId):
                ai.fireShot()
            if not ai.targetAlive(targetId):
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
