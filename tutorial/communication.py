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
mode = "wait"
allMessages = []

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

        playerCount = ai.playerCountServer()

        print ("tick count:", tickCount, "mode:", mode, "players:", playerCount)

        if mode == "wait":
            if playerCount > 1:
                mode = "scan"
        
        elif mode == "scan":
            if playerCount == 1:
                mode = "wait"
                return

            # Clear the list of messages
            allMessages.clear()

            # Scan all messages and add them to a list allMessages
            for message in range(maxMsgs):
                if ai.scanTalkMsg(message):
                    allMessages.append(ai.scanTalkMsg(message))
                    ai.removeTalkMsg(message) 

            # If there is a message in allMessages change mode to send
            if allMessages:
                mode = "send"
            
        elif mode == "send":

            playerName = ""
            
            # Looks through all the messages received and sends back information
            for message in range(len(allMessages)):

                # Sends the coordinates to the player who asked for it
                if "coordinates" in allMessages[message] and name in allMessages[message]:
                    for player in range(playerCount):
                        if ai.playerName(player) in allMessages[message] and ai.playerName != name:
                            playerName = ai.playerName(player)

                    coordinates = playerName + ":" + "X:" + str(selfX) + " Y:" + str(selfY)
                    ai.talk(coordinates)

                # Sends the heading of the ship in radians to the player who asked for it
                if "heading" in allMessages[message] and name in allMessages[message]:
                    for player in range(playerCount):
                        if ai.playerName(player) in allMessages[message] and ai.playerName != name:
                            playerName = ai.playerName(player)

                    heading = playerName + ":" + str(selfHeading)
                    ai.talk(heading)

                # Sends the tracking of the ship in radians to the player who asked for it
                if "tracking" in allMessages[message] and name in allMessages[message]:
                    for player in range(playerCount):
                        if ai.playerName(player) in allMessages[message] and ai.playerName != name:
                            playerName = ai.playerName(player)

                    tracking = playerName + ":" + str(selfTracking)
                    ai.talk(tracking)

                # Sends the speed of the ship to the player who asked for it
                if "speed" in allMessages[message] and name in allMessages[message]:
                    for player in range(playerCount):
                        if ai.playerName(player) in allMessages[message] and ai.playerName != name:
                            playerName = ai.playerName(player)

                    speed = playerName + ":" + str(selfSpeed)
                    ai.talk(speed)

                # Sends the number of items seen on the screen to the player who asked for it
                if "items" in allMessages[message] and name in allMessages[message]:
                    for player in range(playerCount):
                        if ai.playerName(player) in allMessages[message] and ai.playerName != name:
                            playerName = ai.playerName(player)

                    items = playerName + ":" + str(itemScreen)
                    ai.talk(items)

                # Sends the number of ships seen on the screen to the player who asked for it
                if "ships" in allMessages[message] and name in allMessages[message]:
                    for player in range(playerCount):
                        if ai.playerName(player) in allMessages[message] and ai.playerName != name:
                            playerName = ai.playerName(player)

                    ships = playerName + ":" + str(shipScreen)
                    ai.talk(ships)
                
            mode = "scan"

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