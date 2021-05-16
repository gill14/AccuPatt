import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

class  PyQtPlotWidget(pg.GraphicsWindow):
    #pg.setConfigOption('background', 'w')
    #pg.setConfigOption('foreground', 'k')
    def __init__(self, parent=None, **kargs):
        pg.GraphicsWindow.__init__(self, **kargs)
        self.setParent(parent)

if __name__ == '__main__':
    w = PyQtPlotWidget()
    w.show()
    QtGui.QApplication.instance().exec_()
