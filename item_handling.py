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
        previousItemDist = 1000

        
        for index in range(itemCountScreen):
            itemDist = ai.itemDist(index)
            if itemDist < previousItemDist and :
                previousItemDist = itemDist
                itemId = index
        

        # Calcualtes which direction the middle is
        middleDisX = ai.radarWidth()/2 - ai.selfRadarX()
        middleDisY = ai.radarHeight()/2 - ai.selfRadarY()
        middleDir = math.atan2(middleDisY, middleDisX)

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)

        selfHeading = ai.selfHeadingRad()

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

        if mode == "ready":
            if itemCountScreen > 0:
                mode = "aim"
            '''
            else:
                ai.turnToRad(middleDir)
                
                if angleDiff(selfHeading, middleDir) < 0.1: 
                    if selfSpeed < 8:
                        ai.setPower(12)
                    else:
                        ai.setPower(5)
                    mode = "thrust"
                
                elif angleDiff(selfHeading, middleDir) < 0.5:
                    mode = "stop"
            '''
        elif mode == "aim":
            if itemCountScreen == 0:
                mode == "ready"
                return

            # Turns to target direction
            ai.turnToRad(itemDir)


            #print(angleDiff(selfHeading, itemDir))
            # -------------------------------------------------------
            # från mode adjust till aim så kommer alltid selfHeading
            # ha den gamla riktningen vilket leder till att mode
            # adjust kallas igen, alltså en ossilation.
            # -------------------------------------------------------

            
            # Thrust if we are in a sufficient right direction
            if angleDiff(ai.selfTrackingRad(), itemDir) < 0.05:

                # Stops accelerating

                if selfSpeed < 7:
                    ai.setPower(30)
                else:
                    ai.setPower(15)

                if selfSpeed < 10:
                    ai.setPower(45)
                    mode = "thrust"

            # if angleDiff(ai.selfTrackingRad(), itemDir) > 0.5:
            else:
                mode = "adjust"
            
            # Stop if we are in a sufficient wrong direction
            # if angleDiff(ai.selfTrackingRad(), itemDir) > 0.8:
            #    mode = "adjust"
            '''
            if (-1 < ai.wallFeelerRad(1000, ai.selfTrackingRad()) < 200 or
                -1 < ai.wallFeelerRad(-1000, ai.selfTrackingRad()) < 200):
                print("kallar på stop")
                direction += math.pi
                
                mode = "stop"
            '''

            # print(selfSpeed)
            #print(ai.selfTrackingRad(), itemDir, angleDiff(ai.selfTrackingRad(), itemDir))
            #print(angleDiff(prevItemDir, itemDir))

        elif mode == "stop":
            print("stop")
            ai.turnToRad(ai.selfTrackingRad() - math.pi)
            angle = angleDiff(ai.selfTrackingRad(), selfHeading)

            if angle < 0.5:
                mode = "ready"

            ai.setPower(30)
            ai.thrust()

        elif mode == "adjust":
            # kolla på rörelseriktningen och målets riktning.
            # Ta ut riktningen mitt mellan och thrusta.
            movItemDiff = angleDiff(ai.selfTrackingRad(), itemDir)
            selfTrackRad = ai.selfTrackingRad() % (2*math.pi)
            absItemDir = itemDir % (2*math.pi)

            relVelToItem = relativeVel(selfSpeed, ai.selfTrackingRad(), itemDir)

            if selfTrackRad > absItemDir:
                adjustAngle = absItemDir + 3*movItemDiff/2
            else:
                adjustAngle = selfTrackRad + 3*movItemDiff/2

            ai.turnToRad(adjustAngle)
            
            if relVelToItem < 5:
                ai.setPower(10)
            elif relVelToItem < 10:
                ai.setPower(20)
            elif relVelToItem < 15:
                ai.setPower(30)
            
            if selfSpeed > 20:
                mode = "stop"
                return

            ai.thrust()
            print(adjustAngle)
            print(movItemDiff)
            if movItemDiff < 0.1:
                mode = "ready"
            else:
                mode = "adjust"

        elif mode == "thrust":
            mode = "ready"
            ai.thrust()

    except:
        print(traceback.print_exc())


def angleDiff(one, two):
    """Calculates the smallest angle between two angles"""

    a1 = (one - two) % (2*math.pi)
    a2 = (two - one) % (2*math.pi)
    return min(a1, a2)


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
