import os

import accupatt.config as cfg
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QGroupBox, QRadioButton

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "cardPlotOptions.ui")
)


class CardPlotOptions(baseclass):

    # Signal to update plots (individuals, composites, simulations)
    request_update_plots = pyqtSignal(bool, bool, bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.gb_y_axis: QGroupBox = self.ui.gb_y_axis
        self.rb_coverage: QRadioButton = self.ui.rb_coverage
        self.rb_deposition: QRadioButton = self.ui.rb_deposition
        y_axis = cfg.get_card_plot_y_axis()
        self.rb_coverage.setChecked(y_axis == cfg.CARD_PLOT_Y_AXIS_COVERAGE)
        self.rb_deposition.setChecked(y_axis == cfg.CARD_PLOT_Y_AXIS_DEPOSITION)
        self.rb_coverage.toggled[bool].connect(self._rb_coverage)
        self.rb_deposition.toggled[bool].connect(self._rb_deposition)

        self.gb_shading: QGroupBox = self.ui.gb_shading
        self.gb_shading.setChecked(cfg.get_card_plot_shading())
        self.gb_shading.toggled[bool].connect(self._gb_shading)
        self.gb_shading_method: QGroupBox = self.ui.gb_shading_method
        self.rb_dsc: QRadioButton = self.ui.rb_dsc
        self.rb_deposition_average: QRadioButton = self.ui.rb_deposition_average
        self.rb_deposition_target: QRadioButton = self.ui.rb_deposition_target
        shade_method = cfg.get_card_plot_shading_method()
        self.rb_dsc.setChecked(shade_method == cfg.CARD_PLOT_SHADING_METHOD_DSC)
        self.rb_deposition_average.setChecked(
            shade_method == cfg.CARD_PLOT_SHADING_METHOD_DEPOSITION_AVERAGE
        )
        self.rb_deposition_target.setChecked(
            shade_method == cfg.CARD_PLOT_SHADING_METHOD_DEPOSITION_TARGET
        )
        self.rb_dsc.toggled[bool].connect(self._rb_dsc)
        self.rb_deposition_average.toggled[bool].connect(self._rb_deposition_average)
        self.rb_deposition_target.toggled[bool].connect(self._rb_deposition_target)
        self.gb_shading_interp: QGroupBox = self.ui.gb_shading_interp
        self.rb_linear: QRadioButton = self.ui.rb_linear
        self.rb_nearest: QRadioButton = self.ui.rb_nearest
        self.rb_linear.setChecked(cfg.get_card_plot_shading_interpolate())
        self.rb_nearest.setChecked(not cfg.get_card_plot_shading_interpolate())
        self.rb_linear.toggled[bool].connect(self._rb_linear)
        self.rb_nearest.toggled[bool].connect(self._rb_nearest)

        self.gb_average_overlay: QGroupBox = self.ui.gb_average_overlay
        self.gb_average_overlay.setChecked(cfg.get_card_plot_average_dash_overlay())
        self.gb_average_overlay.toggled[bool].connect(self._gb_average_overlay)
        self.rb_swath_box: QRadioButton = self.ui.rb_swath_box
        self.rb_average_value: QRadioButton = self.ui.rb_average_value
        dash = cfg.get_card_plot_average_dash_overlay_method()
        self.rb_swath_box.setChecked(dash == cfg.DASH_OVERLAY_METHOD_ISHA)
        self.rb_average_value.setChecked(dash == cfg.DASH_OVERLAY_METHOD_AVERAGE)
        self.rb_swath_box.toggled[bool].connect(self._rb_swath_box)
        self.rb_average_value.toggled[bool].connect(self._rb_average)

        self.gb_simulation: QGroupBox = self.ui.gb_simulation
        self.rb_one: QRadioButton = self.ui.rb_one
        self.rb_all: QRadioButton = self.ui.rb_all
        sim = cfg.get_card_simulation_view_window()
        self.rb_one.setChecked(sim == cfg.CARD_SIMULATION_VIEW_WINDOW_ONE)
        self.rb_all.setChecked(sim == cfg.CARD_SIMULATINO_VIEW_WINDOW_ALL)
        self.rb_one.toggled[bool].connect(self._rb_one)
        self.rb_all.toggled[bool].connect(self._rb_all)

        self.show()

    """
    Y - Axis
    """

    @pyqtSlot(bool)
    def _rb_coverage(self, checked):
        if checked:
            self._set_y_axis(cfg.CARD_PLOT_Y_AXIS_COVERAGE)

    @pyqtSlot(bool)
    def _rb_deposition(self, checked):
        if checked:
            self._set_y_axis(cfg.CARD_PLOT_Y_AXIS_DEPOSITION)

    def _set_y_axis(self, option: str):
        cfg.set_card_plot_y_axis(option)
        self.request_update_plots.emit(True, True, True)

    """
    Shading
    """

    @pyqtSlot(bool)
    def _gb_shading(self, checked):
        cfg.set_card_plot_shading(checked)
        self.request_update_plots.emit(True, True, False)

    @pyqtSlot(bool)
    def _rb_dsc(self, checked):
        if checked:
            self._set_shading_method(cfg.CARD_PLOT_SHADING_METHOD_DSC)

    @pyqtSlot(bool)
    def _rb_deposition_average(self, checked):
        if checked:
            self._set_shading_method(cfg.CARD_PLOT_SHADING_METHOD_DEPOSITION_AVERAGE)

    @pyqtSlot(bool)
    def _rb_deposition_target(self, checked):
        if checked:
            self._set_shading_method(cfg.CARD_PLOT_SHADING_METHOD_DEPOSITION_TARGET)

    def _set_shading_method(self, option: str):
        cfg.set_card_plot_shading_method(option)
        self.request_update_plots.emit(True, True, False)

    @pyqtSlot(bool)
    def _rb_linear(self, checked):
        if checked:
            self._set_shading_interpolation(True)

    @pyqtSlot(bool)
    def _rb_nearest(self, checked):
        if checked:
            self._set_shading_interpolation(False)

    def _set_shading_interpolation(self, option: bool):
        cfg.set_card_plot_shading_interpolate(option)
        self.request_update_plots.emit(True, True, False)

    """
    Average Overlay
    """

    @pyqtSlot(bool)
    def _gb_average_overlay(self, checked):
        cfg.set_card_plot_average_dash_overlay(checked)
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
        cfg.set_card_plot_average_dash_overlay_method(option)
        self.request_update_plots.emit(False, True, False)

    """
    Simulation X-Range
    """

    @pyqtSlot(bool)
    def _rb_one(self, checked):
        if checked:
            self._set_simulation_range(cfg.CARD_SIMULATION_VIEW_WINDOW_ONE)

    @pyqtSlot(bool)
    def _rb_all(self, checked):
        if checked:
            self._set_simulation_range(cfg.CARD_SIMULATINO_VIEW_WINDOW_ALL)

    def _set_simulation_range(self, option: str):
        cfg.set_card_simulation_view_window(option)
        self.request_update_plots.emit(False, False, True)
