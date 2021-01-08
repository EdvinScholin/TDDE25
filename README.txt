# ==================================================================
# Completed activities
# ==================================================================
Här är en lista på alla uppgifter som utförts:
1. Hela tutorial
2. Basic navigation
3. Item collection
4. Item handling (advanced)
5. Path finding (basic)
6. Path drawing
7. Path following, fast kod för att undvika kulor och skepp är inte 
   implementerad

Tillsammans uppnår det här 100 poäng plus eventuella delpoäng på uppgiften path following.

# ==================================================================
# Exexution of activities
# ==================================================================
Filen item_handling.py använder sig av 1. - 4. och kan köras på kartan
item.xp som finns i mappen, maps. 

# Starta kartan genom att skriva in (om du står i maps):
  xpilots -map item.xp -noQuit +reportToMetaServer -port 15348

# Starta teacherbot genom att skriva in:
  teacherbot.py --port 15348

# Starta boten genom att skriva in:
  python3 item_handling.py --port 15348


Filen path_following.py använder sig av 5. - 7. och kan köras på kartan 
maze.xp som finns i mappen, maps.

# Starta kartan genom att skriva in (om du står i maps):
  xpilots -map maze.xp -noQuit +reportToMetaServer -port 15348

# Starta teacherbot genom att skriva in:
  teacherbot.py --port 15348

# Starta boten genom att skriva in:
  python3 path_following.py --port 15348
