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
        itemCount = ai.itemCountScreen()
        for item in range(itemCount):
                itemId = item

        #
        # Read some "sensors" into local variables, to avoid excessive calls to the API
        # and improve readability.
        #

        selfX = ai.selfX()
        selfY = ai.selfY()
        selfVelX = ai.selfVelX()
        selfVelY = ai.selfVelY()
        selfSpeed = ai.selfSpeed()

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)                 

        # Items X and Y coordinate.
        itemX = ai.itemX(itemId)
        itemY = ai.itemY(itemId)
       
        xDir = itemX - selfX                  
        yDir = itemY - selfY

        itemDist = ai.itemDist(itemId) # Calcualtes the distance to item
        itemDir = math.atan2(yDir, xDir) # Calculates direction in radians to item

        itemVelX = ai.itemVelX(itemId)
        itemVelY = ai.itemVelY(itemId)

        selfHeading = ai.selfHeadingRad() 
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode", mode)
        
        if mode != "stop":
            mode = "travel"
        
        if mode == "travel":
            """ai.setPower(5)
            ai.thrust()
            print(time_of_impact)
            # Determine item velocity
            itemVel = math.hypot(itemVelX, itemVelX)
            
            # Time of impact, when ship hits item
            timeOfImpact = time_of_impact(itemX, itemY, itemVelX, itemVelY, selfSpeed)

            #Vinkel
            itemTravelDistance = itemVel * time_of_impact # Distance traveled to impact point
            itemDistance = selfSpeed * time_of_impact # Distance to the impact point

            v = math.atan2(itemTravelDistance, itemDistance)
            
            """"""radarShotDist = radarShotVel * timeOfImpact
            radarAsteroidDist = radarAsteroidVel * timeOfImpact
            
            v = math.acos((targetDistance**2 + radarShotDist**2 - radarAsteroidDist**2)
                    / (2 * targetDistance * radarShotDist * radarAsteroidDist)) #får DivisionByZeroError
            """"""

            # Determine asteroids direction when shot are supposed to hit target
            itemDir = v + math.atan2(itemY, itemX)"""
            
            #if ai.wallFeelerRad(100, ai.selfTrackRad()) == -1: 
            ai.turnToRad(itemDir) # Turns ship in direction of item
            ai.setPower(5)
            ai.thrust()

            if 0 < ai.wallFeelerRad(70, ai.selfTrackingRad()) < 70: #or itemDist < 90:
                ai.turnToRad(ai.selfTrackingRad() - math.pi) # Rotates the ship 180 degrees
                mode = "stop" 
            if not ai.selfTrackingRad() == selfHeading:
                ai.turnToRad(itemDir)
                ai.thrust()
                
            
        
        if mode == "stop":   
            #ai.turnToRad(ai.selfTrackingRad() - math.pi)
            ai.setPower(55)
            ai.thrust()

            print(selfSpeed)
            if selfSpeed < 1:
                mode = "travel"

        if mode == "ready":
            pass


    except:
        print(traceback.print_exc())

"""def time_of_impact(px, py, vx, vy, s):
    """"""
    Determine the time of impact, when ship hits moving item
    Parameters:
        px, py = initial item position in x,y relative to ship
        vx, vy = initial item velocity in x,y relative to ship
        s = initial ship speed
        t = time to impact, in our case ticks
    """"""
    a = s * s - (vx * vx + vy * vy)
    b = px * vx + py * vy
    c = px * px + py * py

    d = b*b + a*c

    t = 0

    #if d >= 0:
    t = b + math.sqrt(d) / a
    if t < 0:
        t = 0
    print(a)
    print(b)
    print(c)
    print(d)
    print(t)
    return t"""


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
