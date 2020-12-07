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
readyCount = 0
stopCount = 0
mode = "wait"
desiredItemType = -1
itemId = 0
prevTrackRad = 0
prevSelfItem = 0
itemDir = 0

itemDict = {"fuel": 0, "wideangle": 1, "rearshot": 2, "afterburner": 3, "cloak": 4, 
            "sensor": 5, "transporter": 6, "tank": 7, "mine": 8, "missile": 9, "ecm": 10,
            "laser": 11, "emergencythrust": 12, "tractorbeam": 13, "autopilot": 14, 
            "emergencyshield": 15, "itemdeflector": 16, "hyperjump": 17, "phasing": 18, 
            "mirror": 19, "armor": 20} 
def tick():
    #
    # The API won't print out exceptions, so we have to catch and print them ourselves.
    #
    try:

        #
        # Declare global variables so we have access to them in the function
        #
        global tickCount
        global readyCount
        global stopCount
        global mode
        global desiredItemType
        global itemId
        global prevTrackRad
        global prevSelfItem
        global itemDir

        #
        # Reset the state machine if we die.
        #
        if not ai.selfAlive():
            tickCount = 0
            mode = "wait"
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
        try:
            selfMass = ai.selfMass()
        except: UnboundLocalError

        selfHeading = ai.selfHeadingRad()

        # Calcualtes which direction the middle is 
        middleDisX = ai.radarWidth()/2 - ai.selfRadarX()                  
        middleDisY = ai.radarHeight()/2 - ai.selfRadarY()                 
        middleDir = math.atan2(middleDisY, middleDisX)

        wallDistance = ai.wallFeelerRad(1000, ai.selfTrackingRad())

        ai.setMaxTurnRad(2*math.pi)

        # Add more sensors readings here

        print("tick count:", tickCount, "mode", mode)

        if mode == "wait":
            mode = "ready"

        elif mode == "ready":
            
            # To limit times mode we start the mission
            stopCount += 1
        
            # Start mission
            if stopCount == 1:
                ai.talk("teacherbot: start-mission 8")

            if "collect-item" in ai.scanTalkMsg(0):
                mode = "scan"
        
        elif mode == "scan":

            if "[Teacherbot]:[Stub]" in ai.scanTalkMsg(0): 
                # Scan in the most recent message
                message = ai.scanTalkMsg(0)
                
                # Second element in list will be our desired item
                messageList = list(message.split(" "))
                desiredItemType = messageList[1]

                if desiredItemType in itemDict:
                    desiredItemType = itemDict[desiredItemType]
                
                # Save how many items of the desired item we already have
                prevSelfItem = ai.selfItem(desiredItemType)
                        
                mode = "checkSituation"  
        
        # Take the closest item
        itemCount = ai.itemCountScreen()   
        prevItemDist = 1000
        prevDesiredItemDist = 1000
        desirededItemCount = 0

        if itemCount > 0:

            for index in range(itemCount):
                        
                itemDist = ai.itemDist(index)
                
                if ai.itemType(index) == desiredItemType:
                    desirededItemCount += 1
                    
                    if itemDist < prevDesiredItemDist:
                        prevDesiredItemDist = itemDist
                        itemId = index
            
                else:
                    if itemDist < prevItemDist:
                        prevItemDist = itemDist
                        restItemId = index  
            
            # If there are none of the desired type, we want to take the closest item 
            if desirededItemCount == 0:
                itemId = restItemId

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
            t = time_of_impact(relX, relY, relVelX, relVelY, selfSpeed)

            # Point of impact, where ship is supposed to hit item
            aimAtX = relX + relVelX*t
            aimAtY = relY + relVelY*t

            # Direction of aimpoint
            itemDist = math.sqrt(aimAtX**2 + aimAtY**2)
            itemDir = math.atan2(aimAtY, aimAtX)

        if mode == "checkSituation":

            if abs(wallDistance) < 1:
                p = 55
            else:    
                p = selfSpeed**2 * (selfMass+5) / wallDistance
            
            if 40 <= p:
                mode = "stop"
                prevTrackRad = ai.selfTrackingRad()
            
            elif itemCount > 0:
                ai.setPower(45)
                mode = "aim"
            
            else:
                ai.turnToRad(middleDir)
                ai.setPower(45)
                ai.thrust()
        
        elif mode == "aim":
            if itemCount == 0:
                mode = "checkSituation"
                return
            
            if ai.itemSpeed(itemId) > 0:
                selfTrackRad = ai.selfTrackingRad() % (2*math.pi)
                absItemDir = itemDir % (2*math.pi)
                movItemDiff = angleDiff(ai.selfTrackingRad(), itemDir)
                
                if stop_at_point(itemDist + 50):  
                    prevTrackRad = ai.selfTrackingRad()
                    mode = "stop"
                    return
                
                if selfSpeed < 5 or movItemDiff == math.pi/2:
                    angle = itemDir
                
                elif movItemDiff > math.pi/2:
                    prevTrackRad = ai.selfTrackingRad()
                    mode = "stop"
                    return
                    
                else:
                    angle = 2*absItemDir - selfTrackRad
                
                mode = "checkSituation"

                # Turns to target direction
                ai.turnToRad(angle)
                ai.thrust()
            
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
            
            # When we have picked up the item, send us to "done"
            if prevSelfItem < ai.selfItem(desiredItemType):
                mode = "done"
        
        elif mode == "stop":

            angle = angleDiff(prevTrackRad, ai.selfTrackingRad())

            if angle < math.pi/2:
                ai.turnToRad(ai.selfTrackingRad() - math.pi)


            if angle > math.pi/2:
                mode = "checkSituation"
                return
            
            ai.setPower(55)
            ai.thrust()
           
            if prevSelfItem < ai.selfItem(desiredItemType):
                mode = "done"
        
        elif mode == "done":
            
            # Gets the key from the value in our dictionary of our desired 
            # item in order to send a message to teacherbot
            itemStrValue = list(itemDict.keys())[list(itemDict.values()).index(desiredItemType)]
            completed = "Teacherbot: completed collect-item " + itemStrValue
            ai.removeTalkMsg(0)
            ai.talk(completed)
            mode = "scan"

    except:
        print(traceback.print_exc())


def angleDiff(one, two):
    """Calculates the smallest angle between two angles"""

    a1 = (one - two) % (2*math.pi)
    a2 = (two - one) % (2*math.pi)
    return min(a1, a2)

def stop_at_point(objDist):

    """determine when ship need to stop"""

    p = 55
    v0 = ai.selfSpeed()
    m = ai.selfMass() + 5
    a = p / m
    a2 = p / m
    s = objDist
    
    maxV0 = math.sqrt(2*a*s)

    futV = v0 + a2/2
    futS = s - futV
    futMaxV0 = math.sqrt(2*a*futS)

    if futMaxV0 <= futV:
        return True


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
