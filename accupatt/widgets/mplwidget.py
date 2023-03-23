import matplotlib
from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
from PyQt6 import QtWidgets

# Ensure using PyQt6 backend
matplotlib.use("QTAgg")


# Matplotlib canvas class to create figure
class MplCanvas(Canvas):
    def __init__(self):
        self.fig = Figure(layout="tight")
        self.ax: Axes = self.fig.add_subplot(111)
        Canvas.__init__(self, self.fig)


# Matplotlib widget
class MplWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)  # Inherit from QWidget
        self.canvas = MplCanvas()  # Create canvas object
        self.vbl = QtWidgets.QVBoxLayout()  # Set box for plotting
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)
        self.has_legend = True
        self.legend_outside = False
        self.ticks_slanted = False

    def set_ticks_slanted(self):
        self.ticks_slanted = True
        for label in self.canvas.ax.get_xticklabels(which="major"):
            label.set(rotation=30, horizontalalignment="right")

    def resize_inches(self, width_inches: float, height_inches: float):
        fig = self.canvas.fig
        self.figure_size_original = fig.get_size_inches()
        fig.set_size_inches(width_inches, height_inches)
        if self.legend_outside:
            self.canvas.ax.legend(
                loc="center left", bbox_to_anchor=(1, 0.5), fontsize=6
            )
        elif self.has_legend:
            self.canvas.ax.legend(fontsize=6)
        self.canvas.ax.tick_params(axis="both", which="major", labelsize=6)
        self.xlab_size_original = self.canvas.ax.xaxis.label.get_size()
        self.canvas.ax.xaxis.label.set_size(6)
        self.ylab_size_original = self.canvas.ax.yaxis.label.get_size()
        self.canvas.ax.yaxis.label.set_size(6)
        self.canvas.draw()

    def resize_inches_reset(self):
        self.canvas.fig.set_size_inches(self.figure_size_original)
        if self.legend_outside:
            self.canvas.ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        elif self.has_legend:
            self.canvas.ax.legend()
        self.canvas.ax.tick_params(
            axis="both", which="major", top=False, right=False, reset=True
        )
        if self.ticks_slanted:
            self.set_ticks_slanted()
        self.canvas.ax.xaxis.label.set_size(self.xlab_size_original)
        self.canvas.ax.yaxis.label.set_size(self.ylab_size_original)
        self.canvas.draw()
