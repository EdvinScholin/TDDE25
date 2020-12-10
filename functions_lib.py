# --------------------------------------------------------------------------
# Help functions
# --------------------------------------------------------------------------

import sys
import traceback
import math
import libpyAI as ai
from optparse import OptionParser


def direction(x, y):
    return math.atan2(y, x)


def distance(x, y):
    return math.hypot(x, y)


def obj_funcs(objType):
    """Return objekt specified functions"""

    # Kan lägga till för varje objekt typ

    if objType == "asteroid":
        posX = ai.asteroidX
        posY = ai.asteroidY
        countScreen = ai.asteroidCountScreen

    elif objType == "mine":
        posX = ai.mineX
        posY = ai.mineY
        countScreen = ai.mineCountScreen

    elif objType == "ship":
        posX = ai.shipX
        posY = ai.shipY
        countScreen = ai.shipCountScreen

    '''
    elif objType == "laser":
        posX = ai.laserX
        posY = ai.laserY
    '''

    return posX, posY, countScreen


def nearest_target_Id(objType):

    posX, posY, countScreen = obj_funcs(objType)
    prevDist = 10000

    for index in range(countScreen()):
        dist = math.hypot(posX(index), posY(index))

        if dist < prevDist:
            prevDist = dist
            Id = index

    return Id


def nearest_ship_Id(objType):

    posX, posY, countScreen = obj_funcs(objType)

    for index in range(countScreen()):
        if ai.ship2serverId(index) != ai.selfId():
            Id = index

    return Id


def nearest_desired_item_Id(desiredItemType):
    """Determine nearest desired item else nearest random item"""

    # Take the closest item
    prevDist = 10000
    prevDesiredDist = 10000
    desiredCount = 0

    for index in range(ai.itemCountScreen()):

        dist = ai.itemDist(index)

        if ai.itemType(index) == desiredItemType:
            desiredCount += 1

            if dist < prevDesiredDist:
                prevDesiredDist = dist
                Id = index

        else:
            if dist < prevDist:
                prevDist = dist
                restId = index

    # If there are none of the desired type, we want to take the closest item
    if desiredCount == 0:
        Id = restId

    return Id


def target_future_pos(Id, speed):
    """"Determine pos x and y of specific objekt"""

    # item position and velocity
    x = ai.itemX(Id)
    y = ai.itemY(Id)
    velX = ai.itemVelX(Id)
    velY = ai.itemVelY(Id)

    # items initial position relative to self
    relX, relY = relative_pos(x, y)

    # items initial velocity relative to self
    relVelX = velX - ai.selfVelX()
    relVelY = velY - ai.selfVelY()

    # Time of impact, when ship is supposed to reach target
    t = time_of_impact(relX, relY, relVelX, relVelY, speed)

    # Point of impact, where shot is supposed to hit target
    targetX = relX + relVelX*t
    targetY = relY + relVelY*t

    return targetX, targetY


def relative_pos(xCord, yCord):
    """calculate position"""
    x = xCord - ai.selfX()
    y = yCord - ai.selfY()

    return x, y


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

    if dist <= 10:
        return True

    elif futDecForce >= decForce:
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
