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
tasks = []
send = []
lenTasks = 0
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
        global tasks
        global send
        global lenTasks
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
        maxMsgs = ai.getMaxMsgs()

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
                ai.talk("Teacherbot:start-mission 7")

            # When you recieve a message from teacherbot change mode to scan
            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0):
                mode = "scan"


        elif mode == "scan":

            # Clears the tasks list
            tasks.clear()

            # Scans all the messages sent by teacherbot
            # and adds them to the list tasks
            for message in range(maxMsgs):
                if ai.scanTalkMsg(message) and "[Teacherbot]:[Stub]" in ai.scanTalkMsg(message):
                    tasks.append(ai.scanTalkMsg(message))
                    ai.removeTalkMsg(message) 

            # Save the length of the task in the variable lenTasks
            lenTasks = len(tasks)

            # Saves the coordinates of the last message in
            # tasks in the variables xCord and yCord
            coordinates = []
            for seq in tasks[-1].split():
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
            print(angleDiff(targetDirection, ai.selfHeadingRad()))
            if angleDiff(targetDirection, ai.selfHeadingRad()) < 0.03:
                mode = "travel"


        elif mode == "travel":


            
            # If you are close to the target head towards it with 
            # a low speed and when really close change mode to stop
            if targetDistance < 300:
                ai.setPower(5)
                if selfSpeed < 10:
                    ai.thrust()
                if targetDistance < 20:
                    ai.turnToRad(selfHeading + pi)
                    mode = "stop"

            # If you are far away from the target 
            # head towards it with a higher speed
            if targetDistance > 300:
                ai.setPower(10)
                if selfSpeed < 30:
                    ai.thrust()

            # If you are close to the target change mode to stop
            if targetDistance < 350 and targetDistance > 300:
                ai.turnToRad(selfHeading + pi)
                mode = "stop"
            

        elif mode == "stop":

            # If you are really close to the target with
            # a low speed change mode to completed_task
            if targetDistance < 50:
                ai.setPower(10)
                ai.thrust()
                if selfSpeed < 0.4:
                    mode = "completed_task"               

            # If you're further away from the target and
            # have a low speed change mode to travel
            else:
                ai.setPower(25)
                ai.thrust()
   
                if selfSpeed < 0.5:
                    ai.turnToRad(targetDirection)
                    mode = "travel"


        elif mode == "completed_task":

            # Adds the completed task to a list send
            for elem in tasks:
                new_msg = ""
                if str(xCord) in elem and str(yCord) in elem:
                    for seq in elem.split():
                        if not "[" in seq:
                            new_msg += seq + " "
                    completed = "Teacherbot:completed " + new_msg
                    send.append(completed)
            
            # If you have completed all the tasks send the messages from the send list,
            # clear the send and tasks list and change mode to completed_all_tasks
            if len(send) == lenTasks:
                for elem in send:
                    ai.talk(elem)
                send.clear()
                tasks.clear()
                mode = "completed_all_tasks"

            # If you havent completed all the tasks remove the
            # last task in the list and change mode to aim
            else:
                tasks.pop()
                mode = "aim"
                 

        elif mode == "completed_all_tasks":

            # If you recieve a new message from 
            # teacherbot change mode to scan
            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0):
                lenTasks = 0
                mode = "scan"

            


            
            


            

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
