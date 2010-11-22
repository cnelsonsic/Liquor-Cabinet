'''
Defines some default content for insertion into the database by default.

All trademarks mentioned are the property of their respective owners.
 
'''

from settings import *

#TODO: Call upcdatabase.com to pull size and name info: http://www.upcdatabase.com/python_example_new.txt

DEFAULT_INGREDIENTS = (
	#Ingredients:
	#Ingredient(name, barcode, size, current_amount=0, threshold=-1, note="")
	#Size is in mL
	("Smirnoff Vodka", "082000727606", 1750),
	("Heaven Hill Vodka", "096749013302", 750, 0, -1, "Gives me headaches."),
	("Sailor Jerry Spiced Rum", "0083664868735", 1750, 0, -1, "Rocket fuel."),
	("Captain Morgan Original Spiced Rum", "0087000002715", 750),
	("Dekuyper Sour Apple Pucker", "080686395409", 750, 0, -1, "Delicious."),
)

DEFAULT_AMOUNTS = []

if METRIC:
	DEFAULT_AMOUNTS.extend((
		#Amounts:
		#Amount(name, amount, use=3, times_bought=0, times_drank=0)
		#Amount.amount is in mL
		("1cL", 10),
		("50mL", 50), 
		("200mL", 200), 
		("375mL", 375), 
		("500mL", 500), 
		("700mL", 700), 
		("750mL", 750), 
		("1000mL", 1000),
		("1750mL", 1750), 
		("3700mL", 3700),
		
		("Shot", 45), 
		("Double Shot", 45*2), 
		("Wine Glass", 119),
		("Fifth", 750), 
		("Handle", 1750),
	))

#Now, if we want Imperial units, we'll add them to the defaults.
if IMPERIAL:
	IMPOZML = 28.4130625
	DEFAULT_AMOUNTS.extend((
		("1 fl.oz.", 1*IMPOZML),
		("2 fl.oz.", 2*IMPOZML),
		("4 fl.oz.", 4*IMPOZML),
		("8 fl.oz.", 8*IMPOZML),
		("12 fl.oz.", 12*IMPOZML),
		("16 fl.oz.", 16*IMPOZML),
		("32 fl.oz.", 32*IMPOZML),
		
		#("Gill", 5*IMPOZML),
		("Pint", 20*IMPOZML),
		("Quart", 40*IMPOZML),
		("Gallon", 160*IMPOZML),
		
	))

#If we want US units, we'll add them to the defaults.
if UNITEDSTATES:
	USOZML = 29.57353
	DEFAULT_AMOUNTS.extend((
		("1 US fl.oz.", 1*USOZML),
		("2 US fl.oz.", 2*USOZML),
		("4 US fl.oz.", 4*USOZML),
		("8 US fl.oz.", 8*USOZML),
		("12 US fl.oz.", 12*USOZML),
		("16 US fl.oz.", 16*USOZML),
		("32 US fl.oz.", 32*USOZML),

		#("Teaspoon", 4.928921),
		#("Tablespoon", 14.78676),
		("Jigger", 44.36028),
		("Cup", 236.5882),
		("Pint", 473.1765), 
		("Quart", 946.3529), 
		("2-Liter", 2000), 
		("Half-Gallon", 1892.70589),
		("Gallon", 3785.412),

	))










