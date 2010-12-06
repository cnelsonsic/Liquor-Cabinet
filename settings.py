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
DATABASE_PATH = "sqlite:///:memory:"
DEBUG = False
WRITE_DATA_DELAY = 1000*60*5 #Time between writing data to disk In milliseconds

SPLASH_MESSAGE_DELAY = 0.333
NOSPLASH = True #Disables splash screen entirely.

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