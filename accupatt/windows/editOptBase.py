import os

import accupatt.config as cfg
from PyQt6 import uic
from PyQt6.QtWidgets import QDialogButtonBox, QLineEdit, QSpinBox
from accupatt.models.OptBase import OptBase

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "editOptBase.ui")
)


class EditOptBase(baseclass):
    def __init__(self, optBase: OptBase, window_units: str, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.opt = optBase
        self.window_units = window_units
        self._populate_fields()

        self.ui.buttonBox.button(
            QDialogButtonBox.StandardButton.RestoreDefaults
        ).clicked.connect(self._reset_defaults)

        self.show()

    def _populate_fields(self):
        self.ui.labelName.setText(self.opt.name)
        self.lineEditSmoothWindow: QLineEdit = self.ui.lineEditSmoothWindow
        self.lineEditSmoothWindow.setText(str(self.opt.smooth_window))
        self.ui.labelSmoothWindowUnits.setText(self.window_units)
        self.spinBoxOrder: QSpinBox = self.ui.spinBoxOrder
        self.spinBoxOrder.setValue(self.opt.smooth_order)
        self.ui.radioButtonCentroid.setChecked(
            self.opt.center_method == cfg.CENTER_METHOD_CENTROID
        )
        self.ui.radioButtonCOD.setChecked(self.opt.center_method == cfg.CENTER_METHOD_COD)

    def _reset_defaults(self):
        self.ui.labelName.setText(self.opt.name)
        self.lineEditSmoothWindow: QLineEdit = self.ui.lineEditSmoothWindow
        self.lineEditSmoothWindow.setText(str(cfg.get_smooth_window()))
        self.ui.labelSmoothWindowUnits.setText(self.window_units)
        self.spinBoxOrder: QSpinBox = self.ui.spinBoxOrder
        self.spinBoxOrder.setValue(cfg.get_smooth_order())
        self.ui.radioButtonCentroid.setChecked(
            cfg.get_center_method() == cfg.CENTER_METHOD_CENTROID
        )
        self.ui.radioButtonCOD.setChecked(cfg.get_center_method() == cfg.CENTER_METHOD_COD)

    def accept(self):
        # Capture/Cast values
        smooth_window = float(self.lineEditSmoothWindow.text())
        smooth_order = self.spinBoxOrder.value()
        center_method = (
            cfg.CENTER_METHOD_CENTROID
            if self.ui.radioButtonCentroid.isChecked()
            else cfg.CENTER_METHOD_COD
        )
        self.opt.smooth_window = smooth_window
        self.opt.smooth_order = smooth_order
        self.opt.center_method = center_method

        if self.ui.checkBoxUpdateDefaults.isChecked():
            # Update Defaults
            cfg.set_smooth_window(smooth_window)
            cfg.set_smooth_order(smooth_order)
            cfg.set_center_method(center_method)

        super().accept()
