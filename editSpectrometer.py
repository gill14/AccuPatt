import sys
import numpy as np

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import uic

from seabreeze.spectrometers import Spectrometer

Ui_Form, baseclass = uic.loadUiType('editSpectrometer.ui')

class EditSpectrometer(baseclass):

    applied = qtc.pyqtSignal()

    def __init__(self, spectrometer=None):
        super().__init__()
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #Load in Settings or use defaults
        self.settings = qtc.QSettings('BG Application Consulting','AccuPatt')
        #Excitation Wavelength
        if self.settings.contains('target_excitation_wavelength'):
            self.target_excitation_wavelength = self.settings.value('target_excitation_wavelength', type=int)
        else:
            self.target_excitation_wavelength = 525
        #Emission Wavelength
        if self.settings.contains('target_emission_wavelength'):
            self.target_emission_wavelength = self.settings.value('target_emission_wavelength', type=int)
        else:
            self.target_emission_wavelength = 575
        #Integration Time
        if self.settings.contains('integration_time_ms'):
            self.integration_time_ms = self.settings.value('integration_time_ms', type=int)
        else:
            self.integration_time_ms = 100

        self.spec = spectrometer

        #Hook up signals
        self.ui.buttonRefresh.clicked.connect(self.refresh_spec)
        self.ui.lineEditEx.textChanged.connect(self.refresh_spec)
        self.ui.lineEditEm.textChanged.connect(self.refresh_spec)

        self.ui.lineEditEx.setText(str(self.target_excitation_wavelength))
        self.ui.lineEditEm.setText(str(self.target_emission_wavelength))
        self.ui.lineEditIntegrationTime.setText(str(self.integration_time_ms))

        #Utilize built-in signals
        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Your code ends here
        self.show()

    def refresh_spec(self):
        if self.spec == None:
            try:
                self.spec = Spectrometer.from_first_available()
            except:
                self.ui.labelSpec.setText('Spectrometer: None')
                self.ui.labelEx.setText('')
                self.ui.labelEm.setText('')
                self.ui.labelSerialNumber.setText('')
                return
        self.ui.labelSerialNumber.setText(f'Spectrometer Serial Number: {self.spec.serial_number}')
        self.ui.labelSpec.setText(f'Spectrometer: {self.spec.model}')
        wav = self.spec.wavelengths()
        #Check that target_excitation_wavelength is a number
        try:
            self.excitationPix = np.abs(wav-float(self.ui.lineEditEx.text())).argmin()
            self.actual_excitation_wavelength = wav[self.excitationPix]
            self.ui.labelEx.setText(f'Actual Excitation is {self.strip_num(self.actual_excitation_wavelength)}nm at pixel #{self.excitationPix}')
        except:
            self.ui.labelEx.setText('Invalid Target Excitation Wavelength')
            print('Invalid Excitation Wavelength')
        #Check that target_emission_wavelength is a number
        try:
            self.emissionPix = np.abs(wav-int(self.ui.lineEditEm.text())).argmin()
            self.actual_emission_wavelength = wav[self.emissionPix]
            self.ui.labelEm.setText(f'Actual Emission is {self.strip_num(self.actual_emission_wavelength)}nm at pixel #{self.emissionPix}')
        except:
            self.ui.labelEm.setText('Invalid Target Emission Wavelength')
            print('Invalid Emission Wavelength')

    def strip_num(self, x) -> str:
        if type(x) is str:
            if x == '':
                x = 0
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return f'{round(float(x), 2):.2f}'

    def on_applied(self):
        #Validate all and accept if valid
        try:
            self.settings.setValue('target_excitation_wavelength', int(self.ui.lineEditEx.text()))
        except:
            self._show_validation_error(
                'Entered TARGET EXCITATION WAVELENGTH cannot be converted to an INTEGER')
            return
        try:
            self.settings.setValue('target_emission_wavelength', int(self.ui.lineEditEm.text()))
        except:
            self._show_validation_error(
                'Entered TARGET EMISSION WAVELENGTH cannot be converted to an INTEGER')
            return
        try:
            self.settings.setValue('integration_time_ms', int(self.ui.lineEditIntegrationTime.text()))
        except:
            self._show_validation_error(
                'Entered INTEGRATION TIME cannot be converted to an INTEGER')
            return
        
        #All Valid, go ahead and accept and let main know to update vals
        self.applied.emit()

        self.accept()
        self.close()

    def _show_validation_error(self, message):
        msg = qtw.QMessageBox()
        msg.setIcon(qtw.QMessageBox.Critical)
        msg.setText("Input Validation Error")
        msg.setInformativeText(message)
        #msg.setWindowTitle("MessageBox demo")
        #msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(qtw.QMessageBox.Ok)
        result = msg.exec()
        if result == qtw.QMessageBox.Ok:
            self.raise_()
            self.activateWindow()

if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    w = EditSpectrometer()
    sys.exit(app.exec_())
