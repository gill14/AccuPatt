import os

import accupatt.config as cfg
from accupatt.models.seriesData import SeriesData
from accupatt.models.passData import Pass
from accupatt.models.sprayCard import SprayCard
from PyQt6 import uic
from PyQt6.QtCore import QSignalBlocker, Qt
from PyQt6.QtWidgets import QDialogButtonBox, QMessageBox

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "editSpreadFactors.ui")
)


class EditSpreadFactors(baseclass):
    def __init__(self, sprayCard, passData: Pass, seriesData: SeriesData, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # To operate upon
        self.sprayCard: SprayCard = sprayCard
        self.passData = passData
        self.seriesData = seriesData

        # Setup UI to vals
        self.method = self.sprayCard.spread_method
        if self.method == cfg.SPREAD_METHOD_ADAPTIVE:
            self.ui.radioButtonAdaptive.setChecked(True)
        elif self.method == cfg.SPREAD_METHOD_DIRECT:
            self.ui.radioButtonDirect.setChecked(True)
        else:
            self.ui.radioButtonNone.setChecked(True)
        self.ui.spreadFactorALineEdit.setText(f"{self.sprayCard.spread_factor_a:g}")
        self.ui.spreadFactorBLineEdit.setText(f"{self.sprayCard.spread_factor_b:g}")
        self.ui.spreadFactorCLineEdit.setText(f"{self.sprayCard.spread_factor_c:g}")

        # Setup signals
        self.ui.radioButtonAdaptive.toggled.connect(self.updateLabel)
        self.ui.radioButtonDirect.toggled.connect(self.updateLabel)
        self.ui.radioButtonNone.toggled.connect(self.updateLabel)
        self.ui.spreadFactorALineEdit.textChanged.connect(self.updateLabel)
        self.ui.spreadFactorBLineEdit.textChanged.connect(self.updateLabel)
        self.ui.spreadFactorCLineEdit.textChanged.connect(self.updateLabel)

        self.ui.checkBoxApplyToAllSeries.toggled[bool].connect(
            self.toggleApplyToAllSeries
        )

        self.updateLabel()

        self.ui.buttonBox.button(
            QDialogButtonBox.StandardButton.RestoreDefaults
        ).clicked.connect(self._restore_defaults)

        self.show()

    def updateLabel(self):
        # Default
        eqn = "DD = DS"
        # None visibility update
        isNone = self.ui.radioButtonNone.isChecked()
        self.ui.spreadFactorALabel.setEnabled(not isNone)
        self.ui.spreadFactorALineEdit.setEnabled(not isNone)
        self.ui.spreadFactorBLabel.setEnabled(not isNone)
        self.ui.spreadFactorBLineEdit.setEnabled(not isNone)
        self.ui.spreadFactorCLabel.setEnabled(not isNone)
        self.ui.spreadFactorCLineEdit.setEnabled(not isNone)
        if isNone:
            self.ui.labelEquation.setText(eqn)
            self.method = cfg.SPREAD_METHOD_NONE
            return
        # shortcuts for sf's
        a = self.ui.spreadFactorALineEdit.text()
        b = self.ui.spreadFactorBLineEdit.text()
        c = self.ui.spreadFactorCLineEdit.text()
        # Validate numeric spread factors
        try:
            float(a)
            float(b)
            float(c)
        except ValueError:
            self.ui.labelEquation.setText("Invalid Spread Factor(s)")
            return
        # Update Text dependant upon method
        pcs = []
        if float(a) > 0.000001:
            pcs.append(f"{a}(DS)^2")
        if float(b) > 0.000001:
            pcs.append(f"{b}(DS)")
        if float(c) > 0.000001:
            pcs.append(f"{c}")
        if self.ui.radioButtonAdaptive.isChecked():
            eqn = "DD = DS / (" + "+".join(pcs) + ")"
            self.method = cfg.SPREAD_METHOD_ADAPTIVE
        elif self.ui.radioButtonDirect.isChecked():
            eqn = "DD = " + "+".join(pcs)
            self.method = cfg.SPREAD_METHOD_DIRECT

        self.ui.labelEquation.setText(eqn)

    def toggleApplyToAllSeries(self, boo: bool):
        if boo:
            self.ui.checkBoxApplyToAllPass.setCheckState(Qt.CheckState.Checked)
        else:
            self.ui.checkBoxApplyToAllPass.setCheckState(Qt.CheckState.Unchecked)
        self.ui.checkBoxApplyToAllPass.setEnabled(not boo)

    def _restore_defaults(self):
        self.method = cfg.get_spread_factor_equation()
        with QSignalBlocker(self.ui.radioButtonNone):
            self.ui.radioButtonNone.setChecked(self.method == cfg.SPREAD_METHOD_NONE)
        with QSignalBlocker(self.ui.radioButtonDirect):
            self.ui.radioButtonDirect.setChecked(
                self.method == cfg.SPREAD_METHOD_DIRECT
            )
        with QSignalBlocker(self.ui.radioButtonAdaptive):
            self.ui.radioButtonAdaptive.setChecked(
                self.method == cfg.SPREAD_METHOD_ADAPTIVE
            )
        with QSignalBlocker(self.ui.spreadFactorALineEdit):
            self.ui.spreadFactorALineEdit.setText(f"{cfg.get_spread_factor_a():g}")
        with QSignalBlocker(self.ui.spreadFactorBLineEdit):
            self.ui.spreadFactorBLineEdit.setText(f"{cfg.get_spread_factor_b():g}")
        with QSignalBlocker(self.ui.spreadFactorCLineEdit):
            self.ui.spreadFactorCLineEdit.setText(f"{cfg.get_spread_factor_c():g}")
        self.updateLabel()

    def accept(self):
        excepts = []
        try:
            a = float(self.ui.spreadFactorALineEdit.text())
        except:
            excepts.append("-SPREAD FACTOR A cannot be converted to a NUMBER")
        try:
            b = float(self.ui.spreadFactorBLineEdit.text())
        except:
            excepts.append("-SPREAD FACTOR B cannot be converted to a NUMBER")
        try:
            c = float(self.ui.spreadFactorCLineEdit.text())
        except:
            excepts.append("-SPREAD FACTOR C cannot be converted to a NUMBER")
        if len(excepts) > 0:
            QMessageBox.warning(self, "Invalid Data", "\n".join(excepts))
            return

        # Apply to multiple cards if requested
        # Cycle through passes
        for p in self.seriesData.passes:
            # Check if should apply to pass
            if (
                p.name == self.passData.name
                or self.ui.checkBoxApplyToAllSeries.checkState()
                == Qt.CheckState.Checked
            ):
                # Cycle through cards in pass
                for card in p.spray_cards:
                    if (
                        card.name == self.sprayCard.name
                        or self.ui.checkBoxApplyToAllPass.checkState()
                        == Qt.CheckState.Checked
                    ):
                        # Spread Method
                        card.spread_method = self.method
                        # Spread Factors
                        card.spread_factor_a = a
                        card.spread_factor_b = b
                        card.spread_factor_c = c
                        # Currency Flags
                        card.stats.current = False

        # Update Defaults if requested
        if self.ui.checkBoxUpdateDefaults.isChecked():
            cfg.set_spread_factor_a(a)
            cfg.set_spread_factor_b(b)
            cfg.set_spread_factor_c(c)
            cfg.set_spread_factor_equation(self.method)

        # Notify Requestor, Close, Return
        super().accept()
