'''Holds all the tables for our database and whatnot.'''

from sqlalchemy import Table, Column, Integer, String, Float
from sqlalchemy import MetaData, ForeignKey

metadata = MetaData()

#~ drinks_table = Table('drinks', metadata,
	#~ Column('id', Integer, primary_key=True),
    #~ Column('name', String),
#~ )
#~ 
#~ drink_contents_table = Table('drink_contents', metadata,
	#~ Column('id', Integer, primary_key=True),
	#~ Column('drink_id', Integer, ForeignKey('drinks.id')),
	#~ Column('ingredient_id', Integer, ForeignKey('ingredients.id')),
	#~ Column('amount', Float),
#~ )





















