import os

import accupatt.config as cfg
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QGroupBox, QRadioButton

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "stringPlotOptions.ui")
)


class StringPlotOptions(baseclass):

    # Signal to update plots (individuals, composites, simulations)
    request_update_plots = pyqtSignal(bool, bool, bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.gb_average_overlay: QGroupBox = self.ui.gb_average_overlay
        self.gb_average_overlay.setChecked(cfg.get_string_plot_average_dash_overlay())
        self.gb_average_overlay.toggled[bool].connect(self._gb_average_overlay)
        self.rb_swath_box: QRadioButton = self.ui.rb_swath_box
        self.rb_average_value: QRadioButton = self.ui.rb_average_value
        dash = cfg.get_string_plot_average_dash_overlay_method()
        self.rb_swath_box.setChecked(dash == cfg.DASH_OVERLAY_METHOD_ISHA)
        self.rb_average_value.setChecked(dash == cfg.DASH_OVERLAY_METHOD_AVERAGE)
        self.rb_swath_box.toggled[bool].connect(self._rb_swath_box)
        self.rb_average_value.toggled[bool].connect(self._rb_average)

        self.gb_simulation: QGroupBox = self.ui.gb_simulation
        self.rb_one: QRadioButton = self.ui.rb_one
        self.rb_all: QRadioButton = self.ui.rb_all
        sim = cfg.get_string_simulation_view_window()
        self.rb_one.setChecked(sim == cfg.STRING_SIMULATION_VIEW_WINDOW_ONE)
        self.rb_all.setChecked(sim == cfg.STRING_SIMULATION_VIEW_WINDOW_ALL)
        self.rb_one.toggled[bool].connect(self._rb_one)
        self.rb_all.toggled[bool].connect(self._rb_all)

        self.show()

    """
    Average Overlay
    """

    @pyqtSlot(bool)
    def _gb_average_overlay(self, checked):
        cfg.set_string_plot_average_dash_overlay(checked)
        self.request_update_plots.emit(False, True, False)

    @pyqtSlot(bool)
    def _rb_swath_box(self, checked):
        if checked:
            self._set_average_dash_overlay_method(cfg.DASH_OVERLAY_METHOD_ISHA)

    @pyqtSlot(bool)
    def _rb_average(self, checked):
        if checked:
            self._set_average_dash_overlay_method(cfg.DASH_OVERLAY_METHOD_AVERAGE)

    def _set_average_dash_overlay_method(self, option: str):
        cfg.set_string_plot_average_dash_overlay_method(option)
        self.request_update_plots.emit(False, True, False)

    """
    Simulation X-Range
    """

    @pyqtSlot(bool)
    def _rb_one(self, checked):
        if checked:
            self._set_simulation_range(cfg.STRING_SIMULATION_VIEW_WINDOW_ONE)

    @pyqtSlot(bool)
    def _rb_all(self, checked):
        if checked:
            self._set_simulation_range(cfg.STRING_SIMULATION_VIEW_WINDOW_ALL)

    def _set_simulation_range(self, option: str):
        cfg.set_string_simulation_view_window(option)
        self.request_update_plots.emit(False, False, True)
