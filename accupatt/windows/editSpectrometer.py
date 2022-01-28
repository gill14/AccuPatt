import os

import accupatt.config as cfg
import numpy as np
from PyQt6 import uic
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox
from seabreeze.spectrometers import Spectrometer

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'editSpectrometer.ui'))

icon_file = os.path.join(os.getcwd(), 'resources', 'refresh.png')

class EditSpectrometer(baseclass):

    def __init__(self, spectrometer=None, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #Load in Settings or use defaults
        self.settings = QSettings('accupatt','AccuPatt')
        #Excitation Wavelength
        if self.settings.contains('target_excitation_wavelength'):
            self.target_excitation_wavelength = self.settings.value('target_excitation_wavelength', type=int)
        else:
            self.target_excitation_wavelength = cfg.SPEC_WAV_EX__DEFAULT
        #Emission Wavelength
        if self.settings.contains('target_emission_wavelength'):
            self.target_emission_wavelength = self.settings.value('target_emission_wavelength', type=int)
        else:
            self.target_emission_wavelength = cfg.SPEC_WAV_EM__DEFAULT
        #Integration Time
        if self.settings.contains('integration_time_ms'):
            self.integration_time_ms = self.settings.value('integration_time_ms', type=int)
        else:
            self.integration_time_ms = cfg.SPEC_INT_TIME_MS__DEFAULT

        self.spec = spectrometer
        
        
        self.ui.lineEditEx.setText(str(self.target_excitation_wavelength))
        self.ui.lineEditEm.setText(str(self.target_emission_wavelength))
        self.ui.lineEditIntegrationTime.setText(str(self.integration_time_ms))

        #Hook up signals
        self.ui.buttonRefresh.setIcon(QIcon(icon_file))
        self.ui.buttonRefresh.clicked.connect(self.refresh_spec)
        self.ui.lineEditEx.textChanged.connect(self.refresh_spec)
        self.ui.lineEditEm.textChanged.connect(self.refresh_spec)
        
        self.refresh_spec()

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

    def accept(self):
        excepts = []
        # Save Excitation Wavelength
        try:
            self.settings.setValue('target_excitation_wavelength', int(self.ui.lineEditEx.text()))
        except:
            excepts.append('-TARGET EXCITATION WAVELENGTH cannot be converted to an INTEGER')
        try:
            self.settings.setValue('target_emission_wavelength', int(self.ui.lineEditEm.text()))
        except:
            excepts.append('-TARGET EMISSION WAVELENGTH cannot be converted to an INTEGER')
        try:
            self.settings.setValue('integration_time_ms', int(self.ui.lineEditIntegrationTime.text()))
        except:
            excepts.append('-INTEGRATION TIME cannot be converted to an INTEGER')
        # If any invalid, show user and return to current window
        if len(excepts) > 0:
            QMessageBox.warning(self, 'Invalid Data', '\n'.join(excepts))
            return
        # If all checks out, notify requestor and close
        super().accept()
