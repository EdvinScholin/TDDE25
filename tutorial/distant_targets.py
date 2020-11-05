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
        ai.setMaxTurnRad(2*math.pi)
        selfX = ai.selfX()
        selfY = ai.selfY()
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

            # Loop through the indexes of targets and find one that is alive
            # save that index in targetId         
            for target in range(targetCount):
                if ai.targetAlive(target):
                    targetId = target


            # Calculates the direction and disctance of the target
            # save in the variables targetDirection and targetDistance                                  
            x = ai.targetX(targetId) - selfX
            y = ai.targetY(targetId) - selfY
            
            targetDirection = math.atan2(y, x)
            targetDistance = math.hypot(x, y)


            # Turn to the direction of the target
            ai.turnToRad(targetDirection)


            # Check if you are aiming in the direction of the target
            # if so, change mode to travel or if you are close change to shoot
            if angleDiff(targetDirection, ai.selfHeadingRad()) < 0.03:
                if targetDistance < 500:
                    mode = "shoot"
                else:
                    mode = "travel"


        elif mode == "travel":
            
            # Sets the thrustpower to 10 and starts heading towards the target
            ai.setPower(10)
            ai.thrust()


            # Calculates the direction and disctance of the target
            # save in the variables targetDirection and targetDistance
            x = ai.targetX(targetId) - selfX
            y = ai.targetY(targetId) - selfY

            targetDistance = math.hypot(x, y)
            targetDirection = math.atan2(y, x)
            

            # If the angle differnce between the targetDirection and
            # the direction of the ship is to big change mode to stop
            if angleDiff(targetDirection, ai.selfTrackingRad()) > 1:
                mode = "stop"


            # If you are close to the target change mode to stop
            if targetDistance < 500:
                mode = "stop"
            

        elif mode == "stop":

            # Sets the thrustpower to 45
            ai.setPower(45)
            

            # Calculate the direction and distance of the target
            # save in the variable targetDirection and targetDistance
            x = ai.targetX(targetId) - selfX
            y = ai.targetY(targetId) - selfY
            
            targetDirection = math.atan2(y, x)          
            targetDistance = math.hypot(x, y)

        
            # Turns around and starts heading in the oposite direction
            ai.turnToRad(ai.selfTrackingRad() + math.pi)
            ai.thrust()
            

            # If the speed of the ship is low enough change mode to shoot
            # and if you are fare away from the target change mode to aim
            if selfSpeed < 1:
                ai.turnToRad(selfHeading + math.pi)
                if targetDistance > 500:
                    mode = "aim"
                else:
                    mode = "shoot"
            

        elif mode == "shoot":

            # Calculate the direction of the target
            # save in the variable targetDirection
            x = ai.targetX(targetId) - selfX
            y = ai.targetY(targetId) - selfY
            
            targetDirection = math.atan2(y, x)           
        
            
            # Change mode to aim if you are not looking at the target
            if (angleDiff(targetDirection, ai.selfHeadingRad())) > 0.05:
                mode = "aim"

            
            # Shoots the target
            if ai.targetAlive(targetId):
                ai.fireShot()
                

            # If the target is dead change mode to aim    
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
