#
# This file can be used as a starting point for the bots.
#

import sys
import traceback
import math
import libpyAI as ai
import astar
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
all_nodes = []
path = []
# add more if needed
blockSize = ai.blockSize()

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
        global all_nodes
        global path
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
        

        sq = chr(9610)
        mapWidth = ai.mapWidthBlocks()
        mapHeight = ai.mapHeightBlocks()

        ai.setMaxMsgs(15)
        maxMsgs = ai.getMaxMsgs()

        ai.setMaxTurnRad(2*pi)
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode:", mode)

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
                ai.talk("Teacherbot:start-mission 10")
                for x in range(mapWidth):
                    for y in range(mapHeight):
                        if ai.mapData(x, y) == 0:
                            all_nodes.append((x, y))


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
            mode = "path"

        elif mode == "path":
         
            selfBlock = pixel_to_block(selfX, selfY)
            goal = pixel_to_block(xCord, yCord)


            path = list(astar.find_path(selfBlock, goal, neighbors_fnct=neighbors,
                        heuristic_cost_estimate_fnct=cost, distance_between_fnct=distance))

            print(path)
            mode = "aim"









        elif mode == "aim":
            selfBlock = pixel_to_block(selfX, selfY)


            x = path[1][0] - selfBlock[0]
            y = path[1][1] - selfBlock[1]

            targetDirection = math.atan2(y, x)
            targetDistance = math.hypot(x, y)


            print(targetDirection)
            print(targetDistance)

            ai.turnToRad(targetDirection)

            if angleDiff(targetDirection, selfHeading) < 0.03:
                mode = "travel"
            

        elif mode == "travel":
            ai.setPower(5)

            selfBlock = pixel_to_block(selfX, selfY)
            x = path[1][0] - selfBlock[0]
            y = path[1][1] - selfBlock[1]
            targetDirection = math.atan2(y, x)
            targetDistance = math.hypot(x, y)

            if len(path) > 2:
                a = path[2][0] - path[1][0]
                b = path[2][1] - path[1][1]
                nextTargetDirection = math.atan2(b, a)



            ai.thrust()
            

            print(path)

            if targetDistance == 0:
                path.pop(0)
                if len(path) == 2:
                    ai.turnToRad(selfHeading - pi)
                    mode = "stop"
                elif angleDiff(nextTargetDirection, selfHeading) > 0.1:
                    ai.turnToRad(selfHeading - pi)
                    mode = "stop"
                else:
                    mode = "aim"
            
            

        elif mode == "stop":
            ai.setPower(5)
            ai.thrust()

            if selfSpeed < 0.1:
                mode = "aim"
            


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

def pixel_to_block(x, y):
    blockX = x//blockSize
    blockY = y//blockSize
    return (blockX, blockY)

def neighbors(node):
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1),(-1, 0), (-1, -1), (0, -1), (1, -1)]
    result = []
    for dir in dirs:
        neighbor = (node[0] + dir[0], node[1] + dir[1])
        if neighbor in all_nodes:
            result.append(neighbor)
    return result

def cost(n1, n2):
    return 1

def distance(n1, n2):
    (x1, y1) = n1
    (x2, y2) = n2
    return math.hypot(x2 - x1, y2 - y1)




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
