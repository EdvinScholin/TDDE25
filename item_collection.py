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
selectItemType = -1
itemId = -1


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
        global selectItemType
        global itemId

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
        selfSpeed = ai.selfSpeed()

        selfHeading = ai.selfHeadingRad()

        itemCount = ai.itemCountScreen()

        ai.setMaxTurnRad(2*math.pi)

        # Add more sensors readings here

        print("tick count:", tickCount, "mode", mode)

        if mode == "wait":
            if itemCount > 0:
                mode = "ready"
            #else: kanske att åka till mitten eller något för att 
            # hitta ett item.

        elif mode == "ready":
            stopCount += 1
            selfItem = 0
            
            if itemType > -1:
                selfItem = ai.selfItem(selectItemType)
            print(selfItem)

            if stopCount == 1:
                ai.talk("teacherbot: start-mission 8")
            
            if not ai.scanTalkMsg(0) and selfItem > 0:
                complete = "teacherbot: completed collect-item " + str(selectItemType)
                ai.talk(complete)

            if "collect-item" in ai.scanTalkMsg(0):
                mode = "scan"
        
        elif mode == "scan":
            message = ai.scanTalkMsg(0)
            
            messageList = list(message.split(" "))
            selectItemType = messageList[1]

            if selectItemType = "mine":
                selectItemType = 8
            
            ai.removeTalkMsg(0)

            mode "aim"
        
        elif mode == "aim":
            # Excecute when an item is visible
            if itemCount > 0:
                for item in range(itemCount):
                    temp = item
                    if temp
                        
            # Items X and Y coordinate.
                itemX = ai.itemX(itemId)
                itemY = ai.itemY(itemId)

    except:
        print(traceback.print_exc())


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
