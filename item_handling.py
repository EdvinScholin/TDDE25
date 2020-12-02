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
prevTrackRad = 0
mode = "ready"

# add more if needed

itemDict = {"fuel": 0, "wideangle": 1, "rearshot": 2, "afterburner": 3, "cloak": 4,
            "sensor": 5, "transporter": 6, "tank": 7, "mine": 8, "missile": 9, "ecm": 10,
            "laser": 11, "emergencythrust": 12, "tractorbeam": 13, "autopilot": 14,
            "emergencyshield": 15, "itemdeflector": 16, "hyperjump": 17, "phasing": 18,
            "mirror": 19, "armor": 20}


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

        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():

            print("dead")
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

        # 0-2pi, 0 in x direction, positive toward y

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)

        wallDistance = ai.wallFeelerRad(1000, ai.selfTrackingRad())

        # Calcualtes which direction the middle is
        middleDisX = ai.radarWidth()/2 - ai.selfRadarX()
        middleDisY = ai.radarHeight()/2 - ai.selfRadarY()
        middleDir = math.atan2(middleDisY, middleDisX)

        # Lägg till if-sats senare, i detta fall för items
        countScreen = ai.itemCountScreen
        speed = selfSpeed

        # Position in which target will be in when ship/bullet arives
        aimAtX, aimAtY = estimated_target_pos(countScreen, speed)

        # Direction of aimpoint
        dist = math.sqrt(aimAtX**2 + aimAtY**2)
        dirRad = math.atan2(aimAtY, aimAtX)

        if mode == "ready":

            # We want to brake the ship if power p is to high
            if brake(wallDistance + 50) and wallDistance != -1:
                prevTrackRad = ai.selfTrackingRad()
                mode = "stop"

            elif countScreen > 0:  # Aim if any targets are detected
                if selfSpeed < 20:
                    ai.setPower(55)
                mode = "aim"

            else:  # Move towards map middle when no targets are detected
                ai.turnToRad(middleDir)
                ai.setPower(55)
                ai.thrust()

        elif mode == "stop":

            angle = angleDiff(prevTrackRad, ai.selfTrackingRad())

            if angle < math.pi/2:
                ai.turnToRad(ai.selfTrackingRad() - math.pi)

            if angle > math.pi/2:
                mode = "ready"
                return

            ai.setPower(55)
            ai.thrust()

        elif mode == "aim":
            if countScreen == 0:
                mode = "ready"
                return

            # Convert selfTrackingRad and ItemDir to positive radians
            selfTrackRad = ai.selfTrackingRad() % (2*math.pi)
            absItemDir = dirRad % (2*math.pi)

            # Calculate angle difference
            movItemDiff = angleDiff(
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
                prevTrackRad = ai.selfTrackingRad()
                mode = "stop"
                return

            else:  # Uses opposite velocity vektor to cancel out unwanted velocity vektors
                angle = 2*absItemDir - selfTrackRad

            mode = "ready"

            ai.turnToRad(angle)
            ai.thrust()

        ############################## Funktionsanrop ##############################

        # Navigation

        ############################################################################

        print("tick count:", tickCount, "mode", mode)

    except:
        print(traceback.print_exc())

# --------------------------------------------------------------------------
# Help functions
# --------------------------------------------------------------------------


def estimated_target_pos(countScreen, speed):
    """Determine pos x and y of specific objekt"""

    previousDist = 1000000

    for index in range(countScreenFunc()):
        dist = ai.itemDist(index)
        if dist < previousDist:
            previousDist = dist
            Id = index

    if countScreen > 0:
        # item position and velocity
        x = ai.itemX(Id)
        y = ai.itemY(Id)
        velX = ai.itemVelX(Id)
        velY = ai.itemVelY(Id)

        # items initial position relative to self
        relX = x - ai.selfX()
        relY = y - ai.selfY()

        # items initial velocity relative to self
        relVelX = velX - ai.selfVelX()
        relVelY = velY - ai.selfVelY()

        # Time of impact, when ship is supposed to reach target
        t = time_of_impact(relX, relY, relVelX, relVelY, speed)

        # Point of impact, where shot is supposed to hit target
        targetX = relX + relVelX*t
        targetY = relY + relVelY*t

        return targetX, targetY


def angleDiff(one, two):
    """Calculates the smallest angle between two angles"""

    a1 = (one - two) % (2*math.pi)
    a2 = (two - one) % (2*math.pi)
    return min(a1, a2)


def brake(dist, accForce=55, decForce=55):
    """Determine when to brake"""

    m = ai.selfMass() + 5
    v = ai.selfSpeed()

    futV = v + accForce / m
    futDist = dist - v - accForce / (2 * m)

    futDecForce = m * futV**2 / (2 * futDist)

    if futDecForce >= decForce:
        return True
    return False


def time_of_impact(px, py, vx, vy, s):
    """
    Determine the time of impact, when bullet hits moving target
    Parameters:
        px, py = initial target position in x,y relative to shooter
        vx, vy = initial target velocity in x,y relative to shooter
        s = initial bullet speed
        t = time to impact, in our case ticks
    """

    a = s * s - (vx * vx + vy * vy)
    b = px * vx + py * vy
    c = px * px + py * py

    d = b*b + a*c

    t = 0

    if d >= 0:
        try:
            t = (b + math.sqrt(d)) / a
        except ZeroDivisionError:
            t = (b + math.sqrt(d))
        if t < 0:
            t = 0

    return t


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
