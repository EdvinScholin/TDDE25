# ==============================================================================
# Filename: path_following.py
#
# Author:   Pontus Molin (@edvsc779),
#           Edvin Schölin (@ponmo676) &
#           Markus Handstedt (@marha066)
#
# Project:  Xpilot
#
# Group:    sg4-spai-03
# ==============================================================================
#
# This file can be used as a starting point for the bots.
#

import functions_lib as lib
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
mode = "wait"

# Message handling
tasks = []
send = []
lenTasks = 0

# Path finding
all_nodes = []
path = []
xCord = 0
yCord = 0

# Movement
prevTrackRad = 0
dirRad = 0

# Counters
stopCount = 0
stopCount2 = 0


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

        global tasks
        global send
        global lenTasks

        global all_nodes
        global path
        global xCord
        global yCord

        global prevTrackRad
        global dirRad

        global stopCount      
        global stopCount2
        
        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
            tickCount = 0
            if stopCount2 == 0:
                mode = "wait"
            else:
                mode = "cords"
            return

        tickCount += 1
        stopCount2 += 1

        #
        # Read some "sensors" into local variables, to avoid excessive calls to the API
        # and improve readability.
        #

        selfX = ai.selfX()
        selfY = ai.selfY()
        selfSpeed = ai.selfSpeed()
        selfTrackingRad = ai.selfTrackingRad()

        playerCount = ai.playerCountServer()
        pi = math.pi

        mapWidth = ai.mapWidthBlocks()
        mapHeight = ai.mapHeightBlocks()

        ai.setMaxMsgs(15)
        maxMsgs = ai.getMaxMsgs()

        wallDistance = ai.wallFeelerRad(1000, selfTrackingRad)

        ai.setMaxTurnRad(2*pi)

        print("tick count:", tickCount, "mode:", mode)

        # Turns off the shield when we spawn
        if tickCount == 1:
            ai.shield()

        # ----------------------------------------------------------------------------
        # Wallfeeler
        # ----------------------------------------------------------------------------

        if lib.brake(wallDistance) and wallDistance != -1:
            prevTrackRad = selfTrackingRad
            mode = "stop"

        # ----------------------------------------------------------------------------
        # Wait for players
        # ----------------------------------------------------------------------------

        if mode == "wait":
            if playerCount > 1:
                mode = "ready"

        # ----------------------------------------------------------------------------
        # Ready
        # ----------------------------------------------------------------------------

        elif mode == "ready":
            stopCount += 1

            # If you are alone on the server change mode to wait
            if playerCount == 1:
                mode = "wait"
                return

            # Starts mission 7 and create the map
            if stopCount == 1:
                ai.talk("Teacherbot:start-mission 10")

                for x in range(mapWidth):
                    for y in range(mapHeight):
                        if (ai.mapData(x, y) == 0 or 30 <= ai.mapData(x, y) <= 39):
                            all_nodes.append((x, y))

            # When you recieve a message from Teacherbot change mode to scan
            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0):
                mode = "scan"

        # ----------------------------------------------------------------------------
        # Path finding
        # ----------------------------------------------------------------------------

        elif mode == "scan":

            # Clears the tasks list
            tasks.clear()

            # Scans all the messages sent by Teacherbot
            # and adds them to the list tasks
            for message in range(maxMsgs):
                if ai.scanTalkMsg(message) and "[Teacherbot]:[Stub]" in ai.scanTalkMsg(message):
                    tasks.append(ai.scanTalkMsg(message))
                    ai.removeTalkMsg(message)

            # Save the length of the task in the variable lenTasks
            lenTasks = len(tasks)

            # Change mode to navigation
            mode = "cords"

        elif mode == "cords":

            # Saves the coordinates of the last message in
            # tasks in the variables xCord and yCord
            coordinates = []
            for seq in tasks[-1].split():
                if seq.isdigit():
                    coordinates.append(int(seq))
            xCord = coordinates[0]
            yCord = coordinates[1]

            # Change mode to path
            mode = "path"

        elif mode == "path":

            # Calculate the start and goal position of the path
            selfBlock = lib.pixel_to_block(selfX, selfY)
            goal = lib.pixel_to_block(xCord, yCord)

            # Create the path using an a* algorithm
            path = list(astar.find_path(selfBlock, goal, neighbors_fnct=neighbors,
                                        heuristic_cost_estimate_fnct=heuristic_cost_estimate,
                                        distance_between_fnct=block_distance)
                        )

            # Remove the first block of the path
            path.remove(selfBlock)

            # Change mode to navigation
            mode = "navigation"

        # ----------------------------------------------------------------------------
        # Mission handling
        # ----------------------------------------------------------------------------

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
            # last task in the list and change mode to navigation
            else:
                tasks.pop()
                mode = "cords"

        elif mode == "completed_all_tasks":

            # If you recieve a new message from
            # Teacherbot change mode to scan
            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0):
                lenTasks = 0
                mode = "scan"

        # ----------------------------------------------------------------------------
        # Navigation
        # ----------------------------------------------------------------------------

        elif mode == "navigation":

            # Calculate the targetDircetion and targetDistance
            selfBlock = lib.pixel_to_block(selfX, selfY)
            x = path[0][0] - selfBlock[0]
            y = path[0][1] - selfBlock[1]
            dirRad = math.atan2(y, x)
            targetDistance = math.hypot(x, y)

            # Convert selfTrackingRad and ItemDir to positive radians
            selfTrackRad = selfTrackingRad % (2*math.pi)
            absItemDir = dirRad % (2*math.pi)

            # Calculate angle difference
            movItemDiff = lib.angleDiff(
                selfTrackingRad, dirRad)

            # If you are in the targetblock remove to first element from
            # the list and change mode to navigation if the length of the list is 1 or 0
            if targetDistance == 0:
                path.pop(0)
                if len(path) == 1 or not path:
                    mode = "stop"
                return

            # Move towards target
            if selfSpeed < 5 or movItemDiff == math.pi/2:
                angle = dirRad

            # If angle between selfTrackingRad and item direction is to big change mode to stop
            elif movItemDiff > math.pi/2:
                prevTrackRad = selfTrackingRad
                mode = "stop"
                return

            # Uses opposite velocity vektor to cancel out unwanted velocity vektors
            else:
                angle = 2*absItemDir - selfTrackRad

            # Aims at the target and thrusts
            ai.turnToRad(angle)
            ai.thrust()

        elif mode == "stop":

            # Calculate angle difference
            angle = lib.angleDiff(prevTrackRad, selfTrackingRad)

            if angle > math.pi/2:
                if len(path) == 1 or not path:
                    prevTrackRad = selfTrackingRad
                    mode = "completed_task"
                else:
                    path.pop(0)
                    mode = "navigation"

            if angle < math.pi/2:
                ai.turnToRad(selfTrackingRad - math.pi)

            # Aims at the target and thrusts
            ai.setPower(55)
            ai.thrust()

    except:
        print(traceback.print_exc())


def neighbors(node):
    """ Calculates the neighbors to a node """
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1),
            (-1, 0), (-1, -1), (0, -1), (1, -1)]
    result = []
    for dir in dirs:
        neighbor = (node[0] + dir[0], node[1] + dir[1])
        if neighbor in all_nodes:
            result.append(neighbor)
    return result


def heuristic_cost_estimate(n1, n2):
    """ If a node is next to wall increase the cost to 5 """
    if block_neighbors(n1):
        return 100
    return 1


def block_distance(n1, n2):
    """ Calculates the block_distance between two nodes """
    (x1, y1) = n1
    (x2, y2) = n2
    return math.hypot(x2 - x1, y2 - y1)


def block_neighbors(node):
    """ Checks if a node has a neighbor that is a block """
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1),
            (-1, 0), (-1, -1), (0, -1), (1, -1)]
    for dir in dirs:
        neighbor = (node[0] + dir[0], node[1] + dir[1])
        if ai.mapData(neighbor[0], neighbor[1]) == 1:
            return True
    return False


#
# Parse the command line arguments
#
parser = OptionParser()

parser.add_option("-p", "--port", action="store", type="int",
                  dest="port", default=15348,
                  help="The port number. Used to avoid port collisions when"
                  " connecting to the server.")

(options, args) = parser.parse_args()

name = "Stub"

#
# Start the AI
#

ai.start(tick, ["-name", name,
                "-join",
                "-turnSpeed", "64",
                "-turnResistance", "0",
                "-port", str(options.port)])
