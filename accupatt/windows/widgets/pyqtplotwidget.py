from PyQt5.QtWidgets import QApplication, QGraphicsWidget

from pyqtgraph import GraphicsWindow
from pyqtgraph.Qt import QtGui, mkQApp
from pyqtgraph.graphicsItems.GraphicsWidget import GraphicsWidget
from pyqtgraph.widgets.GraphicsLayoutWidget import GraphicsLayoutWidget
from pyqtgraph.widgets.PlotWidget import PlotWidget

class  PyQtPlotWidget(GraphicsLayoutWidget):
     def __init__(self, parent = None, title=None, size=(800,600), **kargs):
        mkQApp()
        GraphicsLayoutWidget.__init__(self, **kargs)
        self.resize(*size)
        if title is not None:
            self.setWindowTitle(title)
        self.show()
        
        self.setParent(parent)

if __name__ == '__main__':
    w = PyQtPlotWidget()
    w.show()
    QtGui.QApplication.instance().exec_()
