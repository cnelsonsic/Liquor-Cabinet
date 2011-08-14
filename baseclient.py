'''This is the base classes that allow you to interface with all the innards of the beast.
''' 

import json
import os
import gzip
import datetime
from datetime import timedelta

import tables
from models import *
import defaults
from settings import *

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.sql import func
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
        self.DEBUG = debug
    
    def try_add(self, item):
        '''Tries to add an item into the database. 
        If it fails due to an IntegrityError, it returns False.
        Otherwise it returns True.
        '''
        try:
            self.session.add(item)
            self.session.commit()
            return True
        except(sqlalchemy.exc.IntegrityError, sqlalchemy.exc.FlushError),err:
            if self.DEBUG:
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
        
    def dump_to_disk(self, filename="database.py"):
        '''Writes the client's database information out to a plaintext python file.
        It writes it twice, once to confirm that there is enough space for the database file,
        and then again for the real file.'''
        
        try:
            with open(filename, "r") as f:
                data = f.read()
        except(IOError):
            data = ""
            
        fdata = ""
        fdata += "from models import *\n\n"
        fdata += "ITEMS = (\n"
        a = 0
        for j in (self.get_ingredients(), self.get_amounts(), self.session.query(Log).all()):
            for i in j:
                fdata += "\t"
                fdata += repr(i)
                fdata += ",\n"
                a += 1
            fdata += "\n"
        fdata += ")\n"
        
        try:
            file("test_diskspace_file.tmp", 'a').write(fdata+data)
            os.unlink("test_diskspace_file.tmp")
        except(IOError), err:
            raise err
        
        if data != fdata:
            if not os.path.exists(DATABASE_BACKUP_DIR):
                os.mkdir(DATABASE_BACKUP_DIR)
                
            date = datetime.datetime.now()
            gzfname = DATABASE_BACKUP_DIR+filename+date.strftime("%m-%d-%Y-%H-%M-%S")+".gz"
            g = gzip.GzipFile(gzfname, 'w')
            g.write(data)
            g.close()
            print "Wrote backup to %s, differed by %d bytes." % (gzfname, abs(len(fdata)-len(data)))
            
            with open(filename, "w") as f:
                f.write(fdata)
                
            print "Wrote %d bytes in %d items." % (len(fdata), a)
        else:
            print "Database data was the same, not saving. (%d, %d)" % (len(data), len(fdata))
            fdata = ""
            a = 0
        
        
        return len(fdata), a
    
    def import_dump(self, filename="database.py"):
        import imp
        if os.path.exists(filename):
            database = imp.load_source('baseclient', filename)
            a = 0
            for item in database.ITEMS:
                self.try_add(item)
                a += 1
            print "Imported %d items." % a
            return a
        else:
            print "Could not import the old database, no worries."
            return False
        
        
    def commit(self):
        return self.session.commit()
        
    def get_ingredients(self):
        q = self.session.query(Ingredient)
        q = q.order_by(Ingredient.hidden)
        q = q.all()
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
    
    def get_amount_by_size(self, size):
        q = self.session.query(Amount).filter(Amount.amount==size).all()[0]
        return q
    
    def get_popular_drink_amounts(self, limit):
        q = self.session.query(Amount).filter(Amount.times_drank > 0).order_by(Amount.amount).order_by(Amount.times_drank).limit(limit).all()
        return q
    
    def get_popular_buy_amounts(self, limit):
        q = self.session.query(Amount).filter(Amount.times_bought > 0).order_by(Amount.amount).order_by(Amount.times_bought).limit(limit).all()
        return q
    
    def get_common_drink_amounts(self, ingredient):
        '''Parses the log and gets the amounts for each drink and then 
        returns them sorted by the number of times they appear.
        '''
        
        q = self.session.query(Log)
        q = q.filter(Log.log_type == Log.TYPES['DRINK'])
        q = q.filter(Log.drink==ingredient.id)
        #q = q.order_by(Log.date.desc())
        #q = q.limit(limit)
        amts = q.all()
        
        named_amounts = [self.get_amount_by_size(a.amount) for a in amts]
        
        amnt_dict = {}
        for n in named_amounts:
            if n in amnt_dict:
                amnt_dict.update({n:amnt_dict[n]+1})
            else:
                amnt_dict.update({n:1})
        
        return amnt_dict
        
        
    def log(self, log_type, message, drink=None, amount=None, date=None):
        if drink is not None:
            drinkid = drink.id
        else:
            drinkid = None
        
        l = Log(log_type, drinkid, amount, message, date)
        print(repr(l))
        l = eval(repr(l))
        self.try_add(l)
        self.commit()
        
        if type(log_type) is int:
            log_type = [k for k, v in Log.TYPES.iteritems() if v == log_type][0]
        if amount is None:
            amount = 0
        retval = ("%s (%s): %s " % (log_type.ljust(8), str(l.date), message))
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
        drink.remove_inventory(amount)
        try:
            self.get_amount_by_size(amount).times_drank += 1
        except(IndexError):
            pass
        return self.log(Log.TYPES['DRINK'], message, drink, amount)
    
    def buy(self, message, drink, amount):
        drink.add_inventory(amount)
        try:
            self.get_amount_by_size(amount).times_bought += 1
        except(IndexError):
            pass
        return self.log(Log.TYPES['BUY'], message, drink, amount)
    
    def wakeup(self, message='', timestamp=None):
        return self.log(Log.TYPES['WAKEUP'], message, date=timestamp)

    def get_out_of_stock(self, only_used=False):
        '''Returns a list of Ingredients that are dangerously low, sorted by popularity.
        If `only_used` is set to True, only return Ingredients that have been used before.'''
        #Ingredients, that we've bought before
        #Where the amount is below its threshold
        #Sorted by the amount we've used (popularity)
        q = self.session.query(Ingredient)
        if only_used:
            q = q.filter(Ingredient.amount_used > 0)
        q = q.filter(Ingredient.threshold > 0)
        q = q.filter(Ingredient.current_amount <= Ingredient.threshold)
        q = q.filter(Ingredient.hidden == False)
        q = q.order_by(Ingredient.amount_used)
        q = q.all()
        
        return q
        
    def get_drinks_on_date(self, date):
		'''Gets all the drinks drunk on that date.'''
		q = self.session.query(Log).filter(Log.log_type == Log.TYPES['DRINK'])
		
		q = q.filter(func.strftime('%Y', Log.date) == "%04d"%date.year)
		q = q.filter(func.strftime('%m', Log.date) == "%02d"%date.month)
		q = q.filter(func.strftime('%d', Log.date) == "%02d"%date.day)
		q = q.order_by(Log.date.desc())
		drinks = q.all()
		return drinks
    
    def get_bac_simple(self, hours=24):
        '''Gets the user's estimated BAC, using a very simple formula, 
        and not taking into account, sex, weight or height.
        Uses the last `hours` worth of drinks.
        '''
        #FIXME: Thinks the user just drank all the drinks in the previous `hours` hours.
        #Perhaps iterate through all the drinks, sorted by date:
        #    Add their alcohol to the bac
        #    Remove the appropriate amount of BAC for each second between the last drink and the current drink.
        #    Max it at 0.
        
        tempbac = 0
        
        #Get all the drinks in the past 24 hours.
        drinks = []
        hoursdelta = timedelta(hours=hours)
        q = self.session.query(Log).filter(Log.log_type == Log.TYPES['DRINK'])
        q = q.filter(Log.date>(datetime.datetime.now()-hoursdelta)).order_by(Log.date.desc())
        drinks = q.all()
        
        if drinks == []:
            return 0
        
        dates = [d.date for d in drinks]
        dates.sort()
        #print dates
        
        seconds = (datetime.datetime.now()-drinks[0].date).seconds
        
        #22.5 mL of pure alcohol raises bac by 0.025
        #multiply potency by 100
        #multiply amount by potency
        #result is amount of pure alcohol.
        #Each mL of pure alcohol raises bac by 0.0011111
        bacperml = 0.025/22.5
        
        for i in drinks:
            #print i.date
            ingr = self.session.query(Ingredient).filter(Ingredient.id==int(i.drink)).all()[0]
            amtpurealc = (ingr.potency/100.0)*i.amount
            #Add them to the temporary bac
            tempbac += (amtpurealc*bacperml)
        
        #print "BAC before absorption: %.4f" % tempbac
        #remove 0.05 for every hour
        #or 0.05/60/60 for every second.
        absorpsec = 0.05/60.0/60.0
        #print "Absorbed %f" % (absorpsec*seconds)
        tempbac -= (absorpsec*seconds)
        #print "Final BAC is %.4f" % tempbac
        return max(0, tempbac)

    def get_latest_wakeup(self):
        q = self.session.query(Log).filter(Log.log_type==Log.TYPES['WAKEUP'])
        q = q.filter(Log.date>(datetime.datetime.now()-datetime.timedelta(hours=24)))
        q = q.order_by(Log.date).first()
        
        if q is None:
            q = datetime.datetime.now()
        else:
            q = q.date
            
        return q
        
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
    
    gin_ingredient.amount_used = 10
    b.commit()
    
    print gin_ingredient
    print b.get_amounts()[0]
    
    print([i.name for i in b.get_out_of_stock()])
    
    b.dump_to_disk()
    b = BaseClient(path='sqlite:///:memory:', debug=False)
    b.import_dump()
    
    import time, random
    for i in xrange(10):
        b.drink("", vodka_ingredient, 45)
        #time.sleep(random.random())
    print b.get_bac_simple()
    
    b.wakeup()
    print b.get_latest_wakeup()

    print b.get_common_drink_amounts(vodka_ingredient)

    
