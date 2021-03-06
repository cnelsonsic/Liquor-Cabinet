#!/usr/bin/env python

import sys
import os
import functools
import time, datetime
import random
import signal
import json
import platform

from Cheetah.Template import Template

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import SIGNAL, SLOT
from PyQt4.QtCore import QUrl, QTimer, Qt
from PyQt4.QtGui import (QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                         QLineEdit, QDoubleSpinBox, QTreeWidgetItem)
import PyQt4.QtWebKit as QtWebKit

import baseclient, models
from settings import *

from graph_interpolation import extrapolate_to_y_zero_linear

#TODO:
#Charts that graph drinking of an ingredient over time.
    #Allow multiple selections
    #Export to CSV for graphing in external applications


class HTMLPrinter(QtWebKit.QWebView):
    '''HTMLPrinter is a handy widget that prints whatever `html` given.
    It applies the stylesheet named 'style.css' in the liquor cabinet 
    resources directory.
    When finished loading, it will show a QPrintPreviewDialog. 
    ''' 
    def __init__(self, html="", parent=None):
        QtWebKit.QWebView.__init__(self, parent)
        self.setHtml(html, QtCore.QUrl("qrc://"))
        
        path = os.getcwd()
        self.settings().setUserStyleSheetUrl(QUrl.fromLocalFile(path+"/"+RESOURCES_DIR+"style.css"))
        
        self.preview = QtGui.QPrintPreviewDialog()
        self.connect(self.preview, SIGNAL("paintRequested (QPrinter *)"), SLOT("print (QPrinter *)"))
        self.connect(self, SIGNAL("loadFinished (bool)"), self.do_print)
            
    def do_print(self, arg):
        self.preview.exec_()
        
class GraphViewer(QtWebKit.QWebView):
    '''This shows an iterable's data as a gRaphael svg element.
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
    '''SystemTrayIcon is a quick-access method of entering small 
    amounts of drinking/purchasing data.
    Left-Clicking this icon in the system tray will hide or show
    the MainWindow. 
    Right-clicking will show a context menu.
    
    There is a 'time until drinking is socially acceptible' timer as well,
    which, given the time you woke up that day can calculate when it is
    socially acceptable to begin drinking.
    Remember, if you're watching the clock for when you can drink,
    you may need to seek help with your addiction.
    
    The context menu will resemble:
        Exit
        ----
        You can drink after XX:XX:XX PM>
            I just woke up.
            I woke up earlier...
        ----
        New>
            Ingredient
            Drink
        ----
        Inventory>
            Vodka>
                Buy
                Drink
        Drink>
            Vodka Neat>
                Buy
                Drink
        ----
        Vodka>
            Buy
            Drink
        ----
        Vodka Neat>
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
            self.menu.clear()
            self.menu.deleteLater()
        except(AttributeError):
            pass
        
        if parent is None:
            parent = self.given_parent
        
        self.menu = QtGui.QMenu(parent)
            
        funcs = [
                functools.partial(self._init_exit),
                functools.partial(self.menu.addSeparator),
                functools.partial(self._init_time, self.menu),
                functools.partial(self.menu.addSeparator),
                functools.partial(self._init_new, self.menu),
                functools.partial(self._init_inventory, self.menu),
                ]

        for f in funcs:
            f()
        
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
        
    def _init_exit(self):
        self.exitAction = self.menu.addAction("Exit")
        self.connect(self.exitAction, QtCore.SIGNAL('triggered()'), app.exit)
        
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
                tmpamt.triggered.connect(functools.partial(self.do_buy, i, amt))
                    
            tmpbuy.addSeparator()
            
            amounts = [a for a in client.get_amounts()]
            amounts.reverse()
            for amt in amounts:
                tmpamt = tmpbuy.addAction(amt.name)
                tmpamt.triggered.connect(functools.partial(self.do_buy, i, amt))
            
            #Now the DRINK menu:
            if(i in instock_ingredients): #If we dont have any in stock, dont offer to drink it.
                tmpdrink = tmpmenu.addMenu("Drink")
                
                for amt in client.get_popular_drink_amounts(5):
                    tmpamt = tmpdrink.addAction(amt.name)
                    tmpamt.triggered.connect(functools.partial(self.do_drink, i, amt))
                        
                tmpdrink.addSeparator()
                
                for amt in client.get_amounts():
                    if amt.amount <= i.current_amount:
                        tmpamt = tmpdrink.addAction(amt.name)
                        tmpamt.triggered.connect(functools.partial(self.do_drink, i, amt))
                
                #TODO: Half, Quarter, Eighth of store
                
                #Rest of the bottle
                a = models.Amount(name="All", amount=i.current_amount)
                tmpamt = tmpdrink.addAction(a.name)
                self.connect(tmpamt, QtCore.SIGNAL('activated()'), 
                    functools.partial(self.do_drink, i, a))
            
            self.ingredient_menus[i.name] = tmpmenu
        
        menu.addSeparator()
        
        #Favorite/Popular Ingredients
        #TODO: Move into its own function so we can reorder it.
        for i in client.get_popular_ingredients(5):
            menu.addMenu(self.ingredient_menus[i.name])
        
        self.inventoryMenu = inventoryMenu
        
    def do_print(self, value):
        print(value)
        
    def do_new_ingredient(self):
        LCSIGNAL.doNewIngredient.emit()
        print("New Ingredient")
        
    def do_new_drink(self):
        self.showMessage("Not Implemented", "Adding drinks arent supported yet, sorry :(")
        LCSIGNAL.doNewDrink.emit()
        print("New Drink")
        
    def do_buy(self, ingredient, amount):
        print client.buy("", ingredient, amount.amount)
        LCSIGNAL.doBuyAction.emit()
        
        self._regenerate_menus()
        
        self.showMessage("Inventory Added", "Added %s of %s to your stores." % (amount.name, ingredient.name))
        
    def do_drink(self, ingredient, amount):
        print client.drink("", ingredient, amount.amount)
        LCSIGNAL.doDrinkAction.emit()
        
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
        w = QtGui.QWidget()
        dialog = TimeSetDialog(w)
        dialog.exec_()
        if dialog.result() == 1:
            self.do_time_given(dialog.get_time())
            
class TimeSetDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
            
        self.layout=QVBoxLayout(self)
        
        #TODO: Convert this from QTimeEdit to QDateTimeEdit
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
        self.tree.setHeaderLabels((u"\u2611", "Name", "Current Amount", "Amount Used", "Barcode"))
            
        self.print_button = QtGui.QPushButton("Print Shopping List")
        self.connect(self.print_button, SIGNAL("clicked()"), self.print_html)
        
        h_box = QtGui.QVBoxLayout()
        h_box.addWidget(self.tree)
        h_box.addWidget(self.print_button)
        self.setLayout(h_box)
        
        s = self.tree.frameSize()
        g = self.frameGeometry()
        self.setGeometry(g.x(), g.y(), s.width()/1.5, s.height()/1.5)
        
        for a in (LCSIGNAL.doBuyAction, LCSIGNAL.doDrinkAction):
            a.connect(self.showEvent)
        
        self.showEvent(None)
        
    def print_html(self):
        rows = []
        for ingr in client.get_out_of_stock():
            data = (ingr.name, str(int(ingr.current_amount))+"mL", str(int(ingr.amount_used))+"mL", ingr.barcode)
            rows.append(data)
        
        headings = ["Name", "Current Amount", "Amount Used", "Barcode"]
        
        data = {'date':datetime.datetime.now().strftime("%x"), 'ingredients':rows, 'headings':headings}
        t = Template(file=TEMPLATE_DIR+"shopping_list.tmpl", searchList=[data])
        
        self.h = HTMLPrinter(html=str(t))
        #self.h.show()
        self.h.do_print(True)
        
    def showEvent(self, ev=None):
        self.tree.clear()
        
        items = list()
        emptybox = QtCore.QString(u"\u2610")
        data = None
        for ingr in client.get_out_of_stock():
            item = QTreeWidgetItem(self.tree)
            data = (emptybox, ingr.name, str(int(ingr.current_amount))+"mL", str(int(ingr.amount_used))+"mL", ingr.barcode)
            for t in enumerate(data):
                item.setText(t[0], t[1])
            items.append(item)
        self.tree.insertTopLevelItems(0, items)
        
        if data:
            for i in xrange(len(data)):
                self.tree.resizeColumnToContents(i)
        
        if ev is not None:
            ev.accept()
           
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
        
        self.fields = ('name', 'barcode', 'size', 'current_amount', 'threshold', 'potency', 'note', 'hidden')
        
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
                
            if a == "potency":
                i.setDecimals(2)
                i.setSuffix("%")
                
            if a == "hidden":
                i = QtGui.QCheckBox("Hidden from shopping list")
                i.setChecked(value)
            
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
            
            try:
                value = i.isChecked()
            except(AttributeError):
                pass
            
            if value is not None:
                label = l.replace(":", "").replace(' ', "_").lower()
                setattr(self.ingredient, label, value)
                
        client.commit()
        client.dump_to_disk()
        
        try:
            trayIcon._regenerate_menus()
        except:
            pass
        
class BottleFullnessGuage(QtGui.QGraphicsView):
    '''Draw a thermometer style image that shows the level of a statistic
    as a wavy filled bar at `level`, based on how large `maximum` is,
    with a second marker that displays a caution type image.'''
    #TODO: Reimplement as a QWidget with paintEvent for speed and/or simplicity and/or scalability.
    def __init__(self, maximum=100, level=50, warn=25, suffix=" mL", parent=None):
        QtGui.QGraphicsView.__init__(self, parent)
        
        self.maximum = maximum
        self.level = level
        self.warn = warn
        
        self.setFixedSize(QtCore.QSize(256, 256))
        #self.resize(256, 256)
        
        self.scene = QtGui.QGraphicsScene()
        self.setScene(self.scene)
        
        self.setInteractive(False)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        path = os.getcwd()+"/"+RESOURCES_DIR
        
        liquid = QtGui.QPixmap(path+"liquid.png")
        caution = QtGui.QPixmap(path+"caution.png")
        bottle = QtGui.QPixmap(path+"bottle_transparent_big.png")
        
        self.liquid = self.scene.addPixmap(liquid)
        self.caution = self.scene.addPixmap(caution)
        self.bottle = self.scene.addPixmap(bottle)
        self.imagemap = {self.liquid:liquid, self.caution:caution, self.bottle:bottle}
        
        self.warntext = self.scene.addText('')
        if level > warn:
            self.warntext.setHtml("<b>%s</b>" % "Notify at: %d%s"%(warn, suffix))
        
        self.leveltext = self.scene.addText('')
        self.leveltext.setHtml("<b>%s</b>" % "Current: %d%s"%(level, suffix))
        
        self.maxtext = self.scene.addText('')
        self.maxtext.setHtml("<b>%s</b>" % "Total: %d%s"%(maximum, suffix))
        
        #self.ensureVisible(self.bottle)
        self.centerOn(self.bottle)
        self.resizeEvent(None)
         
    def resizeEvent(self, event):
        size = self.size()
        width = size.width()
        height = size.height()
        
        if size.width() != size.height():
            s = (size.width()+size.height())/2
            return self.resize(s, s)
            
        for i in self.items():
            if i in self.imagemap:
                pixmap = self.imagemap[i]
                pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                i.setPixmap(pixmap)
        
        #self.ensureVisible(self.bottle)
        self.centerOn(self.bottle)
        
        maxmod = size.height()/float(max(self.maximum, 1))
        
        height = size.height()
        level = max(0, height-(self.level*maxmod))
        warn = height-(self.warn*maxmod)
        
        self.liquid.setPos(0, 0)
        self.liquid.moveBy(0, level)
        
        self.caution.setPos(0, 0)
        self.caution.moveBy(0, warn)
        
        centerx = size.width()/3.75
        self.maxtext.setPos(centerx, height-(height/10.0))
        self.warntext.setPos(centerx, warn)
        self.leveltext.setPos(centerx, level+10)
           
class IngredientViewerPane(QtGui.QWidget):
    '''Shows a set of labels populated with information about Ingredients.'''
    def __init__(self, ingredient, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ingredient = ingredient
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        name = QLabel()
        name.setTextFormat(Qt.RichText)
        name.setText("<h1>%s</h1>" % self.ingredient.name.replace("_", " ").title())
        self.layout().addWidget(name)
        
        
        warninglabel = QLabel()
        warninglabel.setTextFormat(Qt.RichText)
        if self.ingredient.current_amount > self.ingredient.threshold:
            warninglabel.setText("<h2>%.2f%% inventory</h2>" % (self.ingredient.current_amount/float(self.ingredient.size)*100))
        elif self.ingredient.current_amount <= 0:
            warninglabel.setText("<h2>%s</h2>" % "Out of Stock!")
        else:
            warninglabel.setText("<h2>%s</h2>" % "Inventory low!")
        self.layout().addWidget(warninglabel)
        
        self.bottle = BottleFullnessGuage(maximum=self.ingredient.size, level=self.ingredient.current_amount, warn=self.ingredient.threshold)
        layout.addWidget(self.bottle)
        
        formlayout = QtGui.QFormLayout()
        layout.addLayout(formlayout)
        
        #Maybe show UPC with this image (With appropriate cacheing): "http://www.upcdatabase.com/barcode/ean13/%s"
        
        self.fields = ('potency', 'barcode', 'note')
        
        for a in self.fields:
            
            value = getattr(ingredient, a)
            vt = type(value)
            if vt in (int, float, long):
                value = str(int(value))
            else:
                value = str(value)
            
            if a == "potency":
                value += "%ABV"
            
            i = QLabel(str(value))
            i.setWordWrap(True)
            
            label = a.replace("_", " ").title()+":"
            formlayout.addRow(label, i)
               
class IngredientsEditor(QtGui.QWidget):
    '''Shows a list of Ingredients and an IngredientEditorPane when one is selected.
    When it becomes visible, it loads the list of ingredients from the database.
    It selects either the first item or the last one selected.
    It then displays a viewer pane on the right which shows you information about the '''
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        self.ingredients = client.get_ingredients()
        
        self.ingredict = {}
        for v in self.ingredients:
            self.ingredict.update({v.name:v})
            
        self.last_selection = ""
        
        self.leftcol = QVBoxLayout()
        
        #TODO: Use a QSplitter to let people resize their things.
        
        self.listwidget = QtGui.QListWidget()
        self.listwidget.setFixedWidth(self.width()/3.0)
        self.leftcol.addWidget(self.listwidget)
        self.listwidget.connect(self.listwidget, SIGNAL("itemSelectionChanged()"), self.show_edit_pane)
        
        self.addbutton = QtGui.QPushButton("Add Ingredient")
        self.addbutton.connect(self.addbutton, SIGNAL("clicked()"), self.add_new_ingredient)
        self.leftcol.addWidget(self.addbutton)
        
        self.layout().addLayout(self.leftcol)
        
        self.evcontainer = QtGui.QWidget()
        self.evcontainer.setLayout(QVBoxLayout())
        self.layout().addWidget(self.evcontainer)
        self.evpane = None
        #TODO: Add a toggle button to hide or show hidden Ingredients.
        self.editbutton = QPushButton("Enable Editing")
        self.editbutton.connect(self.editbutton, SIGNAL("clicked()"), self.toggle_editmode)
        self.editing = False
        
        for a in (LCSIGNAL.doBuyAction, LCSIGNAL.doDrinkAction):
            a.connect(self.showEvent)
        
        self.update_listwidget()
        
        LCSIGNAL.doNewIngredient.connect(self.add_new_ingredient)
    
    def add_new_ingredient(self):
        i = models.Ingredient('New Ingredient', '', 0)
        client.try_add(i)
        client.commit()
        self.showEvent(None)
        for i in xrange(self.listwidget.count()):
            if self.listwidget.item(i).text() == "New Ingredient":
                self.listwidget.setCurrentItem(self.listwidget.item(i))
                break
        self.toggle_editmode()
    
    def toggle_editmode(self):
        self.editing = not self.editing
        if self.editing:
            self.editbutton.setText("Disable Editing")
        else:
            self.editbutton.setText("Enable Editing")
            self.update_listwidget()
        self.add_viewpane()
    
    def update_listwidget(self):
        self.ingredients = client.get_ingredients()
        self.listwidget.clear()
        for i in self.ingredients:
            self.ingredict.update({i.name:i})
            newitem = QtGui.QListWidgetItem(i.name)
            if i.hidden:
                newitem.setTextColor(Qt.darkGray)
            self.listwidget.addItem(newitem)
            
        items = self.listwidget.findItems(self.last_selection, Qt.MatchExactly)
        if items != []:
            self.listwidget.setCurrentItem(items[0])
        else:
            self.listwidget.setCurrentItem(self.listwidget.item(0))
        
    def show_edit_pane(self):
        if self.listwidget.selectedItems() != []:
            self.last_selection = str(self.listwidget.selectedItems()[0].text())
            self.add_viewpane()
    
    def add_viewpane(self):
        self.evcontainer.layout().removeWidget(self.evpane)
        if self.evpane is not None:
            self.evpane.setParent(None)
        
        if self.last_selection in self.ingredict:
            if self.editing:
                self.evpane = IngredientEditorPane(self.ingredict[self.last_selection])
            else:
                self.evpane = IngredientViewerPane(self.ingredict[self.last_selection])
            self.evcontainer.layout().addWidget(self.evpane)
            self.evcontainer.layout().addWidget(self.editbutton)
        else:
            print "Last selection not in ingredients!"
    
    def showEvent(self, event=None):
        self.update_listwidget()
        try:
            event.ignore()
        except(AttributeError):
            pass
        
class CountDown(QtGui.QLabel):
    secondTick = QtCore.pyqtSignal()
    def __init__(self, countdowntime, starttime=None, parent=None):
        '''`countdowntime` should be a datetime object.'''
        QtGui.QLabel.__init__(self, parent)
        
        self.setStyleSheet("QLabel {font-size:50pt; }")
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
        
        f = self.font()
        self.setFont(f)
        
        if starttime is None:
            starttime = datetime.datetime.now()
            
        self.starttime = starttime
        self.countdowntime = countdowntime
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)
        
        self.update_countdown()
    
    def update_countdown(self):
        self.countdowntime -= datetime.timedelta(seconds=1)
        
        time = self.countdowntime-self.starttime
        
        hour = time.seconds/60/60
        minute = time.seconds/60 % 60
        second = time.seconds % 60
        #text = ("<pre>%.2d:%.2d</pre>" % (hour, minute))
        #text = ("%.2d:%.2d" % (hour, minute))
        text = ("%.2d:%.2d:%.2d" % (hour, minute, second))
        #if (second % 2) == 0:
            #text = text.replace(":", " ")
        self.setText(text)

class UpdatingBACLabel(QtGui.QLabel):
    def __init__(self, frequency=5000, parent=None):
        QtGui.QLabel.__init__(self, parent)
        
        self.setStyleSheet("font-size:100pt;")
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_text)
        self.timer.start(frequency)
        
    def update_text(self):
        if self.isVisible():
            currentbac = client.get_bac_simple()
            self.setText("%.2f" % currentbac)
        
class HomePage(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QVBoxLayout())
        
        self.bigstats = QtGui.QHBoxLayout()
        self.layout().addLayout(self.bigstats)
        
        #Current estimated BAC
        baclayout = QtGui.QVBoxLayout()
        self.bigstats.addLayout(baclayout)
        baclayout.addWidget(QtGui.QLabel("Estimated BAC:"))
        self.bac = UpdatingBACLabel()
        baclayout.addWidget(self.bac)
        
        #Countdown timer for time til sober and time til happy hour
        #These are (re)built on show.
        self.drinktimerlayout = None
        self.countdown = None
        self.drinktimerlabel = None
        self._build_countdowns()
        
        #Top 6 Ingredients/size combos as huge buttons
        self.popingreds = None
        self.ingrbuttons = []
        self.timers = []
        self._build_ingr_buttons()
        
        for a in (LCSIGNAL.doBuyAction, LCSIGNAL.doDrinkAction):
            a.connect(functools.partial(self.showEvent, None))

        #Filler buttons
        #for i in xrange(4-numbuttons):
            #tempbutton = QtGui.QPushButton("Nothing \n(Zip/0mL)")
            #tempbutton.setStyleSheet("font-size:20pt; text-align: center;")
            #self.popingreds.addWidget(tempbutton)
        
        #3 Most Popular things that are about to go out of stock.
        #self.poplow = QtGui.QHBoxLayout()
        #self.layout().addLayout(self.poplow)
        
        
    def _build_countdowns(self):
        if self.drinktimerlayout is not None:
            self.bigstats.removeItem(self.drinktimerlayout)
            
        for w in (self.countdown, self.drinktimerlabel):
            if w is not None:
                w.setParent(None)
            
        currentbac = client.get_bac_simple()
        
        self.drinktimerlayout = QtGui.QVBoxLayout()
        self.bigstats.addLayout(self.drinktimerlayout)
        
        if currentbac > 0:
            #Estimated time remaining until sober
            self.drinktimerlabel = QtGui.QLabel("Time til sober(ish):")
            self.drinktimerlayout.addWidget(self.drinktimerlabel)
            absorpsec = 0.05/60.0/60.0
            s = currentbac/absorpsec
            delta = datetime.timedelta(seconds=s)
            target = datetime.datetime.now()+delta
            self.countdown = CountDown(target)
        else:
            #Estimated time until it's socially acceptable to drink
            self.drinktimerlabel = QtGui.QLabel("Booze o' Clock:")
            
            self.drinktimerlayout.addWidget(self.drinktimerlabel)
            wakeup_time = client.get_latest_wakeup()
            drinktime = (wakeup_time+datetime.timedelta(hours=DRUNK_BEFORE_NOON))
            self.countdown = CountDown(drinktime, wakeup_time)
        
        self.drinktimerlabel.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum))
        self.drinktimerlayout.addWidget(self.countdown)
            
    def _build_ingr_buttons(self):
        if self.popingreds is not None:
            self.layout().removeItem(self.popingreds)
            
        for b in self.ingrbuttons:
            b.setParent(None)
        
        self.popingreds = QtGui.QHBoxLayout()
        self.layout().addLayout(self.popingreds)
        
        numbuttons = 0
        for i in client.get_popular_ingredients(4):
            d = client.get_common_drink_amounts(i)
            
            if len(d) == 0:
                continue
            
            top = 0
            topkey = ""
            
            for k,v in d.iteritems():
                if v > top:
                    top = v
                    topkey = k
                    
            words = []
            length = 0
            for t in i.name.split(" "):
                if length+len(t) > 15:
                    words.append(("\n"))
                    length = 0
                words.append(t)
                length += len(t)
                    
            tempbutton = QtGui.QPushButton("%s \n(%s/%dmL)" % (' '.join(words), topkey.name, topkey.amount))
            tempbutton.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
            tempbutton.setStyleSheet("font-size:20pt; text-align: center;")
            
            tempbutton.clicked.connect(functools.partial(client.drink, "Quickdrink", i, topkey.amount))
            tempbutton.clicked.connect(functools.partial(tempbutton.setEnabled, False))
            tempbutton.clicked.connect(functools.partial(self._build_countdowns))
            
            if topkey.amount > i.current_amount:
				tempbutton.setText(tempbutton.text()+"\n (out of stock)")
				tempbutton.setEnabled(False)
            
            timer = QTimer()
            timer.timeout.connect(functools.partial(tempbutton.setEnabled, True))
            self.timers.append(timer)
            
            tempbutton.clicked.connect(functools.partial(timer.start, 1000))
            
            self.popingreds.addWidget(tempbutton)
            self.ingrbuttons.append(tempbutton)
            numbuttons += 1
    
    def showEvent(self, ev):
        self.bac.update_text()

        self._build_countdowns()
        self._build_ingr_buttons()
        
        if ev is not None:
            ev.ignore()
        
class DrinkCalendar(QtGui.QCalendarWidget):
    '''Show a calendar widget which shows all the Ingredients consumed on each day as an icon.
    Lets users add/remove/modify Ingredient modifications.
    '''
    def paintCell(self, painter, rect, date):
        dateField = date.toString("yyyyMMdd")
        
        font = QtGui.QApplication.font()
        font.setPointSize(rect.width() / 8)
        painter.setFont(font)
        
        painter.drawRect(rect)
        
        drinks = client.get_drinks_on_date(date.toPyDate())
        totalamount = sum([a.amount for a in drinks])
        	
        #Get the things drunk on that day.
        #Show an icon for each drink, maybe scaled up proportionally for the amount that day.
        #Get the ingredient drunk for each drink, choose an icon for the varying percentages of alcohol:
        #Default: Cocktail Glass, <30: Tropical Drink, <20:Wine glass, <5: Beer Mug, 
        #Add a context menu to work with the data in each cell.
        
        if(totalamount > 0):
            font.setWeight(QtGui.QFont.Bold)
            font.setStyle(QtGui.QFont.StyleItalic)
            painter.setFont(font)
            painter.setPen(Qt.blue)
            painter.drawText(rect, Qt.AlignCenter, QtCore.QString(str("*"*len(drinks))+" (%dml)"%totalamount))
        elif(date==QtCore.QDate.currentDate()):
            font.setWeight(QtGui.QFont.Bold)
            painter.setFont(font)
            painter.setPen(Qt.darkRed)
        elif (date.month() == self.monthShown()):
            font.setWeight(QtGui.QFont.Normal)
            painter.setFont(font)
            painter.setPen(Qt.black)
        else:
            font.setWeight(QtGui.QFont.Light)
            painter.setFont(font)
            painter.setPen(Qt.gray)
        
        painter.drawText(QtCore.QRect(rect.left(), rect.top(), rect.width()/2, rect.height()/2), Qt.AlignCenter, date.toString("d"))
        
    

class MainWindow(QtGui.QWidget):
    def __init__(self, win_parent = None):
        #Init the base class
        QtGui.QWidget.__init__(self, win_parent)
        
        try:
            global trayIcon
            if trayIcon:
                trayIcon.activated.connect(self.__icon_activated)
                LCSIGNAL.doNewIngredient.connect(self.show)
        except(NameError):
            pass
        except(AttributeError), err:
            print err
                                         
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
        
        #Some quick statistics in large font
        self.homepage = QtGui.QWidget()
        self.homepage.setLayout(QtGui.QHBoxLayout())
        self.tabs.addTab(self.homepage, "Home")
        self.homepage.layout().addWidget(HomePage())

        #This tab shows a calendar widget that lets you add drinks to specific dates
        self.calendar_tab = QtGui.QWidget()
        self.calendar_tab.setLayout(QtGui.QHBoxLayout())
        self.tabs.addTab(self.calendar_tab, "Calendar")
        self.calendar_tab.layout().addWidget(DrinkCalendar())
        
        #The ShoppingList widget
        self.shoppinglist = QtGui.QWidget()
        self.shoppinglist.setLayout(QtGui.QHBoxLayout())
        self.tabs.addTab(self.shoppinglist, "Shopping List")
        self.shoppinglist.layout().addWidget(ShoppingList())
        
        #The IngredientsEditor widget
        self.ingredients_tab = QtGui.QWidget()
        self.ingredients_tab.setLayout(QtGui.QHBoxLayout())
        self.tabs.addTab(self.ingredients_tab, "Ingredients")
        self.ingredients_tab.layout().addWidget(IngredientsEditor())
        try:
            LCSIGNAL.doNewIngredient.connect(functools.partial(self.tabs.setCurrentWidget, self.ingredients_tab))
        except(NameError, AttributeError):
            pass

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

def safe_client_dump(filename="database.py"):
    try:
        #client.dump_to_disk("test_diskspace_file.tmp")
        return client.dump_to_disk(filename)
    except(IOError), err:
        trayIcon.showMessage("Unable to write database to disk.", str(err))
        return err
    
class LiquorCabinetSignals(QtCore.QObject):
    '''This class holds all the signals that the application uses.'''
    doNewIngredient = QtCore.pyqtSignal()
    doNewDrink = QtCore.pyqtSignal()
    
    doDrinkAction = QtCore.pyqtSignal()
    doBuyAction = QtCore.pyqtSignal()

LCSIGNAL = LiquorCabinetSignals()

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

    appIcon = QtGui.QIcon(TRAY_ICON)
    app.setWindowIcon(appIcon)
    
    global trayIcon
    trayIcon = SystemTrayIcon(appIcon)
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
    
    #ivp = IngredientViewerPane(client.get_ingredients()[0])
    #ivp.show()
    
    #inged = IngredientsEditor()
    #inged.show()
    
    #b = BottleFullnessGuage()
    #b.show()
    
    print("There is now a red and white potion bottle in your system tray. That's where all your icons go. Click to get a window, right click to get a menu.")
    print("CTRL+C will exit the program, but will not save data automatically. Closing from the program will save your data automatically.")

    app.setQuitOnLastWindowClosed(False)
    
    savetimer = QTimer()
    savetimer.connect(savetimer, SIGNAL("timeout()"), functools.partial(safe_client_dump, DATABASE_FILENAME))
    
    length = 0
    for i in (client.get_ingredients(), client.get_amounts(), client.session.query(models.Log).all()):
        length += len(i)
    delaymod = length/100.0
        
    savetimer.start(WRITE_DATA_DELAY*delaymod)
    print "Automatically saving every %.2f minutes" % (((((WRITE_DATA_DELAY*delaymod)/1000.0)/60.0)))

    safe_client_dump(DATABASE_FILENAME)

    rval = app.exec_()
    
    safe_client_dump(DATABASE_FILENAME)
    
    sys.exit(rval)

if __name__ == '__main__':
    main()
