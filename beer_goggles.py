#!/usr/bin/env python

'''This module provides a number of unscientific tests that can be used to
determine if a user is under the influence of mind-effecting substances 
such as alcohol.

The first is simple math.
The second is more complex math.
The third is shape recognition.
The fourth is hand-eye coordination. (Clicking on moving objects.)
'''
from __future__ import division

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import SIGNAL, SLOT

import random
import time

class BeerGogglesMath(QtGui.QWidget):
    def __init__(self, parent = None, simple=False, complex=False):
        QtGui.QWidget.__init__(self, parent)
        
        self.setLayout(QtGui.QVBoxLayout())
        
        self.equationlabel = QtGui.QWidget()
        self.equationlabel.setLayout(QtGui.QHBoxLayout())
        self.layout().addWidget(self.equationlabel)
        
        self.solvebutton = QtGui.QPushButton("Solve!")
        self.layout().addWidget(self.solvebutton)
        self.solvebutton.connect(self.solvebutton, SIGNAL("clicked()"), self.solve)
        
        if simple:
            self.build_equation(self.simple_equation())
        elif complex:
            self.build_equation(self.complex_equation())
            
        self.starttime = time.time()
        self.finishtime = False
        self.correct = None
    
    def showEvent(self, event):
        self.equationanswer.setFocus()
        event.ignore()
    
    def solve(self):
        self.finishtime = time.time()
        self.solvebutton.setEnabled(False)
        
        givenanswer = str(self.equationanswer.text())
        if (givenanswer) == "":
            givenanswer = "0"
        givenanswer = eval(givenanswer)
        realanswer = eval(self.equation)
        
        if givenanswer != realanswer:
            print "WRONG", realanswer
            self.emit(SIGNAL("BeerGogglesWrongAnswer"), self.finishtime, givenanswer, realanswer)
            self.correct = False
        else:
            self.emit(SIGNAL("BeerGogglesRightAnswer"), self.finishtime, realanswer)
            print "RIGHT :D"
            self.correct = True
        
        
        print "Answered in", self.finishtime-self.starttime, "seconds."
    
    def build_equation(self, equation):
        self.equation = equation
        
        #TODO: Move the font size to an external stylesheet
        f = QtGui.QFont()
        f.setPointSize(60)
        
        equation = equation.replace("*", u"\u00D7")
        equation = equation.replace("/", u"\u00F7")
        equatlabel = QtGui.QLabel(equation+"=")
        equatlabel.setFont(f)
        self.equationlabel.layout().addWidget(equatlabel)
        
        self.equationanswer = QtGui.QLineEdit()
        self.equationanswer.connect(self.equationanswer, SIGNAL("returnPressed()"), self.solve)
        
        answerlen = len(str(eval(self.equation)))
        self.equationanswer.setMaxLength(answerlen)
        #self.equationanswer.setInputMask("#"*answerlen)
        
        self.equationanswer.setFont(f)
        fm = QtGui.QFontMetrics(f)
        pixelWidth = fm.width("0"*answerlen)
        self.equationanswer.setFixedWidth(pixelWidth + 10)
        
        self.equationlabel.layout().addWidget(self.equationanswer)
        
    def simple_equation(self):
        x = random.randint(1, 9)
        y = random.randint(1, 9)
        op = random.choice(("+", "-"))
        equation = "%d%s%d" % (x, op, y)
        return equation
        
    def complex_equation(self):
        equation = "0.1"
        while type(eval(equation)) is float:
            x = random.randint(1, 5)
            y = random.randint(1, 5)
            op = random.choice(("*", "/"))
            equation = "%d%s%d" % (x, op, y)
        return equation
        
        
def main():
    import signal
    import sys
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtGui.QApplication(sys.argv)
    
    s =  BeerGogglesMath(simple=True)
    s.show()
    
    c =  BeerGogglesMath(complex=True)
    c.show()
    
    app.exec_()
    

if __name__ == '__main__':
    main()