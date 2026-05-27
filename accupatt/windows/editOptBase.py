import os

import accupatt.config as cfg
from PyQt6 import uic
from PyQt6.QtWidgets import QDialogButtonBox, QLineEdit, QSpinBox

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "editOptBase.ui")
)


class EditOptBase(baseclass):
    def __init__(self, optBase, window_units: str, show_smooth: bool = True, is_string: bool = True, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.opt = optBase
        self.window_units = window_units
        self.show_smooth = show_smooth
        self.is_string = is_string

        if not show_smooth:
            self.ui.lineEditSmoothWindow.hide()
            self.ui.labelSmoothWindowUnits.hide()
            self.ui.spinBoxOrder.hide()
            for widget in [
                getattr(self.ui, name, None)
                for name in ("labelSmoothWindow", "labelSmoothOrder")
            ]:
                if widget:
                    widget.hide()

        self._populate_fields()

        self.ui.buttonBox.button(
            QDialogButtonBox.StandardButton.RestoreDefaults
        ).clicked.connect(self._reset_defaults)

        self.show()

    def _populate_fields(self):
        self.ui.labelName.setText(self.opt.name)
        if self.show_smooth:
            self.lineEditSmoothWindow: QLineEdit = self.ui.lineEditSmoothWindow
            self.lineEditSmoothWindow.setText(str(self.opt.smooth_window))
            self.ui.labelSmoothWindowUnits.setText(self.window_units)
            self.spinBoxOrder: QSpinBox = self.ui.spinBoxOrder
            self.spinBoxOrder.setValue(self.opt.smooth_order)
        self.ui.radioButtonCentroid.setChecked(
            self.opt.center_method == cfg.CENTER_METHOD_CENTROID
        )
        self.ui.radioButtonCOD.setChecked(
            self.opt.center_method == cfg.CENTER_METHOD_COD
        )

    def _reset_defaults(self):
        self.ui.labelName.setText(self.opt.name)
        if self.show_smooth:
            self.ui.lineEditSmoothWindow.setText(str(cfg.get_smooth_window()))
            self.ui.labelSmoothWindowUnits.setText(self.window_units)
            self.ui.spinBoxOrder.setValue(cfg.get_smooth_order())
        _default = cfg.get_center_method_string() if self.is_string else cfg.get_center_method_card()
        self.ui.radioButtonCentroid.setChecked(_default == cfg.CENTER_METHOD_CENTROID)
        self.ui.radioButtonCOD.setChecked(_default == cfg.CENTER_METHOD_COD)

    def accept(self):
        if self.show_smooth:
            self.opt.smooth_window = float(self.ui.lineEditSmoothWindow.text())
            self.opt.smooth_order = self.ui.spinBoxOrder.value()
        center_method = (
            cfg.CENTER_METHOD_CENTROID
            if self.ui.radioButtonCentroid.isChecked()
            else cfg.CENTER_METHOD_COD
        )
        self.opt.center_method = center_method

        if self.ui.checkBoxUpdateDefaults.isChecked():
            if self.show_smooth:
                cfg.set_smooth_window(self.opt.smooth_window)
                cfg.set_smooth_order(self.opt.smooth_order)
            if self.is_string:
                cfg.set_center_method_string(center_method)
            else:
                cfg.set_center_method_card(center_method)

        super().accept()
