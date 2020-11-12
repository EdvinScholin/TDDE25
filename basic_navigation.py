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
mode = "wait"
xCord = 0
yCord = 0
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
        global xCord
        global yCord
        global stopCount

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
        selfSpeed = ai.selfSpeed()

        selfHeading = ai.selfHeadingRad() 
        playerCount = ai.playerCountServer()
        pi = math.pi

        x = xCord - selfX
        y = yCord - selfY

        targetDirection = math.atan2(y, x)
        targetDistance = math.hypot(x, y)

        ai.setMaxMsgs(15)

        ai.setMaxTurnRad(2*pi)
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode:", mode, "targetDistance:", round(targetDistance))

        if mode == "wait" :
            if playerCount > 1:
                mode = "ready"


        elif mode == "ready":
            stopCount += 1

            # If you are alone on the server change mode to wait
            if playerCount == 1:
                mode = "wait"
                return

            # Starts mission 7
            if stopCount == 1:
                ai.talk("teacherbot:start-mission 7")

            # 
            message = ai.scanTalkMsg(0)
            coordinates = []
            for seq in message.split():
                if seq.isdigit():
                    coordinates.append(int(seq))

            # If you have recieved a message from teacherbot
            # and its a new message change mode to scan
            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0) and coordinates[0] != xCord:
                mode = "scan"
    

        elif mode == "scan":

            # Scans the latest message and saves the coordinates
            # in the variables xCord and yCord
            message = ai.scanTalkMsg(0)
            coordinates = []
            for seq in message.split():
                if seq.isdigit():
                    coordinates.append(int(seq))
            xCord = coordinates[0]
            yCord = coordinates[1]

            # Change mode to aim
            mode = "aim"

        elif mode == "aim":

            # Turns to the target
            ai.turnToRad(targetDirection)
            
            # If you are looking at the target change mode to travel
            if angleDiff(targetDirection, ai.selfHeadingRad()) < 0.03:
                mode = "travel"
            

        elif mode == "travel":

            # Sets the thrustpower to 10 and starts heading towards the target
            ai.setPower(10)
            if selfSpeed < 20:
                ai.thrust()

            # If you are close to the target turn around and change mode to stop
            if targetDistance < 300:
                ai.turnToRad(selfHeading + pi)
                mode = "stop"


        elif mode == "stop":

            # Sets the thrustpower to 20 and starts thrusting
            ai.setPower(20)
            ai.thrust()

            # If the speed of the ship is low enough look
            # at the ship and change mode to close_target          
            if selfSpeed < 0.5:
                ai.turnToRad(targetDirection)
                mode = "close_target"

        elif mode == "close_target":

            # Sets the thrustpower to 10 and starts heading towards the target
            ai.setPower(5)
            if selfSpeed < 10:
                ai.thrust()

            # If you are close to the target turn around and change mode to close_stop
            if targetDistance < 20:
                ai.turnToRad(selfHeading + pi)
                mode = "close_stop"

        elif mode == "close_stop":
            # Sets the thrustpower to 10 and starts thrusting
            ai.setPower(10)
            ai.thrust()

            # If the speed of the ship is low enough change mode to done 
            if selfSpeed < 0.5:
                mode = "done"

        elif mode == "done":

            # Copy the last message and add completed
            message = ai.scanTalkMsg(0)
            new_msg = ""
            for seq in message.split():
                if not "[" in seq:
                    new_msg += seq + " "
            completed = "Teacherbot:completed " + new_msg

            # If the mission was move-to-stop change mode to completed
            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0) and "move-to-stop" in ai.scanTalkMsg(0):
                ai.talk(completed)
                mode = "completed"

            # If the mission was move-to-pass change mode to ready
            elif "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0):
                ai.talk(completed)
                mode = "ready"



        
            


            
            


            

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