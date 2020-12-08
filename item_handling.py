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

# Coordinates - Vill helst ha en tuple
coordinates = []
prevCoordinates = []

# Message handling
tasks = []
lenTasks = 0
send = []

# Movement
prevTrackRad = 0
dist = 0
dirRad = 0

# Items
itemDict = {"fuel": 0, "wideangle": 1, "rearshot": 2, "afterburner": 3, "cloak": 4,
            "sensor": 5, "transporter": 6, "tank": 7, "mine": 8, "missile": 9, "ecm": 10,
            "laser": 11, "emergencythrust": 12, "tractorbeam": 13, "autopilot": 14,
            "emergencyshield": 15, "itemdeflector": 16, "hyperjump": 17, "phasing": 18,
            "mirror": 19, "armor": 20}
prevSelfItem = 0
desiredItemType = -1
item_needed = 1


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
        global itemDict
        global prevSelfItem
        global desiredItemType
        global tasks
        global lenTasks
        global send
        global coordinates
        global prevCoordinates
        global dist
        global dirRad
        global item_needed

        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
            print("dead")
            tickCount = 0
            mode = "ready"
            return

        tickCount += 1

        print("tick count:", tickCount, "mode", mode)

        if tickCount == 1:
            ai.talk("teacherbot: start-mission 9")

        #
        # Read some "sensors" into local variables, to avoid excessive calls to the API
        # and improve readability.
        #

        selfX = ai.selfX()
        selfY = ai.selfY()
        print("selfCoordinates: ", selfX, selfY)
        selfVelX = ai.selfVelX()
        selfVelY = ai.selfVelY()
        selfSpeed = ai.selfSpeed()

        # 0-2pi, 0 in x direction, positive toward y

        # Allows the ship to turn 360 degrees.
        ai.setMaxTurnRad(2*math.pi)

        wallDistance = ai.wallFeelerRad(1000, ai.selfTrackingRad())

        # Calcualtes which direction the middle is
        middleDisX = ai.radarWidth()/2 - ai.selfRadarX()
        middleDisY = ai.radarHeight()/2 - ai.selfRadarY()
        middleDir = math.atan2(middleDisY, middleDisX)
        
        # Wallfeeler
        if brake(wallDistance - 50) and wallDistance != -1:
            '''
            prevTrackRad = ai.selfTrackingRad()
            mode = "stop"
            print("wallFeeler")
            return
            '''
            ai.turnToRad(ai.selfTrackingRad() + math.pi)
            print("self heading", ai.selfHeadingRad())
            ai.setPower(55)
            ai.thrust()
            mode = "ready"
            return
            

        # ---------------------------------------------------------------------------
        # Cordinates
        # ---------------------------------------------------------------------------
        # Lägg till if-sats senare, i detta fall för items
        countScreen = ai.itemCountScreen()
        speed = selfSpeed
        # ---------------------------------------------------------------------------
        # Teacherbot
        # ---------------------------------------------------------------------------

        if mode == "ready":

            if countScreen == 0:  # Move towards map middle when no targets are detected
                ai.turnToRad(middleDir)
                ai.setPower(55)
                ai.thrust()
                return

            '''
            # Scan in the most recent message
            message = ai.scanTalkMsg(0)

            # Second element in list will be our desired item
            messageList = list(message.split(" "))
            '''

            ai.setMaxMsgs(15)
            maxMsgs = ai.getMaxMsgs()

            #print("tasks: ", tasks)
           
            # Scans all the messages sent by teacherbot
            # and adds them to the list tasks
            if not tasks:
                for message in range(maxMsgs):
                    if ai.scanTalkMsg(message) and "[Teacherbot]:[Stub]" in ai.scanTalkMsg(message):
                        tasks.append(ai.scanTalkMsg(message))
                        ai.removeTalkMsg(message)
                        # tasks = [ai.scanTalkMsg(message)].copy()
                        #if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0):
                        #    ai.removeTalkMsg(message)
                        
            print("tasks: ", tasks)

            # Save the length of the task in the variable lenTasks
            lenTasks = len(tasks)


            # print("coordinates: ", coordinates)

            '''
            # Read message
            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0):
            '''

            if not coordinates and tasks:
                for seq in tasks[-1].split():
                    if seq.isdigit():
                        coordinates.append(int(seq))
                    if seq in itemDict.keys():
                        desiredItemType = itemDict[seq]
           
            #
            # Nu är det dags att använda en missil och skjuta den
            #

            if tasks:

                if "collect-item" in tasks[-1]: 

                    Id = nearest_desired_target_Id("item")

                    # Targets position relativt self
                    x, y = target_pos(Id, selfSpeed)

                    if prevSelfItem < ai.selfItem(desiredItemType):
                        mode = "completed_task"

                    else:
                        mode = "navigation"

                elif "use-item" in tasks[-1]:
               
                    mode = "navigation"
                
                    if coordinates:
                        # Targets position relativt self
                        x, y = relative_pos(coordinates[0], coordinates[1])
                    
                    elif "mine" in tasks[-1]:
                        Id = nearest_target_Id("mine")
                        x, y = relative_pos(ai.mineX(Id), ai.mineY(Id))
                    
                    else: # När vi inte kan hantera mer så quitar vi
                        ai.quitAI()


                    if ai.selfItem(desiredItemType) == 0 and ai.mineCountScreen() == 0:

                        Id = nearest_desired_target_Id("item")

                        # Targets position relativt self
                        x, y = target_pos(Id, selfSpeed)

                    elif not coordinates:# Betyder att vi har droppat minan
                    
                        # Rör sig bort från mine
                        dist = math.hypot(x, y)
                    
                        # Om det är en vägg i riktningen vi tänkte åka så åker vi i motsatt rikning
                    
                        if dist > 300:
                            print("detonate")
                            ai.detonateMines()
                            prevCoordinates.clear()
                            mode = "completed_task"
                            print(mode)
                        return

                    elif dist < 20:
                        print("dropmine")
                        item_needed = 0
                        ai.dropMine()
                        mode = "completed_task"
                        
                        # Vill åka tillbaka där vi kom ifrån
                        dirRad = ai.selfTrackingRad() -  math.pi
                        return
                        
                    '''
                    # Ship stops when target is reached.
                    if brake(dist):
                        prevTrackRad = ai.selfTrackingRad()
                        mode = "stop"
                        return
                    ''' 
                
                # Distance and direktion to target
                dist = math.hypot(x, y)
                dirRad = math.atan2(y, x)

                # Save how many items of the desired item we already have
                prevSelfItem = ai.selfItem(desiredItemType)

            else: # om vi inte har några tasks
                
                print("all tasks done")
                ''' 
                if selfSpeed > 5:
                    prevTrackRad = ai.selfTrackingRad()
                    mode = "stop"
                '''
                '''
                ai.talk('use-item mine 612 17 [Teacherbot]:[Stub]')
                return
                '''

        elif mode == "completed_task":
            
            ########## Tar inte bort gamla tasket

            # Adds the completed task to a list send
            if coordinates:
                prevCoordinates = coordinates.copy()
                coordinates.clear()
            
            for elem in tasks:
                new_msg = ""
                # if str(prevSelfItem) in elem:
                for seq in elem.split():
                    if not "[" in seq:
                        new_msg += seq + " "
                completed = "Teacherbot:completed " + new_msg
                send.append(completed)


            # If you have completed all the tasks send the messages from the send list,
            # clear the send and tasks list and change mode to completed_all_tasks
            
            print("len send: ", len(send))
            print("len tasks: ", lenTasks)

            
            if len(send) == lenTasks:
                for elem in send:
                    ai.talk(elem)
                send.clear()
                tasks.clear()
                mode = "completed_all_tasks"

            # If you havent completed all the tasks remove the
            # last task in the list and change mode to cords
            else:
                tasks.pop()
                mode = "ready"
            
        elif mode == "completed_all_tasks":

            # If you recieve a new message from
            # teacherbot change mode to scan
            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0):
                lenTasks = 0
                mode = "ready"

            '''
            elif mode == "mission done": 
            # Gets the key from the value in our dictionary of our desired 
            # item in order to send a message to teacherbot
            itemStrValue = list(itemDict.keys())[list(
                itemDict.values()).index(desiredItemType)]
            completed = "Teacherbot: completed collect-item " + itemStrValue
            print(ai.scanTalkMsg(0))
            ai.removeTalkMsg(0)
            ai.talk(completed)
            mode = "scan"
            '''

        # ---------------------------------------------------------------------------
        # Navigational modes, input is dist(only if ship need to stop at destination)
        # and dirRad to target
        # ---------------------------------------------------------------------------

        elif mode == "navigation":

            # Aim if any targets are detected
            if selfSpeed < 20:
                ai.setPower(55)
            mode = "aim"

        elif mode == "stop":
            
            ai.turnToRad(prevTrackRad - math.pi)
            
            angle = angleDiff(prevTrackRad - math.pi, ai.selfTrackingRad())
            '''
            if angle < math.pi/10:
                ai.turnToRad(ai.selfTrackingRad() - math.pi)

            else:
                mode = "ready"
                return
            '''
            if angle < math.pi/2:
                mode = "ready"
                return
            
            print("prevTrackRad: ", prevTrackRad)
            

            ai.setPower(55)
            ai.thrust()

        elif mode == "aim":  # dela upp i aim och travel
            if countScreen == 0:
                mode = "ready"
                return

            # Convert selfTrackingRad and ItemDir to positive radians
            selfTrackRad = ai.selfTrackingRad() % (2*math.pi)
            absItemDir = dirRad % (2*math.pi)

            # Calculate angle difference
            movItemDiff = angleDiff(
                ai.selfTrackingRad(), dirRad)

            # Ship stops when target is reached. Not necessary.
            '''
            if brake(dist + 50):  
                prevTrackRad = ai.selfTrackingRad()
                mode = "stop"
                return
            '''

            # Move towards target
            if selfSpeed < 5 or movItemDiff == math.pi/2:
                angle = dirRad

            elif movItemDiff > math.pi/2:  # if angle between selfTrackingRad and item direction
                print("aim stop.........")
                prevTrackRad = ai.selfTrackingRad()
                mode = "stop"
                return

            else:  # Uses opposite velocity vektor to cancel out unwanted velocity vektors
                angle = 2*absItemDir - selfTrackRad

            mode = "ready"

            ai.turnToRad(angle)
            ai.thrust()


    except:
        print(traceback.print_exc())

# --------------------------------------------------------------------------
# Help functions
# --------------------------------------------------------------------------


def obj_funcs(objType):
    """Return objekt specified functions"""

    # Kan lägga till för varje objekt typ

    if objType == "item":
        countScreen = ai.itemCountScreen()
        distFunc = ai.itemDist
        typeFunc = ai.itemType
        
        return countScreen, distFunc, typeFunc

    elif objType == "asteroid":
        countScreen = ai.asteroidCountScreen()
        distFunc = ai.asteroidDist
        typeFunc = ai.asteroidType
        
        return countScreen, distFunc, typeFunc

    elif objType == "mine":
        return ai.mineX, ai.mineY, ai.mineCountScreen

    elif objType == "laser":
        return ai.laserX, ai.laserY



def nearest_target_Id(objType):

    xFunc, yFunc, countScreen = obj_funcs(objType)
    prevDist = 10000

    for index in range(countScreen()):
        dist = math.hypot(yFunc(index), xFunc(index))

        if dist < prevDist:
            prevDist = dist
            Id = index

    return Id
    

def nearest_desired_target_Id(objType):
    """Determine nearest desired objekt else nearest random objekt"""

    countScreen, distFunc, typeFunc = obj_funcs(objType)

    # Take the closest item
    prevDist = 1000
    prevDesiredDist = 1000
    desirededCount = 0

    for index in range(countScreen):

        dist = distFunc(index)

        if typeFunc(index) == desiredItemType:
            desirededCount += 1

            if dist < prevDesiredDist:
                prevDesiredDist = dist
                Id = index

        else:
            if dist < prevDist:
                prevDist = dist
                restId = index

    # If there are none of the desired type, we want to take the closest item
    if desirededCount == 0:
        Id = restId

    return Id


def target_pos(Id, speed):
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

    if futDecForce >= decForce:
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
