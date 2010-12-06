#!/usr/bin/env python

import sys
import os
import functools
import time, datetime
import random
import signal
import json

from Cheetah.Template import Template

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QUrl, QTimer, Qt
from PyQt4.QtGui import QPrintPreviewDialog, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QDoubleSpinBox, QTreeWidgetItem
from PyQt4.QtCore import SIGNAL, SLOT
import PyQt4.QtWebKit as QtWebKit

import baseclient, models
from settings import *

from graph_interpolation import extrapolate_to_y_zero_linear

#TODO:
#Ingredient adding/modification interface, simple form. 
    #A lock thing that warns about how they're editing data for the whole object?
#Charts that graph drinking of an ingredient over time.
    #Allow multiple selections
    #Export to CSV for graphing in external applications
    

class HTMLPrinter(QtWebKit.QWebView):
    def __init__(self, html="", parent=None):
        QtWebKit.QWebView.__init__(self, parent)
        self.setHtml(html, QtCore.QUrl("qrc://"))
        
        path = os.getcwd()
        self.settings().setUserStyleSheetUrl(QUrl.fromLocalFile(path+RESOURCES_DIR+"/style.css"))
        
        self.preview = QPrintPreviewDialog()
        self.connect(self.preview, SIGNAL("paintRequested (QPrinter *)"), SLOT("print (QPrinter *)"))
        self.connect(self, SIGNAL("loadFinished (bool)"), self.do_print)
            
    def do_print(self, arg):
        self.preview.exec_()
        
class GraphViewer(QtWebKit.QWebView):
    '''This shows an interable's data as a gRaphael svg element.
    Pass a list or tuple as x and y to graph those points.
    Past a list or tuple of tuples or lists to x and y and it 
    will graph multiple lines!
    
    >>> GraphViewer((1, 2, 3), (4,5,6))
    
    >>> GraphViewer(((1,2,3), (7,8,9)), ((4,5,6), (2,5,8)))
    ''' 
    
    def __init__(self, x, y, parent=None):
        QtWebKit.QWebView.__init__(self, parent)
        self.x = x
        self.y = y
        
        self.connect(self, SIGNAL("loadFinished (bool)"), self.do_graph)
        
        path = os.getcwd()
        self.load(QUrl.fromLocalFile(path+RESOURCES_DIR+"/graphael_test.html"))
        
    def do_graph(self, x=None, y=None):
        if x is None:
            x = self.x
        if y is None:
            y = self.y
                
        frame = self.page().mainFrame() 
        
        x = json.dumps(x)
        y = json.dumps(y)
        print x, y
        frame.evaluateJavaScript("if(ready == true) {generate_graph(%s, %s);}" % (x, y))

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
        
        self.given_parent = parent
        
        self.wakeup_time = None
        
        self.menu = None
        self._regenerate_menus(parent)
    
    def _regenerate_menus(self, parent=None):
        '''This should be called when you want to re-generate the right click menu.'''
        
        try:
            self.menu.deleteLater()
        except(AttributeError):
            pass
        
        if parent is None:
            parent = self.given_parent
        
        self.menu = QtGui.QMenu(parent)
        
        exitAction = self.menu.addAction("Exit")
        self.connect(exitAction, QtCore.SIGNAL('triggered()'), app.exit)
        
        self.menu.addSeparator()
        
        self._init_time(self.menu)
        
        self.menu.addSeparator()
        
        self._init_new(self.menu)
        self._init_inventory(self.menu)
        
        self.setContextMenu(self.menu)
        
    def _init_time(self, menu):
        if self.wakeup_time == None:
            #If our wakeup time is not set, just set it to when when we start the program.
            self.wakeup_time = datetime.datetime.now()
            
        drinktime = self.wakeup_time+datetime.timedelta(hours=DRUNK_BEFORE_NOON)
        timeMenu = menu.addMenu("You can drink after %s" % drinktime.strftime("%X"))
        wakeUp = timeMenu.addAction("I just woke up.")
        self.connect(wakeUp, QtCore.SIGNAL('triggered()'), functools.partial(self.do_time_now)) 
        
        wakeUpPast = timeMenu.addAction("I woke up earlier...")
        self.connect(wakeUpPast, QtCore.SIGNAL('triggered()'), self.do_time_query)
        
        self.timeMenu = timeMenu
        
    def _init_new(self, menu):
        newMenu = menu.addMenu("New")
        
        newIngredient = newMenu.addAction("Ingredient")
        self.connect(newIngredient, QtCore.SIGNAL('triggered()'), self.do_new_ingredient)
        
        newDrink = newMenu.addAction("Drink")
        self.connect(newDrink, QtCore.SIGNAL('triggered()'), self.do_new_drink)
        self.newMenu = newMenu
        
    def _init_inventory(self, menu):
        #Inventory 

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
        
        self._regenerate_menus()
        
        self.showMessage("Inventory Added", "Added %s of %s to your stores." % (amount.name, ingredient.name))
        
    def do_drink(self, ingredient, amount):
        ingredient.remove_inventory(amount.amount)
        client.commit()
        print client.drink("", ingredient, amount.amount)
        
        self._regenerate_menus()
        
        self.showMessage("Inventory Removed", "Removed %s of %s from your stores." % (amount.name, ingredient.name))

    def do_time_now(self):
        print client.wakeup(message="Woke up very recently.")
        self.wakeup_time = datetime.datetime.now()
        self._regenerate_menus()
        
    def do_time_given(self, t):
        print client.wakeup(message="Woke up a while ago.", timestamp=t) #Log our wakeup
        self.wakeup_time = t
        self._regenerate_menus()
        
    def do_time_query(self):
        #If timestamp is True, use now as the time.
        #If timestamp is None, show a window and ask the user for when they woke up
        #Then call this function again with the time.
        w = QtGui.QWidget()
        dialog = TimeSetDialog(w)
        dialog.exec_()
        if dialog.result() == 1:
            self.do_time_given(dialog.get_time())
            
class TimeSetDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
            
        self.layout=QVBoxLayout(self)
        
        dnow = datetime.datetime.now()
        now = QtCore.QTime(dnow.hour, dnow.minute)
        self.timeEdit = QtGui.QTimeEdit(now)
        self.layout.addWidget(self.timeEdit)
        
        hlayout = QHBoxLayout()
        self.layout.addLayout(hlayout)
        
        self.OK = QPushButton("OK")
        self.connect(self.OK, SIGNAL("clicked()"), self.accept)
        hlayout.addWidget(self.OK)
        
        self.Cancel = QPushButton("Cancel")
        self.connect(self.Cancel, SIGNAL("clicked()"), self.reject)
        hlayout.addWidget(self.Cancel)
        
        

        
    def get_time(self):
        d = datetime.datetime.now()
        t = self.timeEdit.time().toPyTime()
        return d.replace(hour=t.hour, minute=t.minute)

class MainWindow(QtGui.QWidget):
    def __init__(self, win_parent = None):
        #Init the base class
        QtGui.QWidget.__init__(self, win_parent)
        
        traySignal = "activated(QSystemTrayIcon::ActivationReason)"
        global trayIcon
        QtCore.QObject.connect(trayIcon, QtCore.SIGNAL(traySignal), self.__icon_activated)
        
        self.okayToClose = False
        
        self.create_widgets()
    
    def closeEvent(self, event):
        if self.okayToClose: 
            #user asked for exit
            event.accept()
        else:
            #"minimize"
            self.hide()
            event.ignore()
    
    def __icon_activated(self, reason):
        if reason in (QtGui.QSystemTrayIcon.Trigger, QtGui.QSystemTrayIcon.DoubleClick):
            if self.isVisible():
                self.hide()
            elif not self.isVisible():
                self.show()

    def create_widgets(self):
        h_box = QtGui.QHBoxLayout()
        self.setLayout(h_box)
        
        self.tabs = QtGui.QTabWidget()
        self.tabs.setUsesScrollButtons(False)
        h_box.addWidget(self.tabs)
        
        #Some quick statistics in large font: (Current estimated BAC, other stats.  
        #warnings about things that are due to go out of stock
        self.homepage = QtGui.QWidget()
        self.homepage.setLayout(QtGui.QHBoxLayout())
        self.tabs.addTab(self.homepage, "Home")
        
        #The IngredientsEditor widget
        self.ingredients_tab = QtGui.QWidget()
        self.ingredients_tab.setLayout(QtGui.QHBoxLayout())
        self.tabs.addTab(self.ingredients_tab, "Ingredients")
        
        #The StatisticsViewer widget
        self.statistics = QtGui.QWidget()
        self.statistics.setLayout(QtGui.QHBoxLayout())
        self.tabs.addTab(self.statistics, "Statistics")

        
        
        
        '''#Build our main window:
            #Build our ingredient adding/modification interface
            #Build Statistics page
                #Show popular ingredient inventory amount over time graph
                #Show amount drank over time graph for each ingredient
                #BAC over time.
                #When can we drink according to social standards
            #Build Inventory management page
                #List our available ingredients, double click to edit the Ingredient itself
                #Show non-editable info and a dropdown of volumes 
                '''

class ShoppingList(QtGui.QWidget):
    '''This widget looks at the current inventory and displays a list of Ingredients
    that are currently out of stock.
    Columns:
        Checkbox, Name, Current Amount, Amount Used
    '''
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        
        self.tree = QtGui.QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels((u"\u2611", "Name", "Current Amount", "Amount Used"))
        
        items = list()
        emptybox = QtCore.QString(u"\u2610")
        data = None
        for ingr in client.get_out_of_stock():
            item = QTreeWidgetItem(self.tree)
            data = (emptybox, ingr.name, str(int(ingr.current_amount))+"mL", str(int(ingr.amount_used))+"mL")
            for t in enumerate(data):
                item.setText(t[0], t[1])
            items.append(item)
        self.tree.insertTopLevelItems(0, items)
        
        if data:
            for i in xrange(len(data)):
                self.tree.resizeColumnToContents(i)
            
        self.print_button = QtGui.QPushButton("Print Shopping List")
        self.connect(self.print_button, SIGNAL("clicked()"), self.print_html)
        
        h_box = QtGui.QVBoxLayout()
        h_box.addWidget(self.tree)
        h_box.addWidget(self.print_button)
        self.setLayout(h_box)
        
        s = self.tree.frameSize()
        g = self.frameGeometry()
        self.setGeometry(g.x(), g.y(), s.width()/1.5, s.height()/1.5)
        
    def print_html(self):
        rows = []
        for ingr in client.get_out_of_stock():
            data = (ingr.name, str(int(ingr.current_amount))+"mL", str(int(ingr.amount_used))+"mL")
            rows.append(data)
        
        data = {'date':datetime.datetime.now().strftime("%x"), 'ingredients':rows}
        t = Template(file=TEMPLATE_DIR+"shopping_list.tmpl", searchList=[data])
        
        self.h = HTMLPrinter(html=str(t))
        #self.h.show()
        self.h.do_print(True)
           
class PsychicShoppingList(ShoppingList):
    '''This widget looks like the ShoppingList widget, but uses 
    the previous logs to predict when the user will be out of booze.
    It takes into account drinking schedules and sorts by which 
    will be out of stock soonest.
    '''

class IngredientEditorPane(QtGui.QWidget):
    '''Shows a form for filling out information about Ingredients.'''
    def __init__(self, ingredient, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        self.ingredient = ingredient
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        formlayout = QtGui.QFormLayout()
        layout.addLayout(formlayout)
        
        layout.addWidget(QLabel("Changes to Current Amount \nwill not be reflected in graphs."))
        
        self.inputs = {}
        
        self.fields = ('name', 'barcode', 'size', 'current_amount', 'threshold', 'note')
        
        for a in self.fields:
            value = getattr(ingredient, a)
            vt = type(value)
            if vt in (str, unicode):
                i = QLineEdit(text=value)
            elif vt in (int, float, long):
                i = QDoubleSpinBox()
                i.setDecimals(0)
                i.setRange(0, 10000)
                i.setSuffix(" mL")
                i.setValue(value)
            
            label = a.replace("_", " ").title()+":"
            formlayout.addRow(label, i)
            
            self.inputs.update({a:i})
            
        save = QPushButton("Save")
        save.connect(save, SIGNAL("clicked()"), self.save_data)
        layout.addWidget(save)
    
    def save_data(self):
        for k in self.inputs:
            v = self.inputs[k]
            l = k
            i = v
            
            value = None
            
            try:
                value = int(i.value())
            except(AttributeError):
                try:
                    value = str(i.text())
                except(AttributeError):
                    pass
            
            if value is not None:
                label = l.replace(":", "").replace(' ', "_").lower()
                setattr(self.ingredient, label, value)
                
        client.commit()
        client.dump_to_disk()
        
class IngredientViewerPane(QtGui.QWidget):
    '''Shows a set of labels populated with information about Ingredients.'''
    def __init__(self, ingredient, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ingredient = ingredient
        
class IngredientsEditor(QtGui.QWidget):
    '''Shows a list of Ingredients and an IngredientEditorPane when one is selected.'''
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    global app
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("Liquor Cabinet")
    
    if not NOSPLASH:
        pixmap = QtGui.QPixmap("resources/splashscreen.png")
        splash = QtGui.QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    
        #~ splash.setMask(pixmap.mask())
        splash.show()
        splash.showMessage(u'Starting...', Qt.AlignVCenter | Qt.AlignBottom)
        time.sleep(SPLASH_MESSAGE_DELAY)
    
    #Load our database...
    global client
    client = baseclient.BaseClient(DATABASE_PATH, DEBUG)
    
    if not NOSPLASH:
        splash.showMessage(u'Loading database...', Qt.AlignVCenter | Qt.AlignBottom)
        time.sleep(SPLASH_MESSAGE_DELAY)
    
    
    client.import_dump()
    client.load_defaults()
    
    if not NOSPLASH:
        splash.showMessage(u'Populating Menus...', Qt.AlignVCenter | Qt.AlignBottom)
        time.sleep(SPLASH_MESSAGE_DELAY)

    app.processEvents()

    w = QtGui.QWidget()
    
    appIcon = QtGui.QIcon(TRAY_ICON)
    app.setWindowIcon(appIcon)
    
    global trayIcon
    trayIcon = SystemTrayIcon(appIcon, w)
    trayIcon.show()
    
    #Do our main window.
    mainwindow = MainWindow()
    
    if not NOSPLASH:
        splash.showMessage(u'Building Main Window...', Qt.AlignVCenter | Qt.AlignBottom)
    
        for m in random.sample(LOADING_MESSAGES, len(LOADING_MESSAGES)):
            splash.showMessage(m, Qt.AlignVCenter | Qt.AlignBottom)
            if SPLASH_MESSAGE_DELAY is 0:
                s = 0
            else:
                s = abs(SPLASH_MESSAGE_DELAY-(random.random()/2.0))
            time.sleep(s)
    
        splash.finish(w)
    
    mainwindow.show()
    
    #slist = ShoppingList()
    #slist.show()
    
    #ied = IngredientsEditor()
    #ied.show()
    
    print("There is now a red and white potion bottle in your system tray. That's where all your icons go. Click to get a window, right click to get a menu.")
    print("CTRL+C will exit the program, but will not save data automatically. Closing from the program will save your data automatically.")

    app.setQuitOnLastWindowClosed(False)
    
    savetimer = QTimer()
    savetimer.connect(savetimer, SIGNAL("timeout()"), functools.partial(client.dump_to_disk))
    
    length = 0
    for i in (client.get_ingredients(), client.get_amounts(), client.session.query(models.Log).all()):
        length += len(i)
    delaymod = length/100.0
        
    savetimer.start(WRITE_DATA_DELAY*delaymod)
    print "Automatically saving every %.2f minutes" % (((((WRITE_DATA_DELAY*delaymod)/1000.0)/60.0)))

    rval = app.exec_()
    
    client.dump_to_disk()
    
    sys.exit(rval)

if __name__ == '__main__':
    main()
