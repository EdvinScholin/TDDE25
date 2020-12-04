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
stopCount = 0
stopCount2 = 0
mode = "wait"
xCord = 0
yCord = 0
tasks = []
send = []
lenTasks = 0
all_nodes = []
path = []
prevTrackRad = 0
dirRad = 0
# add more if needed
blockSize = ai.blockSize()

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
        global xCord
        global yCord
        global stopCount
        global tasks
        global send
        global lenTasks
        global all_nodes
        global path
        global stopCount2
        global prevTrackRad
        global dirRad
        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
            tickCount = 0
            if stopCount2 == 0:
                mode = "wait"
            else:
                mode = "cords"
            return

        tickCount += 1
        stopCount2 += 1

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
        selfTrackingRad = ai.selfTrackingRad()
        playerCount = ai.playerCountServer()
        pi = math.pi
        

        mapWidth = ai.mapWidthBlocks()
        mapHeight = ai.mapHeightBlocks()

        shotCount = ai.shotCountScreen()

        ai.setMaxMsgs(15)
        maxMsgs = ai.getMaxMsgs()

        wallDistance = ai.wallFeelerRad(1000, selfTrackingRad)

        ai.setMaxTurnRad(2*pi)
        # 0-2pi, 0 in x direction, positive toward y

        # Add more sensors readings here

        print ("tick count:", tickCount, "mode:", mode)
        print("Path: ", path)

        if tickCount == 1:
            ai.shield()


        if mode == "wait" :
            if playerCount > 1:
                mode = "ready"


        elif mode == "ready":
            stopCount += 1

            # If you are alone on the server change mode to wait
            if playerCount == 1:
                mode = "wait"
                return

            # Starts mission 7 and create the map
            if stopCount == 1:
                ai.talk("Teacherbot:start-mission 10")

                for x in range(mapWidth):
                    for y in range(mapHeight):
                        if (ai.mapData(x, y) == 0 or 30 <= ai.mapData(x, y) <= 39):
                            all_nodes.append((x, y))


            # When you recieve a message from teacherbot change mode to scan
            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0):
                mode = "scan"


        elif mode == "scan":

            # Clears the tasks list
            tasks.clear()

            # Scans all the messages sent by teacherbot
            # and adds them to the list tasks
            for message in range(maxMsgs):
                if ai.scanTalkMsg(message) and "[Teacherbot]:[Stub]" in ai.scanTalkMsg(message):
                    tasks.append(ai.scanTalkMsg(message))
                    ai.removeTalkMsg(message) 

            # Save the length of the task in the variable lenTasks
            lenTasks = len(tasks)

            # Change mode to aim
            mode = "cords"


        elif mode == "cords":

            # Saves the coordinates of the last message in
            # tasks in the variables xCord and yCord
            coordinates = []
            for seq in tasks[-1].split():
                if seq.isdigit():
                    coordinates.append(int(seq))
            xCord = coordinates[0]
            yCord = coordinates[1]

            #Change mode to path
            mode = "path"


        elif mode == "path":
         
            # Calculate the start and goal position of the path
            selfBlock = pixel_to_block(selfX, selfY)
            goal = pixel_to_block(xCord, yCord)

            

            # Create the path using an a* algorithm
            path = list(astar.find_path(selfBlock, goal, neighbors_fnct=neighbors,
                        heuristic_cost_estimate_fnct=heuristic_cost_estimate, distance_between_fnct=distance))

            path.remove(selfBlock)
            
            print(path)            
            # Change mode to aim
            mode = "aim"


        elif mode == "aim":  # dela upp i aim och travel 

            selfBlock = pixel_to_block(selfX, selfY)

            x = path[0][0] - selfBlock[0]
            y = path[0][1] - selfBlock[1]


            dirRad = math.atan2(y, x)
            targetDistance = math.hypot(x, y)
            print("Targetdistinace:", targetDistance)

            # Convert selfTrackingRad and ItemDir to positive radians
            selfTrackRad = ai.selfTrackingRad() % (2*math.pi)
            absItemDir = dirRad % (2*math.pi)

            # Calculate angle difference
            movItemDiff = angleDiff(
                ai.selfTrackingRad(), dirRad)

            if targetDistance == 0:
                print("hej")
                path.pop(0)
                if len(path) == 1:
                    mode = "stop"
                if not path:
                    mode = "stop"
                return

            # Wallfeeler
            if brake(wallDistance - 50) and wallDistance != -1:
                prevTrackRad = ai.selfTrackingRad()
                mode = "stop"


            # Move towards target
            if selfSpeed < 5 or movItemDiff == math.pi/2:
                angle = dirRad

            elif movItemDiff > math.pi/2:  # if angle between selfTrackingRad and item direction
                prevTrackRad = ai.selfTrackingRad()
                mode = "stop"
                return

            else:  # Uses opposite velocity vektor to cancel out unwanted velocity vektors
                angle = 2*absItemDir - selfTrackRad

            

            ai.turnToRad(angle)
            ai.thrust()


            
            

        elif mode == "navigation":

            """
            # Wallfeeler
            if brake(wallDistance - 50) and wallDistance != -1:
                prevTrackRad = ai.selfTrackingRad()
                mode = "stop"
            """

            
            if selfSpeed < 20:
                ai.setPower(55)
            mode = "aim"


            

        elif mode == "stop":
            
            angle = angleDiff(prevTrackRad, ai.selfTrackingRad())

            if angle < math.pi/2:
                ai.turnToRad(ai.selfTrackingRad() - math.pi)

            if angle > math.pi/2:
                if len(path) == 1 or not path:
                    mode = "completed_task"
                else:
                    path.pop(0)
                    mode = "aim"
        

            ai.setPower(55)
            ai.thrust()

            


        elif mode == "completed_task":

            # Adds the completed task to a list send
            for elem in tasks:
                new_msg = ""
                if str(xCord) in elem and str(yCord) in elem:
                    for seq in elem.split():
                        if not "[" in seq:
                            new_msg += seq + " "
                    completed = "Teacherbot:completed " + new_msg
                    send.append(completed)
            
            # If you have completed all the tasks send the messages from the send list,
            # clear the send and tasks list and change mode to completed_all_tasks
            if len(send) == lenTasks:
                for elem in send:
                    ai.talk(elem)
                send.clear()
                tasks.clear()
                mode = "completed_all_tasks"

            # If you havent completed all the tasks remove the
            # last task in the list and change mode to aim
            else:
                tasks.pop()
                mode = "cords"
                 

        elif mode == "completed_all_tasks":

            # If you recieve a new message from 
            # teacherbot change mode to scan
            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0):
                lenTasks = 0
                mode = "scan"

            


            
            


            

    except:
        print(traceback.print_exc())

def angleDiff(one, two):
    """Calculates the smallest angle between two angles"""

    a1 = (one - two) % (2*math.pi)
    a2 = (two - one) % (2*math.pi)
    return min(a1, a2)

def block_to_pixel(x, y):
    pixelX = x*blockSize + blockSize/2
    pixely = y*blockSize + blockSize/2
    return (pixelX, pixely)

def pixel_to_block(x, y):
    blockX = x//blockSize
    blockY = y//blockSize
    return (blockX, blockY)

def neighbors(node):
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1),(-1, 0), (-1, -1), (0, -1), (1, -1)]
    result = []
    for dir in dirs:
        neighbor = (node[0] + dir[0], node[1] + dir[1])
        if neighbor in all_nodes:
            result.append(neighbor)
    return result

def heuristic_cost_estimate(n1, n2):
    """ If a node is next to wall increase the cost to 5 """
    if block_neighbors(n1):
        return 20
    return 1

def distance(n1, n2):
    (x1, y1) = n1
    (x2, y2) = n2
    return math.hypot(x2 - x1, y2 - y1)

def block_neighbors(node):
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1),(-1, 0), (-1, -1), (0, -1), (1, -1)]
    for dir in dirs:
        neighbor = (node[0] + dir[0], node[1] + dir[1])
        if ai.mapData(neighbor[0], neighbor[1]) == 1:
            return True
    return False

def stop_at_point(objDist):

    v0 = ai.selfSpeed()
    m = ai.selfMass() + 5
    p = 55
    a = p / m
    a2 = 45 / m

    oldb = (v0)**2 / (2 * a)
    print("brake: ", oldb)

    brakeDist = (v0 + a2)**2 / (2 * a)
    print("futbrake: ", brakeDist)

    # s = 2 * v0**2 * m / p

    if objDist <= brakeDist:
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

def brake(dist, accForce=55, decForce=55):
    """Determine when to brake"""

    m = ai.selfMass() + 5
    v = ai.selfSpeed()

    futV = v + accForce / m
    futDist = dist - v - accForce / (2 * m)

    futDecForce = m * futV**2 / (2 * futDist)

    if futDecForce >= decForce:
        return True
    return False



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
