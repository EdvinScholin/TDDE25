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

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)

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

            # Direction of aimpoint
            itemDir = math.atan2(aimAtY, aimAtX)

        print("tick count:", tickCount, "mode", mode)

        # Move away from wall

        try:
            power = selfSpeed**2 * (ai.selfMass()+5) / (2*wallDistance-40)
        except ZeroDivisionError:
            power = 55

        if 30 <= power <= 55:
            if wallDistance < 80:
                power = 55
            mode = "stop"

        if mode == "ready":

            if itemCountScreen > 0:
                ai.setPower(45)
                if wallDistance < 20:
                    ai.setPower(15)
                mode = "aim"

            else:
                ai.turnToRad(middleDir)

                if angleDiff(selfHeading, middleDir) < 0.1:
                    if selfSpeed < 8:
                        ai.setPower(12)
                    else:
                        ai.setPower(5)
                    ai.thrust()

                '''
                elif angleDiff(selfHeading, middleDir) < 0.5:
                    power = 55
                    mode = "stop"
                '''

        elif mode == "aim":
            if itemCountScreen == 0:
                mode == "ready"
                return

            movItemDiff = angleDiff(ai.selfTrackingRad(), itemDir)
            selfTrackRad = ai.selfTrackingRad() % (2*math.pi)
            absItemDir = itemDir % (2*math.pi)

            if movItemDiff < math.pi/2:
                angle = 2*absItemDir - selfTrackRad

            elif selfSpeed == 0:
                angle = itemDir

            else:
                mode = "stop"
                return

            # Turns to target direction
            ai.turnToRad(angle)
            ai.thrust()

            '''
            # Thrust if we are in a sufficient right direction
            if angleDiff(selfHeading, itemDir) < 0.05:
                if selfSpeed < 50:
                    ai.thrust()
                mode = "ready"

            elif angleDiff(ai.selfTrackingRad(), itemDir) > 0.5:
                mode = "adjust"

            else:
                mode = "ready"
            '''

        elif mode == "stop":

            angle = angleDiff(ai.selfTrackingRad(), selfHeading) != math.pi:
                ai.turnToRad(ai.selfTrackingRad() - math.pi)

            '''
            if angleDiff(prevTrackRad, ai.selfTrackingRad()) < 0.1:
                ai.turnToRad(ai.selfTrackingRad() - math.pi)
            '''

            print(angle)

            if angleDiff(prevTrackRad, ai.selfTrackingRad()) > 1:
                mode = "ready"

            if 5 < power < 55:
                ai.setPower(power)
            else:
                ai.setPower(55)

            prevTrackRad = ai.selfTrackingRad()

            ai.thrust()

        '''
        elif mode == "adjust":
            # kolla på rörelseriktningen och målets riktning.
            # Ta ut riktningen mitt mellan och thrusta.
            movItemDiff = angleDiff(ai.selfTrackingRad(), itemDir)
            selfTrackRad = ai.selfTrackingRad() % (2*math.pi)
            absItemDir = itemDir % (2*math.pi)

            if movItemDiff < math.pi/2:
                print("1")
                adjustAngle = 2*absItemDir - selfTrackRad

            else:
                adjustAngle = ai.selfTrackingRad() - math.pi

            
            elif 3*math.pi/4 > movItemDiff >= math.pi/2:
                print("4")
                adjustAngle = a
            else:
                print("3")
                power = 55
                mode = "stop"
                return

            
            elif 3*math.pi/4 > movItemDiff >= math.pi/2:
                print("2")
                #adjustAngle = (3*absItemDir - selfTrackRad)/2

            elif movItemDiff == math.pi:
                print("3")
                power = 55
                mode = "stop"
                return

            else:
                print("4")
                adjustAngle = absItemDir

            

            ai.turnToRad(adjustAngle)
            selfHeading = ai.selfHeadingRad()

            ai.thrust()

            if angleDiff(selfHeading, itemDir) < 0.05 or selfSpeed < 1:
                mode = "ready"
            '''

    except:
        print(traceback.print_exc())


def angleDiff(one, two):
    """Calculates the smallest angle between two angles"""

    a1 = (one - two) % (2*math.pi)
    a2 = (two - one) % (2*math.pi)
    return min(a1, a2)


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
