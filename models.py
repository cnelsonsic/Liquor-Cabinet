'''Declares all our models and classes that we'll be using.'''

#TODO: JSON export so we can backup before upgrading to a new version?

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy import ForeignKey

import datetime
import time

#TODO: Consider adding "categories" to ingredients so we can put 
    #"Smirnoff Vodka" and "Heaven Hill Vodka" in the "Vodka" category.
    #This would make a great way to add submenus to the ingredient menu.

class Ingredient(Base):
    __tablename__ = 'ingredients'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    barcode = Column(String)

    #Size, Current Amount, and Threshold should be in Milliliters
    size = Column(Float)
    current_amount = Column(Float)
    threshold = Column(Float)
    potency = Column(Float) #Percent alcahol
    note = Column(String)
    amount_used = Column(Float)
    hidden = Column(Boolean)

    def __init__(self, name, barcode, size, current_amount=0, threshold=-1, 
                 note="", amount_used=0, potency=5.0, id=None, hidden=False):
        if id is not None:
            self.id = id
        self.name = name
        self.barcode = barcode
        
        #Size, Current Amount, and Threshold should be in Milliliters
        self.size = size 
        self.current_amount = current_amount
        self.threshold = threshold
        self.note = note
        self.amount_used = amount_used
        self.potency = potency
        self.hidden = hidden
        
        #If no threshold is set, warn if it drops below 1/4th of its size.
        if threshold == -1:
            self.threshold = size/4.0

    def __repr__(self):
        return "Ingredient(name=%s, barcode=%s, size=%d, current_amount=%d, threshold=%d, \
note=%s, amount_used=%d, potency=%d, id=%d, hidden=%s)" % (repr(self.name), 
                                    repr(self.barcode), 
                                    self.size, 
                                    self.current_amount, 
                                    self.threshold, 
                                    repr(self.note), 
                                    self.amount_used, 
                                    self.potency,
                                    self.id,
                                    self.hidden)
        
    def add_inventory(self, amount):
        self.current_amount += amount
        
    def remove_inventory(self, amount):
        self.current_amount = max(0, self.current_amount-amount)
        self.amount_used += max(0, self.current_amount-amount)

class Drink(Base):
    __tablename__ = "drinks"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    amount_used = Column(Float)
    
    #A JSON dict of ingredients like so:
    #{[[1,100], [2,150]]}
    #This would be 100ml of ingredient with id 1 and 150ml of ingredient with id 2
    ingredients = Column(String) 
    
    #ingredients = relation('Ingredient', secondary=tables.drink_contents_table, backref='drinks')

    def __init__(self, name, ingredients):
        self.name = name
        self.ingredients = ingredients
        
class Amount(Base):
    '''This table lets you look up various measurements for their mililiter values.'''
    __tablename__ = "amounts"
    
    FOR_DRINKING = 1
    FOR_BUYING = 2
    FOR_BOTH = 3
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    amount = Column(Float) #the amount in mililiters.
    times_bought = Column(Integer, default=0) #The times it's been drank. Drink a lot of shots? Shots show up as a favorite.
    times_drank = Column(Integer, default=0) #The times it's been bought. Buy a lot of handles? Handles show up as favorite.
    use = Column(Integer) 
    
    def __init__(self, name, amount, use=3, times_bought=0, times_drank=0, id=None):
        if id is None:
            self.id = id
            
        self.name = name
        self.amount = amount
        self.use = use
        self.times_bought = times_bought
        self.times_drank = times_drank
    
    def __repr__(self):
        return "Amount(name=%s, amount=%d, use=%d, times_bought=%d, times_drank=%d, id=%d)" % (
                repr(self.name),
                self.amount,
                self.use,
                self.times_bought,
                self.times_drank,
                self.id,
                )
        
class Log(Base):
    '''Log times drinking and what and how much.'''
    __tablename__ = "log"
    
    #Log_type Enum:
    TYPES = {
        'DEBUG': 0,
        'INFO': 1,
        'WARNING': 2,
        'ERROR': 3,
        'DRINK': 4,
        'BUY': 5,
        'WAKEUP': 6,
        }
    
    id = Column(Integer, primary_key=True)
    log_type = Column(Integer)
    drink = Column(Integer, ForeignKey('ingredients.id'))
    amount = Column(Float)
    message = Column(String)
    date = Column(DateTime, default=datetime.datetime.now())
    
    def __init__(self, log_type, drink, amount, message, date=None):
        if type(log_type) is str:
            log_type = self.TYPES[log_type]
        self.log_type = log_type
        
        self.drink = drink
        self.amount = amount
        self.message = message
        
        if date is None:
            self.date = datetime.datetime.now()
        elif type(date) in (int, float):
            self.date = datetime.datetime.fromtimestamp(date)
        else:
            self.date = date
            
    def __repr__(self):
        return "Log(log_type=%d, drink=%s, amount=%s, message=%s, date=%d)" % (self.log_type, str(self.drink), str(self.amount), repr(self.message), int(time.mktime(self.date.timetuple())))






