import os

import accupatt.config as cfg
import numpy as np
import pandas as pd
from accupatt.helpers.atomizationModel import AtomizationModel
from accupatt.models.appInfo import AppInfo, Nozzle
from accupatt.models.passData import Pass
from PyQt6 import uic
from PyQt6.QtCore import QDate, QDateTime, pyqtSignal, pyqtSlot, QSignalBlocker
from PyQt6.QtWidgets import QComboBox, QMessageBox

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'passInfo.ui'))

class PassInfoWidget(baseclass):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
       
    def fill_from_pass(self, passData: Pass):
        self.ui.lineEditGS.setText(passData.str_ground_speed())
        self.ui.comboBoxUnitsGS.addItems(cfg.UNITS_GROUND_SPEED)
        self.ui.comboBoxUnitsGS.setCurrentText(passData.ground_speed_units)
        self.ui.lineEditSH.setText(passData.str_spray_height())
        self.ui.comboBoxUnitsSH.addItems(cfg.UNITS_SPRAY_HEIGHT)
        self.ui.comboBoxUnitsSH.setCurrentText(passData.spray_height_units)
        self.ui.lineEditPH.setText(passData.str_pass_heading())
        self.ui.lineEditWD.setText(passData.str_wind_direction())
        self.ui.lineEditWS.setText(passData.str_wind_speed())
        self.ui.comboBoxUnitsWS.addItems(cfg.UNITS_WIND_SPEED)
        self.ui.comboBoxUnitsWS.setCurrentText(passData.wind_speed_units)
        self.ui.lineEditT.setText(passData.str_temperature())
        self.ui.comboBoxUnitsT.addItems(cfg.UNITS_TEMPERATURE)
        self.ui.comboBoxUnitsT.setCurrentText(passData.temperature_units)
        self.ui.lineEditH.setText(passData.str_humidity())
    
    '''
    Check if each field has an invalid value, else set the currently selected
    value to the passData object. Returns a string list of exceptions, or an
    empty list if no exceptions.
    '''
    def validate_fields(self, passData: Pass) -> list[str]:
        p = passData
        excepts = []
        #Ground Speed
        if not p.set_ground_speed(self.ui.lineEditGS.text()):
            excepts.append('-GROUND SPEED cannot be converted to a NUMBER')
        p.ground_speed_units = self.ui.comboBoxUnitsGS.currentText()
        #Spray Height
        if not p.set_spray_height(self.ui.lineEditSH.text()):
            excepts.append('-SPRAY HEIGHT cannot be converted to a NUMBER')
        p.spray_height_units = self.ui.comboBoxUnitsSH.currentText()
        #Pass Heading
        if not p.set_pass_heading(self.ui.lineEditPH.text()):
            excepts.append('-PASS HEADING cannot be converted to an INTEGER')
        #Wind Direction
        if not p.set_wind_direction(self.ui.lineEditWD.text()):
            excepts.append('-WIND DIRECTION cannot be converted to a NUMBER')
        #Wind Speed
        if not p.set_wind_speed(self.ui.lineEditWS.text()):
            excepts.append('-WIND SPEED cannot be converted to a NUMBER')
        p.wind_speed_units = self.ui.comboBoxUnitsWS.currentText()
        #Temperature
        if not p.set_temperature(self.ui.lineEditT.text()):
            excepts.append('-TEMPERATURE cannot be converted to a NUMBER')
        p.temperature_units = self.ui.comboBoxUnitsT.currentText()
        #Humidity
        if not p.set_humidity(self.ui.lineEditH.text()):
            excepts.append('-HUMIDITY cannot be converted to a NUMBER')
        return excepts