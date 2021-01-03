# --------------------------------------------------------------------------
# Help functions
# --------------------------------------------------------------------------

import sys
import traceback
import math
import libpyAI as ai
from optparse import OptionParser


def direction(x, y):
    """ Returns direction of coordinates. """
    return math.atan2(y, x)


def distance(x, y):
    """ Returns distance to coordinates. """
    return math.hypot(x, y)


def obj_funcs(objType):
    """ Return objekt specified functions. """

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

    return posX, posY, countScreen


def nearest_target_Id(objType, x, y):
    """ Returns id of nearest desired target """

    if objType == "ship":
        return nearest_ship_Id(x, y)

    targetX, targetY, countScreen = obj_funcs(objType)

    prevDist = 10000

    for index in range(countScreen()):
        if objType == "ship":
            relX, relY = relative_pos(x, y, targetX(index), targetY(index))
        dist = distance(relX, relY)

        if dist < prevDist:
            prevDist = dist
            Id = index

    return Id


def nearest_ship_Id(x, y):
    """ Returns id of nearest ship on the screen. """

    prevDist = 10000

    for index in range(ai.shipCountScreen()):
        if ai.ship2serverId(index) != ai.selfId():
            relX, relY = relative_pos(x, y, ai.shipX(index), ai.shipY(index))
            dist = distance(relX, relY)

            if dist < prevDist:
                prevDist = dist
                shipId = index

    return shipId


def nearest_mine_Id(x, y):
    """ Returns id of nearest mine on the screen. """

    prevDist = 10000

    for index in range(ai.mineCountScreen()):
        if ai.mineFriendly(index):
            relX, relY = relative_pos(x, y, ai.mineX(index), ai.mineY(index))
            dist = distance(relX, relY)

            if dist < prevDist:
                prevDist = dist
                mineId = index

    return mineId


def nearest_desired_item_Id(desiredItemType):
    """ Determine nearest desired item, else nearest random item. """

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
    """" Determine pos x and y of specific object. """

    # item position and velocity
    x = ai.itemX(Id)
    y = ai.itemY(Id)
    velX = ai.itemVelX(Id)
    velY = ai.itemVelY(Id)

    # items initial position relative to self
    relX, relY = relative_pos(ai.selfX(), ai.selfY(), x, y)

    # items initial velocity relative to self
    relVelX = velX - ai.selfVelX()
    relVelY = velY - ai.selfVelY()

    # Time of impact, when ship is supposed to reach target
    t = time_of_impact(relX, relY, relVelX, relVelY, speed)

    # Point of impact, where shot is supposed to hit target
    targetX = relX + relVelX*t
    targetY = relY + relVelY*t

    return targetX, targetY


def relative_pos(x, y, targetX, targetY):
    """ Returns relative position to target. """

    relX = targetX - x
    relY = targetY - y

    return relX, relY


def angleDiff(one, two):
    """ Calculates the smallest angle between two angles. """

    a1 = (one - two) % (2*math.pi)
    a2 = (two - one) % (2*math.pi)
    return min(a1, a2)


def brake(dist, accForce=55, decForce=55):
    """ Determine when to brake. """
    try:
        m = ai.selfMass() + 5
        v = ai.selfSpeed()

        futV = v + accForce*2 / m
        futDist = dist - v*2 - accForce*4 / (2 * m)

        futDecForce = m * futV**2 / (2 * futDist)

        if futDist < 20:
            return True

        elif futDecForce >= decForce:
            return True
        return False
    
    except RuntimeError:
        pass


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

def block_to_pixel(x, y):
    """ Transform a block coordinate to a pixel coordinate., """
    blockSize = ai.blockSize()
    pixelX = x*blockSize + blockSize/2
    pixely = y*blockSize + blockSize/2
    return (pixelX, pixely)


def pixel_to_block(x, y):
    """ Transform a pixel coordinate to a block coordinate. """
    blockSize = ai.blockSize()
    blockX = x//blockSize
    blockY = y//blockSize
    return (blockX, blockY)