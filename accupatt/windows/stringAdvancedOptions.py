import os

import accupatt.config as cfg
from PyQt6 import uic
from PyQt6.QtWidgets import QDialogButtonBox, QLineEdit, QSpinBox
from accupatt.models.passData import Pass

from accupatt.models.seriesData import SeriesData

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "stringAdvancedOptions.ui")
)


class StringAdvancedOptions(baseclass):
    def __init__(
        self, passData: Pass = None, seriesData: SeriesData = None, parent=None
    ):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        if passData:
            self._populate_fields(
                name=passData.name,
                window=passData.string.smooth_window,
                window_units=passData.string.data_loc_units,
                order=passData.string.smooth_order,
                center_method=passData.string.center_method,
            )
        else:
            self._populate_fields(
                name="Series",
                window=seriesData.string.smooth_window,
                window_units=seriesData.info.swath_units,
                order=seriesData.string.smooth_order,
                center_method=seriesData.string.center_method,
            )

        self.passData = passData
        self.seriesData = seriesData

        self.ui.buttonBox.button(
            QDialogButtonBox.StandardButton.RestoreDefaults
        ).clicked.connect(self._reset_defaults)

        self.show()

    def _populate_fields(
        self,
        name: str,
        window: float,
        window_units: str,
        order: int,
        center_method: str,
    ):
        self.ui.labelName.setText(name)
        self.lineEditSmoothWindow: QLineEdit = self.ui.lineEditSmoothWindow
        self.lineEditSmoothWindow.setText(str(window))
        self.ui.labelSmoothWindowUnits.setText(window_units)
        self.spinBoxOrder: QSpinBox = self.ui.spinBoxOrder
        self.spinBoxOrder.setValue(order)
        self.ui.radioButtonCentroid.setChecked(
            center_method == cfg.CENTER_METHOD_CENTROID
        )
        self.ui.radioButtonCOD.setChecked(center_method == cfg.CENTER_METHOD_COD)

    def _reset_defaults(self):
        self._populate_fields(
            name=self.ui.labelName.text(),
            window=cfg.get_string_smooth_window(),
            window_units=self.ui.labelSmoothWindowUnits.text(),
            order=cfg.get_string_smooth_order(),
            center_method=cfg.get_center_method(),
        )

    def accept(self):
        # Capture/Cast values
        smooth_window = float(self.lineEditSmoothWindow.text())
        smooth_order = self.spinBoxOrder.value()
        center_method = (
            cfg.CENTER_METHOD_CENTROID
            if self.ui.radioButtonCentroid.isChecked()
            else cfg.CENTER_METHOD_COD
        )

        if self.passData:
            # Update Pass object
            self.passData.string.smooth_window = smooth_window
            self.passData.string.smooth_order = smooth_order
            self.passData.string.center_method = center_method
        else:
            # Update Series Object
            self.seriesData.string.smooth_window = smooth_window
            self.seriesData.string.smooth_order = smooth_order
            self.seriesData.string.center_method = center_method

        if self.ui.checkBoxUpdateDefaults.isChecked():
            # Update Defaults
            cfg.set_string_smooth_window(smooth_window)
            cfg.set_string_smooth_order(smooth_order)
            cfg.set_center_method(center_method)

        super().accept()
