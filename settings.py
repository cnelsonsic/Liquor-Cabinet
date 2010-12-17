'''
A note about settings:
The number sign: "#" is the mark to denote a line is a comment.
By commenting out lines, you can turn them off and return them to the defaults.
This is Python, dont add whitespace that isnt there, use proper capitalization.
In general, follow the examples.
'''
 
#Set one or more of these to True to get more units of measurement.
#If you disable one of these, their units wont go away until 
#you delete your database file.
METRIC = True
IMPERIAL = False
UNITEDSTATES = False

RESOURCES_DIR = "resources/"
TEMPLATE_DIR = RESOURCES_DIR+"templates/"

TRAY_ICON = RESOURCES_DIR+"bottle.png"

#Database Path should be an SQL URI. SQLite is fastest so we use it in memory by default.
#See http://www.sqlalchemy.org/docs/05/dbengine.html#create-engine-url-arguments to use a different database.
DATABASE_PATH = "sqlite:///:memory:"

#Database Filename is the name of the python file we'll write to every so often and read in on startup.
#This gives us free forwards compatibility, plus a (mostly) human readable database file.
DATABASE_FILENAME = "database.py"
DATABASE_BACKUP_DIR = "database_backups/"

DEBUG = False

#Time between writing data to disk In milliseconds
WRITE_DATA_DELAY = 1000*60*5

SPLASH_MESSAGE_DELAY = 0.333

#Disables splash screen entirely.
NOSPLASH = True 

#10 hours past 8am, 6pm
PURITAN_TIME = 10

#4 hours past 8am, 12 noon
MODERN_TIME = 4 

#A sure sign of alcoholism is when a person is drunk before noon. Or 6pm.
DRUNK_BEFORE_NOON = PURITAN_TIME 

LOADING_MESSAGES = (
    "Extruding Mesh Terrain",
    "Balancing Domestic Coefficients",
    "Inverting Career Ladder",
    "Calculating Money Supply",
    "Normalizing Social Network",
    "Reticulating Splines",
    "Adjusting Emotional Weights",
    "Calibrating Personality Matrix",
    "Inserting Chaos Generator",
)