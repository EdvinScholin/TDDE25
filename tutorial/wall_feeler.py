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
itemId = -1
itemDir = 0

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
        global itemId
        global itemDir

        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
            tickCount = 0
            mode = "ready"
            return

        tickCount += 1

        # Sets the first item in itemCount as itemId which the ship will
        # focus to aquire.

        #
        # Read some "sensors" into local variables, to avoid excessive calls to the API
        # and improve readability.
        #

        selfX = ai.selfX()
        selfY = ai.selfY()
        selfVelX = ai.selfVelX()
        selfVelY = ai.selfVelY()
        selfSpeed = ai.selfSpeed()

        # Calcualtes which direction the middle is 
        middleDisX = ai.radarWidth()/2 - ai.selfRadarX()                  
        middleDisY = ai.radarHeight()/2 - ai.selfRadarY()                 
        middleDir = math.atan2(middleDisY, middleDisX)

        itemCount = ai.itemCountScreen()

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)                 

        selfHeading = ai.selfHeadingRad() 

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode", mode)

        if mode == "ready":
            mode = "aim"

        if mode == "aim":
            
            if itemCount == 0:
                
                ai.turnToRad(middleDir)
                
                # Thrust if we are in a sufficient right direction
                if angleDiff(selfHeading, middleDir) < 0.1:                    
                    ai.setPower(30)
                    ai.thrust()
            
                # Stop if we are in a sufficient wrong direction
                elif angleDiff(ai.selfTrackingRad(), middleDir) > 0.8 and selfSpeed > 3:
                    if (0 < ai.wallFeelerRad(1000, ai.selfTrackingRad()) > 100):
                        mode = "stop"
                    
            else:
            
                # Excecute when an item is visible
                for item in range(itemCount):
                    itemId = item
                
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

                # Time of impact, when ship is supposed to hit item
                try:
                    t = time_of_impact(relX, relY, relVelX, relVelY, selfSpeed)
                except ZeroDivisionError:
                    pass
                
                if ai.itemSpeed(itemId) > 0:
                
                    # Point of impact, where ship is supposed to hit item
                    aimAtX = relX + relVelX*t
                    aimAtY = relY + relVelY*t

                    # Direction of aimpoint
                    itemDir = math.atan2(aimAtY, aimAtX)

                    # Turns to item direction
                    ai.turnToRad(itemDir)

                    # Thrust if we are in a sufficient right direction
                    if angleDiff(selfHeading, itemDir) < 0.05:

                        if (0 < ai.wallFeelerRad(1000, ai.selfTrackingRad()) > 100):
                   
                            ai.setPower(35)
                            ai.thrust()
                            mode = "aim"

                    elif angleDiff(ai.selfTrackingRad(), itemDir) > 0.1:
                        mode = "adjust"
                
                else:
                    # If item has no velocity 
                    itemStopped = math.atan2(relY, relX)
                    ai.turnToRad(itemStopped)

                    # Thrust if we are in a sufficient right direction
                    if angleDiff(selfHeading, itemStopped) < 0.1:
                        ai.setPower(30)
                        ai.thrust()
            
                    # Stop if we are in a sufficient wrong direction
                    if angleDiff(ai.selfTrackingRad(), itemStopped) > 0.8 and selfSpeed > 3:
                        if (0 < ai.wallFeelerRad(1000, ai.selfTrackingRad()) > 100):
                            mode = "stop"
       
            # Different distances to wall for different speeds
            if (0 < ai.wallFeelerRad(1000, ai.selfTrackingRad()) < 100):
                mode = "closeToWall"
            
            if selfSpeed > 12:
                if (0 < ai.wallFeelerRad(1000, ai.selfTrackingRad()) < 250):
                    mode = "closeToWall" 
            
            if selfSpeed > 18:
                if (0 < ai.wallFeelerRad(1000, ai.selfTrackingRad()) < 350):
                    mode = "closeToWall"
            
            if selfSpeed > 24:
                if (0 < ai.wallFeelerRad(1000, ai.selfTrackingRad()) < 450):
                    mode = "closeToWall"
        
        elif mode == "closeToWall":
            
            prevTrackRad = ai.selfTrackingRad()
            ai.turnToRad(ai.selfTrackingRad() - math.pi)
            angle = angleDiff(ai.selfTrackingRad(), selfHeading)
            
            if selfSpeed < 3:
                mode = "aim"
            
            ai.setPower(55)
            ai.thrust()
        
        elif mode == "stop":
            if selfSpeed > 1:
                ai.turnToRad(ai.selfTrackingRad() - math.pi)

            angle = angleDiff(ai.selfTrackingRad(), selfHeading)

            if angle < 0.5:
                mode = "aim"

            ai.setPower(45)
            ai.thrust()

            if prevSelfItem < ai.selfItem(selectItemType):
                if selfSpeed < 3:
                    mode = "done"
                else:
                    mode = "stop"
        
        elif mode == "adjust":
            
            # kolla på rörelseriktningen och målets riktning.
            # Ta ut riktningen mitt mellan och thrusta.
            movItemDiff = angleDiff(ai.selfTrackingRad(), itemDir)
            selfTrackRad = ai.selfTrackingRad() % (2*math.pi)
            absItemDir = itemDir % (2*math.pi)
            
            if movItemDiff < math.pi/2:
                adjustAngle = 2*absItemDir - selfTrackRad
            
            elif 3*math.pi/4 > movItemDiff >= math.pi/2:
                adjustAngle = (3*absItemDir - selfTrackRad)/2
            
            elif movItemDiff == math.pi:
                mode = "stop"
                return
            
            else:    
                adjustAngle = absItemDir
            
            ai.turnToRad(adjustAngle)
            selfHeading = ai.selfHeadingRad()

            ai.setPower(45)
            ai.thrust()

            if angleDiff(selfHeading, itemDir) < 0.05:
                mode = "aim"
            else:
                mode = "adjust"

    except:
        print(traceback.print_exc())


def angleDiff(one, two):
    """Calculates the smallest angle between two angles"""

    a1 = (one - two) % (2*math.pi)
    a2 = (two - one) % (2*math.pi)
    return min(a1, a2)

def time_of_impact(px, py, vx, vy, s):
    """
    Determine the time of impact, when ship hits moving target
    Parameters:
        px, py = initial target position in x,y relative to ship
        vx, vy = initial target velocity in x,y relative to ship
        s = initial ship speed
        t = time to impact, in our case ticks
    """

    a = s * s - (vx * vx + vy * vy)
    b = px * vx + py * vy
    c = px * px + py * py

    d = b*b + a*c

    t = 0

    if d >= 0:
        t = (b + math.sqrt(d)) / a
        if t < 0:
            t = 0

    return t

#
# Parse the command line arguments
#
parser = OptionParser()

parser.add_option ("-p", "--port", action="store", type="int", 
                   dest="port", default=15348, 
                   help="The port number. Used to avoid port collisions when" 
                   " connecting to the server.")

(options, args) = parser.parse_args()

name = "Stub"

#
# Start the AI
#

ai.start(tick,["-name", name, 
               "-join",
               "-turnSpeed", "64",
               "-turnResistance", "0",
               "-port", str(options.port)])
