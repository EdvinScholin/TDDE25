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

# Coordinates
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

# Counters
shieldOnCount = -1
compCounter = 0
missionCount = 0


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
        global lenTasks
        global send

        global coordinates
        global prevCoordinates

        global prevTrackRad
        global dist
        global dirRad

        global itemDict
        global prevSelfItem
        global desiredItemType

        global shieldOnCount
        global compCounter
        global missionCount

        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
            print("dead")
            tickCount = 0
            mode = "ready"
            return

        if ai.playerCountServer() == 1:
            mode = "completed_task"

        tickCount += 1
        missionCount += 1

        # In case we die, we do not want to restart the mission
        if missionCount == 1:
            ai.talk("teacherbot: start-mission 9")

        # Ship starts with a shield and we want to deactivate it in the beginnning
        if tickCount == 1:
            ai.shield()

        print("tick count:", tickCount, "mode", mode)

        # ----------------------------------------------------------------------------
        # Read some "sensors" into local variables, to avoid excessive calls to the API
        # and improve readability.
        # ----------------------------------------------------------------------------

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)

        selfX = ai.selfX()
        selfY = ai.selfY()
        selfSpeed = ai.selfSpeed()
        selfTrackingRad = ai.selfTrackingRad()
        selfHeading = ai.selfHeadingRad()

        selfRadarX = ai.selfRadarX()
        selfRadarY = ai.selfRadarY()
        radarWidth = ai.radarWidth()
        radarHeight = ai.radarHeight()

        # Calcualtes which direction the middle is
        middleRelX = radarWidth/2 - selfRadarX
        middleRelY = radarHeight/2 - selfRadarY
        middleDir = lib.direction(middleRelX, middleRelY)

        wallDistance = ai.wallFeelerRad(1000, selfTrackingRad)

        shipCountScreen = ai.shipCountScreen()

        # ----------------------------------------------------------------------------
        # Wallfeeler
        # ----------------------------------------------------------------------------

        if lib.brake(wallDistance) and wallDistance != -1:
            prevTrackRad = selfTrackingRad
            mode = "stop"

        # ----------------------------------------------------------------------------
        # Ship detector and ship avoider
        # ----------------------------------------------------------------------------

        if shipCountScreen > 1:
            shipId = lib.nearest_ship_Id(selfX, selfY)
            shipX = ai.shipX(shipId)
            shipY = ai.shipY(shipId)

            selfRelShipX, selfRelShipY = lib.relative_pos(
                selfX, selfY, shipX, shipY)

            selfShipDist = lib.distance(selfRelShipX, selfRelShipY)

            # Avoids crashing into another ship
            if lib.brake(selfShipDist):
                prevTrackRad = selfTrackingRad
                mode = "stop"

        # ----------------------------------------------------------------------------
        # Shield
        # ----------------------------------------------------------------------------

        if -1 < shieldOnCount < 10:
            shieldOnCount += 1
            ai.shield()

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

            # Save the length of the task in the variable lenTasks
            lenTasks = len(tasks)

            # When coordinates is empty, we want to check what the next desired item is.
            # As long as coordinates is not empty, we are still handling the current
            # desired item.
            if not coordinates and tasks:
                for seq in tasks[-1].split():
                    if seq.isdigit():
                        coordinates.append(int(seq))
                    if seq in itemDict.keys():
                        desiredItemType = itemDict[seq]

            mode = "ready"

        elif mode == "mission":
            if not tasks:
                mode = "scan"

            # Starting with the most recent task
            current_task = tasks[-1]
            mode = "navigation"

            if "collect-item" in current_task:

                if ai.itemCountScreen() == 0:
                    ai.turnToRad(middleDir)

                    if selfSpeed < 20:
                        ai.setPower(55)

                    ai.thrust()
                    mode = "mission"
                    return

                Id = lib.nearest_desired_item_Id(desiredItemType)

                # Targets position relative to self
                x, y = lib.target_future_pos(Id, selfSpeed)

                # If we acquired the item we can start handling it
                if prevSelfItem < ai.selfItem(desiredItemType):
                    mode = "completed_task"
                    return

            elif "use-item" in current_task:

                # In order to handle an item, we have to acquire it
                itemStrValue = list(itemDict.keys())[list(
                    itemDict.values()).index(desiredItemType)]

                if (ai.selfItem(desiredItemType) == 0
                        and f'collect-item {itemStrValue} [Teacherbot]:[Stub]' not in current_task):

                    ai.talk('collect-item ' + itemStrValue +
                            ' [Teacherbot]:[Stub]')

                    mode = "scan"
                    return

                elif "mine" in current_task:

                    if coordinates:

                        # Targets position relative to self
                        x, y = lib.relative_pos(selfX, selfY,
                                                coordinates[0], coordinates[1])

                        # Distance to dropzone
                        dist = lib.distance(x, y)

                        # Place mine
                        if dist < 50:
                            ai.dropMine()
                            prevTrackRad = selfTrackingRad
                            mode = "completed_task"
                            return

                        # Ship stops when target is reached.
                        if lib.brake(dist):
                            prevTrackRad = selfTrackingRad
                            mode = "stop"
                            return

                    else:

                        if shipCountScreen == 1:
                            ai.turnToRad(middleDir)

                            if selfSpeed < 20:
                                ai.setPower(55)

                            ai.thrust()
                            mode = "mission"
                            return

                        dirRad = lib.direction(selfRelShipX, selfRelShipY)

                        # Under the right circumstances we want to detach mine and "shoot"
                        # the mine on the enemy ship
                        if (selfSpeed > 10 and lib.angleDiff(selfTrackingRad, dirRad) < 0.1) or selfShipDist < 100:
                            ai.detachMine()

                            # If we are too close to the detonation, we need a shield
                            if selfShipDist < 300:
                                ai.shield()
                                shieldOnCount = 0

                            prevTrackRad = selfTrackingRad
                            mode = "completed_task"

                        else:
                            mode = "navigation"

                        return

                elif "missile" in current_task:
                    ai.lockClose()
                    ai.fireMissile()
                    mode = "completed_task"

                elif "fuel" in current_task:
                    ai.refuel()
                    mode = "completed_task"
                    return

                elif "emergencyshield" in current_task:
                    ai.emergencyShield()
                    ai.shield()
                    shieldOnCount = 0

                    mode = "completed_task"
                    return

                elif "laser" in current_task:

                    # We need to see the enemy ship in order to shoot it
                    if ai.shipCountScreen() == 1:
                        ai.turnToRad(middleDir)
                        ai.setPower(55)
                        ai.thrust()
                        mode = "mission"
                        return

                    Id = lib.nearest_ship_Id(selfX, selfY)

                    # Targets position relative to self
                    x, y = lib.relative_pos(
                        selfX, selfY, ai.shipX(Id), ai.shipY(Id))
                    dirRad = lib.direction(x, y)

                    # We need the to look in the right direction so the
                    # laser do not miss
                    if lib.angleDiff(selfHeading, dirRad) > 0.1:
                        mode = "navigation"

                    else:
                        ai.fireLaser()
                        mode = "completed_task"

                elif "armor" in current_task:
                    mode = "completed_task"
                    return

            # Distance and direction to target
            dist = lib.distance(x, y)
            dirRad = lib.direction(x, y)

            # Save how many items of the desired item we already have
            prevSelfItem = ai.selfItem(desiredItemType)

        # ----------------------------------------------------------------
        # Mission completed
        # ----------------------------------------------------------------

        elif mode == "completed_task":

            current_task = tasks[-1]

            # Adds the completed task to a list send
            if '[Teacherbot]:[Stub] [Stub]' not in current_task:
                if coordinates:
                    prevCoordinates = coordinates.copy()
                    coordinates.clear()

                new_msg = ""
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
            if len(send) == lenTasks:
                for elem in send:
                    ai.talk(elem)
                send.clear()
                tasks.clear()

                mode = "completed_all_tasks"

                for message in range(ai.getMaxMsgs()):
                    ai.removeTalkMsg(message)

            # If you havent completed all the tasks remove the
            # last task in the list and change mode to cords
            else:
                tasks.pop()
                mode = "ready"

        elif mode == "completed_all_tasks":

            compCounter += 1

            # If you recieve a new message from
            # teacherbot change mode to scan
            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0):
                lenTasks = 0
                compCounter = 0
                mode = "ready"

            # Since there is a delay with the messages sometimes,
            # we use a counter to make sure we can pause without
            # having a message to handle
            elif compCounter > 50:
                mode = "pause"

        # ---------------------------------------------------------------------------
        # Navigational modes
        # ---------------------------------------------------------------------------

        elif mode == "navigation":

            # Convert selfTrackingRad and ItemDir to positive radians
            positiveSelfTrackingRad = selfTrackingRad % (2*math.pi)
            positiveItemDir = dirRad % (2*math.pi)

            # Calculate angle difference
            movItemDiff = lib.angleDiff(selfTrackingRad, dirRad)

            # Move towards target
            if selfSpeed < 5 or movItemDiff == math.pi/2:
                angle = dirRad

            # If angle between selfTrackingRad and item direction
            elif movItemDiff > math.pi/2:
                prevTrackRad = selfTrackingRad
                mode = "stop"
                return

            # Uses opposite velocity vector to cancel out unwanted velocity vectors
            else:
                angle = 2*positiveItemDir - positiveSelfTrackingRad

            mode = "mission"

            ai.turnToRad(angle)

            ai.setPower(55)
            ai.thrust()

        elif mode == "stop":

            # The angle difference between our resulting velocity vector
            # in the last tick and our current resulting velocity vector
            angle = lib.angleDiff(prevTrackRad, selfTrackingRad)

            if angle < math.pi/2:
                ai.turnToRad(selfTrackingRad - math.pi)

            if angle > math.pi/2:
                mode = "ready"
                return

            prevTrackRad = selfTrackingRad
            ai.setPower(55)
            ai.thrust()

    except:
        print(traceback.print_exc())


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
