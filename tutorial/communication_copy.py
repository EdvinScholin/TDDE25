#
# This file can be used as a starting point for the bots.
#

import sys
import traceback
import math
import libpyAI as ai
import random
from optparse import OptionParser

#
# Global variables that persist between ticks
#
tickCount = 0
mode = "wait"
allMessages = []
stopCount = 0

lista = {0: "Stub:coordinates?", 1: "Stub:heading?", 2: "Stub:tracking?", 3: "Stub:speed?", 4: "Stub:items?", 5: "Stub:ships?"}

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
        global allMessages
        global stopCount

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
        selfTracking = ai.selfTrackingRad()

        itemScreen = ai.itemCountScreen()
        shipScreen = ai.shipCountScreen() - 1

        maxMsgs = ai.getMaxMsgs()

        ai.setMaxMsgs(15)

        playerCount = ai.playerCountServer()

        print ("tick count:", tickCount, "mode:", mode, "players:", playerCount)

        if mode == "wait":
            if playerCount > 1:
                mode = "send"
        
        elif mode == "send":
            if playerCount == 1:
                mode = "wait"
                return
            
            randd = random.randrange(6)

            if stopCount % 80 == 0:
                for message in range(maxMsgs):
                    ai.removeTalkMsg(message)
                for i in range(randd):
                    ai.talk(lista[random.randrange(6)])
            
            stopCount += 1

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

name = "Send"

#
# Start the AI
#

ai.start(tick,["-name", name, 
               "-join",
               "-turnSpeed", "64",
               "-turnResistance", "0",
               "-port", str(options.port)])