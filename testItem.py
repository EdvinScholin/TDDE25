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
        selfMass = ai.selfMass()

        selfHeading = ai.selfHeadingRad()
        # 0-2pi, 0 in x direction, positive toward y

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)

        wallDistance = ai.wallFeelerRad(1000, ai.selfTrackingRad())

        # Add more sensors readings here
        itemCountScreen = ai.itemCountScreen()
        previousItemDist = 1000000

        for index in range(itemCountScreen):
            itemDist = ai.itemDist(index)
            if itemDist < previousItemDist:
                previousItemDist = itemDist
                itemId = index

        # Calcualtes which direction the middle is
        middleDisX = ai.radarWidth()/2 - ai.selfRadarX()
        middleDisY = ai.radarHeight()/2 - ai.selfRadarY()
        middleDir = math.atan2(middleDisY, middleDisX)

        if itemCountScreen > 0:
            # item position and velocity
            itemX = ai.itemX(itemId)
            itemY = ai.itemY(itemId)
            itemVelX = ai.itemVelX(itemId)
            itemVelY = ai.itemVelY(itemId)

            # items initial position relative to self
            relX = itemX - selfX
            relY = itemY - selfY

            # items initial velocity relative to self
            relVelX = itemVelX - selfVelX
            relVelY = itemVelY - selfVelY

            # Time of impact, when ship is supposed to reach target
            t = time_of_impact(relX, relY, relVelX, relVelY, selfSpeed)

            # Point of impact, where shot is supposed to hit target
            aimAtX = relX + relVelX*t
            aimAtY = relY + relVelY*t

            # Direction of aimpoint
            itemDist = math.sqrt(aimAtX**2 + aimAtY**2)
            itemDir = math.atan2(aimAtY, aimAtX)

        if mode == "ready":

            if abs(wallDistance) < 1:
                p = 55
            else:
                p = selfSpeed**2 * (selfMass+5) / wallDistance

            print("wallDistance: ", wallDistance)

            print("power: ", p)

            if 40 <= p:
                mode = "stop"
                prevTrackRad = ai.selfTrackingRad()

                '''
                if stop_at_point(wallDistance, 55):
                prevTrackRad = ai.selfTrackingRad()
                power = 55
                mode = "stop"
                return
                '''

            elif itemCountScreen > 0:
                if selfSpeed < 20:
                    ai.setPower(55)
                mode = "aim"

            else:
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
            if itemCountScreen == 0:
                mode = "ready"
                return

            selfTrackRad = ai.selfTrackingRad() % (2*math.pi)
            absItemDir = itemDir % (2*math.pi)
            movItemDiff = angleDiff(
                ai.selfTrackingRad(), itemDir)

            # if stop_at_point(itemDist + 50):
            if brake(itemDist):
                # elif round(itemDist, 1) == 0 or movItemDiff > math.pi/2:
                prevTrackRad = ai.selfTrackingRad()
                mode = "stop"
                return

            if selfSpeed < 5 or movItemDiff == math.pi/2:
                angle = itemDir

            elif movItemDiff > math.pi/2:
                # ai.setMaxTurnRad(math.pi)
                prevTrackRad = ai.selfTrackingRad()
                mode = "stop"
                print("movItemDiff: ", movItemDiff)
                return

            else:
                angle = 2*absItemDir - selfTrackRad

            mode = "ready"

            # Turns to target direction
            ai.turnToRad(angle)
            ai.thrust()

        print("tick count:", tickCount, "mode", mode)

        if mode == "ready":
            pass

    except:
        print(traceback.print_exc())


def angleDiff(one, two):
    """Calculates the smallest angle between two angles"""

    a1 = (one - two) % (2*math.pi)
    a2 = (two - one) % (2*math.pi)
    return min(a1, a2)


def stop_at_point(objDist):
    """determine when ship need to stop"""

    p = 55
    v0 = ai.selfSpeed()
    m = ai.selfMass() + 5
    a = p / m
    a2 = p / m
    s = objDist

    maxV0 = math.sqrt(2*a*s)
    print("Max Velocity: ", maxV0)
    print("Velocity: ", v0)

    futV = v0 + a2/2
    futS = s - futV
    futMaxV0 = math.sqrt(2*a*futS)
    print("futMaxV0: ", futMaxV0)

    if futMaxV0 <= futV:
        return True


def brake(dist):
    """Determine when to brake"""

    m = ai.selfMass()
    v = ai.selfVel()
    p = 55

    ek = m * v**2 / 2
    ep = p * dist

    if not round(ek - ep):
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

    return False


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
