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
prevItemDir = 0
direction = 0
itemDir = 0
power = 5
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
        global mode
        global prevTrackRad
        global prevItemDir
        global direction
        global itemDir
        global power

        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
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

        selfHeading = ai.selfHeadingRad()
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here
        itemCountScreen = ai.itemCountScreen()
        previousItemDist = 1000

        for index in range(itemCountScreen):
            itemDist = ai.itemDist(index)
            if itemDist < previousItemDist:
                previousItemDist = itemDist
                itemId = index

        # Calcualtes which direction the middle is
        middleDisX = ai.radarWidth()/2 - ai.selfRadarX()
        middleDisY = ai.radarHeight()/2 - ai.selfRadarY()
        middleDir = math.atan2(middleDisY, middleDisX)

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)

        selfHeading = ai.selfHeadingRad()

        wallDistance = ai.wallFeelerRad(10000, ai.selfTrackingRad())

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
            distance = math.sqrt((aimAtX**2 + aimAtY**2))

            # Direction of aimpoint
            itemDir = math.atan2(aimAtY, aimAtX)

        print("tick count:", tickCount, "mode", mode)

        # Move away from wall

        try:
            power = selfSpeed**2 * (ai.selfMass()+5) / (2*wallDistance-40)
        except ZeroDivisionError:
            power = 55

        if 30 <= power <= 55:
            if wallDistance < 50:
                power = 55
            mode = "stop"

        if mode == "ready":

            # ai.setPower(55)
            # ai.thrust()

            # -----------------------------------------------------
            # Det är adjust som är fel.
            # -----------------------------------------------------

            # -----------------------------------------------------
            # Om man flyttar koden nedan utanför if satsen kanske det funkar

            # -----------------------------------------------------

            """
                if ai.wallFeelerRad(300, ai.selfTrackingRad()) > 0:

                mode = "stop"


                print(ai.wallFeelerRad(300, ai.selfTrackingRad()))
                print(wall_perpendicular())
                wallPerp = wall_perpendicular()
                perpendicularVel = selfSpeed * \
                    math.cos(angleDiff(ai.selfTrackingRad(), wallPerp))


                ai.setPower(15)

                if ai.wallFeelerRad(50, wallPerp) > 0:
                    ai.setPower(5)
                    mode = "aim"

                elif ai.wallFeelerRad(150, wallPerp) > 0:
                    ai.setPower(10)
                    mode = "aim"

                # Behöver mer statements
                if perpendicularVel > 10:
                    ai.turnToRad(wall_perpendicular() - math.pi)
                    power = 55
                    mode = "stop"
            """

            elif itemCountScreen > 0:
                ai.setPower(45)
                mode = "aim"

            else:
                ai.turnToRad(middleDir)

                if angleDiff(selfHeading, middleDir) < 0.1:
                    if selfSpeed < 8:
                        ai.setPower(12)
                    else:
                        ai.setPower(5)
                    ai.thrust()

                elif angleDiff(selfHeading, middleDir) < 0.5:
                    power = 55
                    mode = "stop"

        elif mode == "aim":
            if itemCountScreen == 0:
                mode == "ready"
                return

            # Turns to target direction
            ai.turnToRad(itemDir)

            # Thrust if we are in a sufficient right direction
            if angleDiff(selfHeading, itemDir) < 0.05:

                # Stops accelerating
                '''
                if selfSpeed < 7:
                    ai.setPower(30)
                else:
                    ai.setPower(15)

                if selfSpeed < 10:
                    ai.setPower(45)
                '''
                ai.thrust()
                mode = "ready"

            elif angleDiff(ai.selfTrackingRad(), itemDir) > 0.1:
                mode = "adjust"

        elif mode == "stop":

            if angleDiff(prevTrackRad, ai.selfTrackingRad()) < 0.1:
                ai.turnToRad(ai.selfTrackingRad() - math.pi)

            selfHeading = ai.selfHeadingRad()

            angle = angleDiff(ai.selfTrackingRad(), selfHeading)
            prevTrackRad = ai.selfTrackingRad()

            if angle < 0.1:
                mode = "ready"

            # power = selfSpeed**2 * (ai.selfMass()+5) / ((ai.wallFeelerRad(300, ai.selfTrackingRad())))

            # print(selfSpeed)

            if wallDistance > 50:
                ai.setPower(power)
            else:
                ai.setPower(55)

            # print("angle: ", angle)
            # print("distance: ", ai.wallFeelerRad(300, ai.selfTrackingRad()))

            # else:
            #    print("djkajdl")
            #    mode = "ready"
            #    return

            ai.thrust()

        elif mode == "adjust":
            # kolla på rörelseriktningen och målets riktning.
            # Ta ut riktningen mitt mellan och thrusta.
            movItemDiff = angleDiff(ai.selfTrackingRad(), itemDir)
            selfTrackRad = ai.selfTrackingRad() % (2*math.pi)
            absItemDir = itemDir % (2*math.pi)

            relVelToItem = relativeVel(
                selfSpeed, ai.selfTrackingRad(), itemDir)

            if movItemDiff < math.pi/2:
                adjustAngle = 2*absItemDir - selfTrackRad

            elif 3*math.pi/4 > movItemDiff >= math.pi/2:
                adjustAngle = (3*absItemDir - selfTrackRad)/2

            elif movItemDiff == math.pi:
                power = 55
                mode = "stop"
                return

            else:
                adjustAngle = absItemDir

            ai.turnToRad(adjustAngle)
            selfHeading = ai.selfHeadingRad()

            ai.thrust()

            if angleDiff(selfHeading, itemDir) < 0.05:
                mode = "ready"
            else:
                mode = "adjust"

    except:
        print(traceback.print_exc())


def angleDiff(one, two):
    """Calculates the smallest angle between two angles"""

    a1 = (one - two) % (2*math.pi)
    a2 = (two - one) % (2*math.pi)
    return min(a1, a2)


def wall_perpendicular():
    """
    a = selfTrackRad
    eps = very small angel #Smaller --> more exact
    d = distance to wall in the direction of self velocity/ self tracking radians
    v = ---------------- || ---------------- v + eps
    h = ---------------- || ---------------- v - eps
    """

    eps = math.pi/100
    a = ai.selfTrackingRad()
    d = ai.wallFeelerRad(100, a)
    v = ai.wallFeelerRad(100, a + eps)
    h = ai.wallFeelerRad(100, a - eps)

    if v >= h:
        s = h
    else:
        s = v

    x = s * math.cos(eps)
    y = s * math.sin(eps)
    z = d - x

    alpha = math.atan(y/z)

    gamma = math.pi/2 - alpha

    if v > h:
        new_a = a - gamma
    else:
        new_a = a + gamma

    return new_a


def relativeVel(selfVel, selfVelDir, itemPosDir):
    """self relativa hastighet till items framtida position"""

    a = selfVelDir % (2*math.pi)
    b = itemPosDir % (2*math.pi)

    if a > b:
        v = a - b + math.pi/2
    elif b > a:
        v = b - a + math.pi/2
    else:
        v = 0

    relVel = selfVel * math.cos(v)
    return relVel


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

# print("hfjakhflj: ", time_of_impact(3,4,0,0,4))


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
