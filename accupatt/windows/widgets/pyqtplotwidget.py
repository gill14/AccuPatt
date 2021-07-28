from PyQt5.QtWidgets import QApplication

from pyqtgraph import GraphicsWindow
from pyqtgraph.Qt import QtGui

class  PyQtPlotWidget(GraphicsWindow):
    #pg.setConfigOption('background', 'w')
    #pg.setConfigOption('foreground', 'k')
    def __init__(self, parent=None, **kargs):
        GraphicsWindow.__init__(self, **kargs)
        self.setParent(parent)

if __name__ == '__main__':
    w = PyQtPlotWidget()
    w.show()
    QtGui.QApplication.instance().exec_()
