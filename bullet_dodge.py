#
# This file can be used as a starting point for the bots.
#

import sys
import traceback
import math
import libpyAI as ai
from sympy import symbols, solve
from optparse import OptionParser

#
# Global variables that persist between ticks
#
tickCount = 0
mode = "ready"

    

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

        #
        # Read some "sensors" into local variables, to avoid excessive calls to the API
        # and improve readability.
        #
        ai.setMaxTurnRad(2*math.pi)
        
        selfX = ai.selfX()
        selfY = ai.selfY()
        selfVelX = ai.selfVelX()
        selfVelY = ai.selfVelY()

        selfHedingRad = ai.selfHeadingRad()

        shotCount = ai.shotCountScreen()

        selfSpeed = ai.selfSpeed()

        

        if tickCount == 1:
            ai.shield()

        print ("tick count:", tickCount, "mode", mode)


        if mode == "ready":
        
            f1 = equation(selfX, selfY, selfHedingRad)
            
            for shot in range(shotCount):
                f2 = equation(ai.shotX(shot), ai.shotY(shot), ai.shotTrackingRad(shot))
                intPoint = intersect(f1, f2)
                time_of_intersect(intPoint, selfSpeed, selfX, selfY)
                time_of_intersect(intPoint, ai.shotSpeed(shot), ai.shotX(shot), ai.shotY(shot))
            
            
    


    except:
        print(traceback.print_exc())


def angleDiff(one, two):
    """Calculates the smallest angle between two angles"""

    a1 = (one - two) % (2*math.pi)
    a2 = (two - one) % (2*math.pi)
    return min(a1, a2)

def equation(x, y, angle):

    k = math.tan(angle)

    m = y - x*k

    return (k, m)

def intersect(f1, f2):

    m1 = f1[1]
    m2 = f2[1]
    k1 = f1[0]
    k2 = f2[0]

    try:
        x = (m2- m1) / (k1 - k2)
    except ZeroDivisionError:
        return None

    y = x*k1 + m1

    return (x, y)

def time_of_intersect(point, selfVel, selfX, selfY):
    pointX = point[0]
    pointY = point[1]
    
    a = pointX - selfX
    b = pointY - selfY

    S = math.hypot(a, b)
    V = selfVel
    A = ai.getPower() / (ai.selfMass()+5)

    x = symbols('x')
    sol = solve((A/2)*x**2+V*x-S, x)

    for elem in sol:
        if elem > 0:
            return elem



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