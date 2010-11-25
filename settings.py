'''
A note about settings:
The number sign: "#" is the mark to denote a line is a comment.
By commenting out lines, you can turn them off and return them to their defaults.
This is Python, so dont add whitespace that isnt there, use proper capitalization.
In general, follow the examples.
'''
 
#Set one or more of these to True to get more units of measurement.
#If you disable one of these, their units wont go away until you delete your database file.
METRIC = True
IMPERIAL = False
UNITEDSTATES = False

TRAY_ICON = "resources/bottle.png"
DATABASE_PATH = "sqlite:///liquor_cabinet.sqlite"
DEBUG = False

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