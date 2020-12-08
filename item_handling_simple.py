#
# This file can be used as a starting point for the bots.
#

import functions_lib as lib
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

# Coordinates - Vill helst ha en tuple
coordinates = []
prevCoordinates = []

# Message handling
tasks = []
lenTasks = 0
send = []

# Movement
prevTrackRad = 0
dist = 0
dirRad = 0

# Items
itemDict = {"fuel": 0, "wideangle": 1, "rearshot": 2, "afterburner": 3, "cloak": 4,
            "sensor": 5, "transporter": 6, "tank": 7, "mine": 8, "missile": 9, "ecm": 10,
            "laser": 11, "emergencythrust": 12, "tractorbeam": 13, "autopilot": 14,
            "emergencyshield": 15, "itemdeflector": 16, "hyperjump": 17, "phasing": 18,
            "mirror": 19, "armor": 20}
prevSelfItem = 0
desiredItemType = -1
item_needed = 1


def tick():
    #
    # The API won't print out exceptions, so we have to catch and print them ourselves.
    #
    try:

        #
        # Declare global variables so we have access to them in the function
        #
        global tickCount
        global prevTrackRad
        global mode
        global itemDict
        global prevSelfItem
        global desiredItemType
        global tasks
        global lenTasks
        global send
        global coordinates
        global prevCoordinates
        global dist
        global dirRad
        global item_needed

        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
            print("dead")
            tickCount = 0
            mode = "ready"
            return

        tickCount += 1

        print("tick count:", tickCount, "mode", mode)

        if tickCount == 1:
            ai.talk("teacherbot: start-mission 9")

        #
        # Read some "sensors" into local variables, to avoid excessive calls to the API
        # and improve readability.
        #

        selfX = ai.selfX()
        selfY = ai.selfY()
        print("selfCoordinates: ", selfX, selfY)
        selfVelX = ai.selfVelX()
        selfVelY = ai.selfVelY()
        selfSpeed = ai.selfSpeed()

        # 0-2pi, 0 in x direction, positive toward y

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)

        wallDistance = ai.wallFeelerRad(1000, ai.selfTrackingRad())

        # Calcualtes which direction the middle is
        middleDisX = ai.radarWidth()/2 - ai.selfRadarX()
        middleDisY = ai.radarHeight()/2 - ai.selfRadarY()
        middleDir = math.atan2(middleDisY, middleDisX)

        # ----------------------------------------------------------------------------
        # Wallfeeler
        # ----------------------------------------------------------------------------

        if lib.brake(wallDistance - 50) and wallDistance != -1:
            prevTrackRad = ai.selfTrackingRad()
            mode = "stop"
            print("wallFeeler")

            '''
            ai.turnToRad(ai.selfTrackingRad() - math.pi)
            print("self heading", ai.selfHeadingRad())
            ai.setPower(55)
            ai.thrust()
            mode = "ready"
            '''

        # ---------------------------------------------------------------------------
        # Ready
        # ---------------------------------------------------------------------------

        if mode == "ready":

            if not tasks:
                mode = "scan"

            else:
                mode = "mission"

        # ---------------------------------------------------------------------------
        # Missions
        # ---------------------------------------------------------------------------

        elif mode == "scan":

            ai.setMaxMsgs(15)
            maxMsgs = ai.getMaxMsgs()

            # Scans all the messages sent by teacherbot
            # and adds them to the list tasks
            for message in range(maxMsgs):
                if ai.scanTalkMsg(message) and "[Teacherbot]:[Stub]" in ai.scanTalkMsg(message):
                    tasks.append(ai.scanTalkMsg(message))
                    ai.removeTalkMsg(message)

            print("tasks1: ", tasks)

            # Save the length of the task in the variable lenTasks
            lenTasks = len(tasks)

            # När vi inte har några kordinater ska vi ta ett nytt föremål.
            # Så länge vi har kordinater håller vi på med ett föremål.
            if not coordinates and tasks:
                for seq in tasks[-1].split():
                    if seq.isdigit():
                        coordinates.append(int(seq))
                    if seq in itemDict.keys():
                        desiredItemType = itemDict[seq]

            mode = "ready"

        elif mode == "mission":

            print("tasks: ", tasks)

            # INPUT: desiredItemType, tasks
            current_task = tasks[-1]
            mode = "navigation"

            if "collect-item" in current_task:

                if not ai.itemCountScreen():
                    ai.turnToRad(middleDir)
                    ai.setPower(55)
                    ai.thrust()
                    mode = "mission"
                    return

                Id = lib.nearest_desired_item_Id(desiredItemType)

                # Targets position relativt self
                x, y = lib.target_future_pos(Id, selfSpeed)

                # If we already have the item
                if prevSelfItem < ai.selfItem(desiredItemType):
                    mode = "completed_task"

            elif "use-item" in current_task:

                if not coordinates:  # Meanes that we fire item

                    # Placed mine position and distance
                    x, y = lib.relative_pos(
                        prevCoordinates[0], prevCoordinates[1])
                    dist = math.hypot(x, y)

                    # Safe distance from explosion
                    if dist > 300:
                        ai.detonateMines()
                        prevCoordinates.clear()
                        mode = "completed_task"

                elif ai.selfItem(desiredItemType) == 0:
                    ai.talk('collect-item mine [Teacherbot]:[Stub]')
                    mode = "scan"
                    return

                else:
                    # Targets position relativt self
                    x, y = lib.relative_pos(coordinates[0], coordinates[1])
                    dist = math.hypot(x, y)

                    # Place mine
                    if dist < 20:
                        ai.dropMine()
                        mode = "completed_task"

            else:  # We cannot handle item
                print("cannot handle task")
                mode = "ready"
                return

            # Distance and direktion to target
            dist = math.hypot(x, y)
            dirRad = math.atan2(y, x)

            # Save how many items of the desired item we already have
            prevSelfItem = ai.selfItem(desiredItemType)

        # ----------------------------------------------------------------
        # Mission completed
        # ----------------------------------------------------------------

        elif mode == "completed_task":

            # Tar inte bort gamla tasket
            current_task = tasks[-1]
            # Adds the completed task to a list send

            # for elem in tasks:
            if '[Teacherbot]:[Stub] [Stub]' not in current_task:
                if coordinates:
                    prevCoordinates = coordinates.copy()
                    coordinates.clear()

                new_msg = ""
                # if str(prevSelfItem) in elem:
                for seq in current_task.split():
                    if not "[" in seq:
                        new_msg += seq + " "
                completed = "Teacherbot:completed " + new_msg
                send.append(completed)
            else:
                completed = "Stub:completed"
                send.append(completed)

            # If you have completed all the tasks send the messages from the send list,
            # clear the send and tasks list and change mode to completed_all_tasks

            print("len send: ", len(send))
            print("len tasks: ", lenTasks)

            if len(send) == lenTasks:
                for elem in send:
                    ai.talk(elem)
                send.clear()
                tasks.clear()
                mode = "completed_all_tasks"

            # If you havent completed all the tasks remove the
            # last task in the list and change mode to cords
            else:
                tasks.pop()
                mode = "ready"

        elif mode == "completed_all_tasks":

            # If you recieve a new message from
            # teacherbot change mode to scan
            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0):
                lenTasks = 0
                mode = "ready"

            '''
            elif mode == "mission done": 
            # Gets the key from the value in our dictionary of our desired 
            # item in order to send a message to teacherbot
            itemStrValue = list(itemDict.keys())[list(
                itemDict.values()).index(desiredItemType)]
            completed = "Teacherbot: completed collect-item " + itemStrValue
            print(ai.scanTalkMsg(0))
            ai.removeTalkMsg(0)
            ai.talk(completed)
            mode = "scan"
            '''

        # ---------------------------------------------------------------------------
        # Navigational modes, input is dist(only if ship need to stop at destination)
        # and dirRad to target
        # ---------------------------------------------------------------------------

        elif mode == "navigation":

            # Aim if any targets are detected
            if selfSpeed < 20:
                ai.setPower(55)
            mode = "aim"

        elif mode == "stop":

            # ai.turnToRad(prevTrackRad - math.pi)

            angle = lib.angleDiff(prevTrackRad, ai.selfTrackingRad())

            if angle > math.pi/2:
                ai.turnToRad(ai.selfTrackingRad() - math.pi)

            else:
                mode = "mission"
                return
            '''
            if angle < math.pi/2:
                mode = "ready"
                return

            print("prevTrackRad: ", prevTrackRad)
            '''
            ai.setPower(55)
            ai.thrust()

        elif mode == "aim":  # dela upp i aim och travel

            # Convert selfTrackingRad and ItemDir to positive radians
            selfTrackRad = ai.selfTrackingRad() % (2*math.pi)
            absItemDir = dirRad % (2*math.pi)

            # Calculate angle difference
            movItemDiff = lib.angleDiff(
                ai.selfTrackingRad(), dirRad)

            # Ship stops when target is reached. Not necessary.
            '''
            if brake(dist + 50):  
                prevTrackRad = ai.selfTrackingRad()
                mode = "stop"
                return
            '''

            # Move towards target
            if selfSpeed < 5 or movItemDiff == math.pi/2:
                angle = dirRad

            elif movItemDiff > math.pi/2:  # if angle between selfTrackingRad and item direction
                print("aim stop.........")
                prevTrackRad = ai.selfTrackingRad()
                mode = "stop"
                return

            else:  # Uses opposite velocity vektor to cancel out unwanted velocity vektors
                angle = 2*absItemDir - selfTrackRad

            mode = "mission"

            ai.turnToRad(angle)
            ai.thrust()

    except:
        print(traceback.print_exc())


#
# Parse the command line arguments
#
parser = OptionParser()

parser.add_option("-p", "--port", action="store", type="int",
                  dest="port", default=15347,
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
