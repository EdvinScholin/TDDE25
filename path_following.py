#
# This file can be used as a starting point for the bots.
#

import sys
import traceback
import math
import libpyAI as ai
import astar
from optparse import OptionParser

#
# Global variables that persist between ticks
#
tickCount = 0
mode = "ready"
all_nodes = []
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
        global all_nodes

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

        mapWidth = ai.mapWidthBlocks()
        mapHeight = ai.mapHeightBlocks()
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode", mode)


        if mode == "ready":

            for x in range(mapWidth):
                for y in range(mapHeight):
                    all_nodes.append((x, y))
            

            if tickCount == 50:
                for element in all_nodes:
                    if ai.mapData(element[0], element[1]) == 1:
                        print(chr(9608), end=(' ' if element[1]!=31 else '\n'))
                        
               
           

    except:
        print(traceback.print_exc())

def make_maze(w=32, h=32):
    """returns an ascii maze as a string"""
    ver = [[chr(9608)] * w for _ in range(h)] + [[]]
    hor = [[chr(9608)] * w for _ in range(h + 1)]

    result = ''
    for (a, b) in zip(hor, ver):
        if ai.mapData() == 1:
            result = result + (' '.join(a + ['\n'] + b)) + '\n'
    return result.strip()

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
