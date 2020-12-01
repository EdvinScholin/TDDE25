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
mapp = []
stopCount = 0
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
        global stopCount
        global mapp

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

        sq = chr(9610)
        mapWidth = ai.mapWidthBlocks()
        mapHeight = ai.mapHeightBlocks()
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode:", mode)


        if mode == "ready":

            for x in range(mapWidth-1, -1, -1):
                for y in range(mapHeight):
                    mapp.append((y, x))
            

            for x in range(mapWidth):
                for y in range(mapHeight):
                    if (ai.mapData(x, y) == 0 or 30 <= ai.mapData(x, y) <= 39) and block_neighbors((x, y)):
                        all_nodes.append((x, y))
            print(all_nodes)
            mode = "draw"


        elif mode == "draw":

            path = list(astar.find_path((2, 2), (29, 29), neighbors_fnct=neighbors,
                        heuristic_cost_estimate_fnct=cost, distance_between_fnct=distance))

            
            for element in mapp:
                if element in path:
                    if element == path[0] or element == path[-1]:
                        print("x", end="")
                    else:
                        print("o", end="")  
                elif element[0] == mapWidth-1:
                        if ai.mapData(element[0], element[1]) == 1:
                            print(sq, end="\n")
                        else:
                            print(" ", end="\n")
                elif ai.mapData(element[0], element[1]) == 1:
                    print(sq, end="")
                else:
                    print(" ", end="")
            
            
            mode = "wait"
               
        elif mode == "wait":
            return
           

    except:
        print(traceback.print_exc())

def block_neighbors(node):
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1),(-1, 0), (-1, -1), (0, -1), (1, -1)]
    for dir in dirs:
        neighbor = (node[0] + dir[0], node[1] + dir[1])
        if ai.mapData(neighbor[0], neighbor[1]) == 1:
            return False
    return True

def neighbors(node):
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1),(-1, 0), (-1, -1), (0, -1), (1, -1)]
    result = []
    for dir in dirs:
        neighbor = (node[0] + dir[0], node[1] + dir[1])
        if neighbor in all_nodes:
            result.append(neighbor)
    return result

def cost(n1, n2):
    return 1

def distance(n1, n2):
    (x1, y1) = n1
    (x2, y2) = n2
    return math.hypot(x2 - x1, y2 - y1)

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
