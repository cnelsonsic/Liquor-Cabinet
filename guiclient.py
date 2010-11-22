import sys
import functools

from PyQt4 import QtGui, QtCore

import baseclient, models
from settings import *

class SystemTrayIcon(QtGui.QSystemTrayIcon):
    '''System Tray Right-Click menu will look like:
        Exit
        ----
        New>
            Ingredient
            Drink
        Inventory>
            Vodka>
                Buy
                Drink
        ----
        Vodka>
            Buy
            Drink
    '''
    def __init__(self, icon, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, icon, parent)
        menu = QtGui.QMenu(parent)
        
        exitAction = menu.addAction("Exit")
        self.connect(exitAction, QtCore.SIGNAL('triggered()'), app.exit)
        
        menu.addSeparator()
        
        self._init_new(menu)
        self._init_inventory(menu)
        
        self.setContextMenu(menu)
        self.menu = menu
        
    def _init_new(self, menu):
        newMenu = menu.addMenu("New")
        
        newIngredient = newMenu.addAction("Ingredient")
        self.connect(newIngredient, QtCore.SIGNAL('triggered()'), self.do_new_ingredient)
        
        newDrink = newMenu.addAction("Drink")
        self.connect(newDrink, QtCore.SIGNAL('triggered()'), self.do_new_drink)
        
    def _init_inventory(self, menu):
        #Inventory 
        try:
            self.inventoryMenu.deleteLater()
        except(AttributeError):
            pass
            
        inventoryMenu = menu.addMenu("Inventory")
        
        #Add all our known ingredients
        instock_ingredients = client.get_ingredients_in_stock()
        self.ingredient_menus = {}
        for i in client.get_ingredients():
            tmpmenu = inventoryMenu.addMenu(i.name+" (%dmL)" % i.current_amount)
            #And now the two menus per ingredient.
            
            #First the BUY menu:
            tmpbuy = tmpmenu.addMenu("Buy")
            
            for amt in client.get_popular_buy_amounts(5):
                tmpamt = tmpbuy.addAction(amt.name)
                self.connect(tmpamt, QtCore.SIGNAL('activated()'), 
                    functools.partial(self.do_buy, i, amt))
                    
            tmpbuy.addSeparator()
            
            amounts = [a for a in client.get_amounts()]
            amounts.reverse()
            for amt in amounts:
                tmpamt = tmpbuy.addAction(amt.name)
                self.connect(tmpamt, QtCore.SIGNAL('activated()'), 
                    functools.partial(self.do_buy, i, amt))
            
            #Now the DRINK menu:
            if(i in instock_ingredients): #If we dont have any in stock, dont offer to drink it.
                tmpdrink = tmpmenu.addMenu("Drink")
                
                for amt in client.get_popular_drink_amounts(5):
                    tmpamt = tmpbuy.addAction(amt.name)
                    self.connect(tmpamt, QtCore.SIGNAL('activated()'), 
                        functools.partial(self.do_drink, i, amt))
                        
                tmpdrink.addSeparator()
                
                for amt in client.get_amounts():
                    if amt.amount <= i.current_amount:
                        tmpamt = tmpdrink.addAction(amt.name)
                        self.connect(tmpamt, QtCore.SIGNAL('activated()'), 
                            functools.partial(self.do_drink, i, amt))
                
                #TODO: Half, Quarter, Eighth of store
                
                #Rest of the bottle
                a = models.Amount(name="All", amount=i.current_amount)
                tmpamt = tmpdrink.addAction(a.name)
                self.connect(tmpamt, QtCore.SIGNAL('activated()'), 
                    functools.partial(self.do_drink, i, a))
            
            self.ingredient_menus[i.name] = tmpmenu
        
        menu.addSeparator()
        
        #Favorite/Popular Ingredients
        for i in client.get_popular_ingredients(5):
            menu.addMenu(self.ingredient_menus[i.name])
            
        self.inventoryMenu = inventoryMenu
        
        
        
    def do_print(self, value):
        print(value)
        
    def do_new_ingredient(self):
        self.showMessage("Not Implemented", "Adding ingredients arent supported yet. Edit defaults.py with a text editor to add new ingredients until then.")
        print("New Ingredient")
        
    def do_new_drink(self):
        self.showMessage("Not Implemented", "Adding drinks arent supported yet.")
        print("New Drink")
        
    def do_buy(self, ingredient, amount):
        ingredient.add_inventory(amount.amount)
        client.commit()
        print client.buy("", ingredient, amount.amount)
        
        self._init_inventory(self.menu)
        
        self.showMessage("Inventory Added", "Added %s of %s to your stores." % (amount.name, ingredient.name))
        
        
    def do_drink(self, ingredient, amount):
        ingredient.remove_inventory(amount.amount)
        client.commit()
        print client.drink("", ingredient, amount.amount)
        
        self._init_inventory(self.menu)
        
        self.showMessage("Inventory Removed", "Removed %s of %s from your stores." % (amount.name, ingredient.name))
        


def main():
    global client
    client = baseclient.BaseClient(DATABASE_PATH, DEBUG)
    client.load_defaults()
    
    global app
    app = QtGui.QApplication(sys.argv)

    w = QtGui.QWidget()
    trayIcon = SystemTrayIcon(QtGui.QIcon(TRAY_ICON), w)

    trayIcon.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
