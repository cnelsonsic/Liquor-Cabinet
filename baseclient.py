'''This is the base classes that allow you to interface with all the innards of the beast.
''' 

import tables
from models import *
import defaults
from settings import *

import json

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker

class BaseClient(object):
	def __init__(self, path='sqlite:///liquor_cabinet.sqlite', debug=True):
		engine = create_engine(path, echo=debug)
		#~ engine = create_engine('sqlite:///:memory:', echo=debug)
		Ingredient.metadata.create_all(engine)

		#And set up our Sessions
		Session = sessionmaker(bind=engine)
		self.session = Session()
	
	def try_add(self, item):
		'''Tries to add an item into the database. 
		If it fails due to an IntegrityError, it returns False.
		Otherwise it returns True.
		'''
		try:
			self.session.add(item)
			self.session.commit()
			return True
		except(sqlalchemy.exc.IntegrityError),err:
			print(err)
			self.session.rollback()
			return False
			
	def load_defaults(self):
		for i in defaults.DEFAULT_INGREDIENTS:
			self.try_add(Ingredient(*i))
			self.session.commit()
		for a in defaults.DEFAULT_AMOUNTS:
			self.try_add(Amount(*a))
			self.session.commit()
		
	def commit(self):
		self.session.commit()
		
	def get_ingredients(self):
		q = self.session.query(Ingredient).all()
		return q
		
	def get_ingredients_in_stock(self):
		q = self.session.query(Ingredient).filter(Ingredient.current_amount > 0).all()
		return(q)
		
	def get_popular_ingredients(self, limit):
		q = self.session.query(Ingredient).filter(Ingredient.amount_used > 0).order_by(Ingredient.amount_used).limit(limit).all()
		return q
		
	def get_amounts(self):
		q = self.session.query(Amount).order_by(Amount.amount).all()
		return q
		
	def get_amount_by_name(self, name):
		q = self.session.query(Amount).filter(Amount.name==name).all()[0]
		return q
	
	def get_popular_drink_amounts(self, limit):
		q = self.session.query(Amount).filter(Amount.times_drank > 0).order_by(Amount.amount).order_by(Amount.times_drank).limit(limit).all()
		return q
	
	def get_popular_buy_amounts(self, limit):
		q = self.session.query(Amount).filter(Amount.times_bought > 0).order_by(Amount.amount).order_by(Amount.times_bought).limit(limit).all()
		return q
		
	def log(self, log_type, message, drink=None, amount=None):
		if drink is not None:
			drinkid = drink.id
		else:
			drinkid = None
		
		l = Log(log_type, drinkid, amount, message)
		self.try_add(l)
		
		if type(log_type) is int:
			log_type = [k for k, v in Log.TYPES.iteritems() if v == log_type][0]
		if amount is None:
			amount = 0
		retval = ("%s (%s): %s " % (log_type.ljust(8), str(datetime.datetime.now()), message))
		if drink:
			retval += "(%s, %d)" % (str(drink.name), int(amount))
		return retval
		
	def debug(self, message): 
		return self.log(Log.TYPES['DEBUG'], message)
	def info(self, message): 
		return self.log(Log.TYPES['INFO'], message)
	def warning(self, message): 
		return self.log(Log.TYPES['WARNING'], message)
	def error(self, message): 
		return self.log(Log.TYPES['ERROR'], message)
	def drink(self, message, drink, amount):
		return self.log(Log.TYPES['DRINK'], message, drink, amount)
	def buy(self, message, drink, amount): 
		return self.log(Log.TYPES['BUY'], message, drink, amount)


if __name__ == "__main__":
	b = BaseClient(path='sqlite:///:memory:', debug=False)
	#~ b = BaseClient(debug=False)
	
	b.load_defaults()
	
	vodka_ingredient = Ingredient('Vodka', '082000727606', 1500, 1300, 500)
	b.try_add(vodka_ingredient)
	
	gin_ingredient = Ingredient('Gin', '082000727607', 1500, 0, 500)
	b.try_add(gin_ingredient)
	
	vodka_and_gin = ((vodka_ingredient.id, 100), (gin_ingredient.id, 100),)
	
	b.session.add(Drink('Vodka & Gin', json.dumps(vodka_and_gin)))
	
	b.session.commit()
	
	print b.debug("Testing our logging function.")
	print b.buy("Testing buying!", vodka_ingredient, 12345)
	
	print([i.name for i in b.get_ingredients()])
	print([i.name for i in b.get_popular_ingredients(5)])
	
	print([i.name for i in b.get_amounts()])
	print([i.name for i in b.get_popular_drink_amounts(5)])
	print([i.name for i in b.get_popular_buy_amounts(5)])
	


    

