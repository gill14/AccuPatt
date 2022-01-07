import sys, os

from PyQt5.QtWidgets import QApplication, QComboBox, QMessageBox, QWidget
from PyQt5 import uic
from PyQt5.QtCore import QDate, QDateTime, pyqtSlot
import numpy as np
import pandas as pd

import accupatt.config as cfg
from accupatt.helpers.atomizationModel import AtomizationModel 
from accupatt.models.appInfo import AppInfo

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'seriesInfo.ui'))

class SeriesInfoWidget(baseclass):
    
    aircraftFile = os.path.join(os.getcwd(), 'resources', 'AgAircraftData.xlsx')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.init_aircraft()
        self.init_spray_system()
        self.init_nozzles()
       
    def fill_from_info(self, info: AppInfo):
        self.fill_flyin(info)
        self.fill_series(info)
        self.fill_applicator(info) 
        self.fill_notes(info)
        self.fill_aircraft(info)
        self.fill_spray_system(info)
        self.fill_nozzles(info)
        
    
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Fly-In
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def fill_flyin(self, info: AppInfo):
        self.ui.lineEditName.setText(info.flyin_name)
        self.ui.lineEditLocation.setText(info.flyin_location)
        self.ui.lineEditDate.setText(info.flyin_date)
        self.ui.dateEdit.setDateTime(QDateTime.currentDateTime())
        self.ui.dateEdit.dateChanged[QDate].connect(self._date_changed)
        self.ui.lineEditAnalyst.setText(info.flyin_analyst)
    
    @pyqtSlot(QDate)   
    def _date_changed(self, date: QDate):
        self.ui.lineEditDate.setText(date.toString('d MMM yyyy'))
        
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Series
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def fill_series(self, info: AppInfo):
        self.ui.lineEditRegNum.setText(info.regnum)
        self.ui.lineEditSeriesNum.setText(str(info.series))
        
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Applicator
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def fill_applicator(self, info: AppInfo):
        self.ui.pilotLineEdit.setText(info.pilot)
        self.ui.businessLineEdit.setText(info.business)
        self.ui.streetLineEdit.setText(info.street)
        self.ui.cityLineEdit.setText(info.city)
        self.ui.stateLineEdit.setText(info.state)
        self.ui.zipLineEdit.setText(info.strip_num(info.zip))
        self.ui.phoneLineEdit.setText(info.phone)
        self.ui.emailLineEdit.setText(info.email)
        
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Spray System
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def fill_notes(self, info: AppInfo):
        self.ui.plainTextEditNotesSetup.setPlainText(info.notes_setup)
        self.ui.plainTextEditNotesAnalyst.setPlainText(info.notes_analyst)
        
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Aircraft
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def init_aircraft(self):
        self.aircraft_map = pd.read_excel(self.aircraftFile, sheet_name=None)
        self.ui.comboBoxMake.addItems(self.aircraft_map.keys())
        self.ui.comboBoxMake.setCurrentIndex(-1)
        self.ui.comboBoxMake.currentTextChanged[str].connect(self._on_make_selected)
        self.ui.comboBoxModel.currentTextChanged[str].connect(self._on_model_selected)
        self.ui.comboBoxWingspanUnits.addItems(cfg.UNITS_LENGTH_LARGE)
        self.ui.comboBoxWingspanUnits.setCurrentText(cfg.UNIT_FT)
        self.ui.comboBoxWingspanUnits.currentTextChanged[str].connect(self._on_wingspan_units_changed)
        self.ui.comboBoxWinglets.addItems(['Yes','No'])
        self.ui.comboBoxWinglets.setCurrentIndex(-1)
    
    def fill_aircraft(self, info: AppInfo):
        self.ui.comboBoxMake.setCurrentText(info.make)
        self.ui.comboBoxModel.setCurrentText(info.model)
        self.ui.comboBoxWingspanUnits.setCurrentText(info.wingspan_units)
        self.ui.lineEditWingspan.setText(f'{info.strip_num(info.wingspan)}')
        self.ui.comboBoxWinglets.setCurrentText(info.winglets)
    
    @pyqtSlot(str)
    def _on_make_selected(self, make):
        self.ui.comboBoxModel.clear()
        if make in self.aircraft_map.keys():
            df = self.aircraft_map[make]
            self.ui.comboBoxModel.addItems(df['Model'])
            self.ui.comboBoxModel.setCurrentIndex(-1)
            
    @pyqtSlot(str)
    def _on_model_selected(self, model):
        self.ui.lineEditWingspan.clear()
        make = self.ui.comboBoxMake.currentText()
        if make in self.aircraft_map.keys():
            df = self.aircraft_map[make]
            if model != '' and df[df['Model'].str.contains(model)].any().any():
                df = df.set_index('Model')
                ws = df.at[model,'Wingspan (FT)']
                if self.ui.comboBoxWingspanUnits.currentText() == 'm':
                    ws = ws / cfg.FT_PER_M
                    self.ui.lineEditWingspan.setText(f"{round(ws, 2):.2f}")
                else:
                    self.ui.lineEditWingspan.setText(str(round(ws)))
    
    @pyqtSlot(str)
    def _on_wingspan_units_changed(self, units):
        if self.ui.lineEditWingspan.text() != '':
            ws = float(self.ui.lineEditWingspan.text())
            if units == cfg.UNIT_FT:
                ws = ws * cfg.FT_PER_M
            else:
                ws = ws / cfg.FT_PER_M
            self.ui.lineEditWingspan.setText(f"{round(ws,2):.2f}") 
    
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Spray System
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def init_spray_system(self):
        self.ui.comboBoxUnitsSwath.addItems(cfg.UNITS_LENGTH_LARGE)
        self.ui.comboBoxUnitsSwath.setCurrentText(cfg.UNIT_FT)
        self.ui.comboBoxUnitsRate.addItems(cfg.UNITS_RATE)
        self.ui.comboBoxUnitsRate.setCurrentText(cfg.UNIT_GPA)
        self.ui.comboBoxUnitsPressure.addItems(cfg.UNITS_PRESSURE)
        self.ui.comboBoxUnitsPressure.setCurrentText(cfg.UNIT_PSI)
        self.ui.comboBoxUnitsBoomWidth.addItems(cfg.UNITS_LENGTH_LARGE)
        self.ui.comboBoxUnitsBoomWidth.addItem('%')
        self.ui.comboBoxUnitsBoomWidth.setCurrentText(cfg.UNIT_FT)
        self.ui.comboBoxUnitsBoomDrop.addItems(cfg.UNITS_LENGTH_SMALL)
        self.ui.comboBoxUnitsBoomDrop.setCurrentText(cfg.UNIT_IN)
        self.ui.comboBoxUnitsNozzleSpacing.addItems(cfg.UNITS_LENGTH_SMALL)
        self.ui.comboBoxUnitsNozzleSpacing.setCurrentText(cfg.UNIT_IN)
    
    def fill_spray_system(self, info: AppInfo):
        self.ui.lineEditSwath.setText(str(info.swath))
        self.ui.comboBoxUnitsSwath.setCurrentText(info.swath_units)
        self.ui.lineEditRate.setText(f'{info.strip_num(info.rate)}')
        self.ui.comboBoxUnitsRate.setCurrentText(info.rate_units)
        self.ui.lineEditPressure.setText(f'{info.strip_num(info.pressure)}')
        self.ui.comboBoxUnitsPressure.setCurrentText(info.pressure_units)
        self.ui.lineEditBoomWidth.setText(f'{info.strip_num(info.boom_width)}')
        self.ui.comboBoxUnitsBoomWidth.setCurrentText(info.boom_width_units)
        self.ui.lineEditBoomDrop.setText(f'{info.strip_num(info.boom_drop)}')
        self.ui.comboBoxUnitsBoomDrop.setCurrentText(info.boom_drop_units)
        self.ui.lineEditNozzleSpacing.setText(f'{info.strip_num(info.nozzle_spacing)}')
        self.ui.comboBoxUnitsNozzleSpacing.setCurrentText(info.nozzle_spacing_units)
    
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Nozzles
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def init_nozzles(self):
        self.ui.comboBoxNT1.addItems(AtomizationModel.nozzles)
        self.ui.comboBoxNT1.setCurrentIndex(-1)
        self.ui.comboBoxNT1.currentTextChanged[str].connect(self._on_nozzle_1_selected)
        self.ui.comboBoxNT2.addItems(AtomizationModel.nozzles)
        self.ui.comboBoxNT2.setCurrentIndex(-1)
        self.ui.comboBoxNT2.currentTextChanged[str].connect(self._on_nozzle_2_selected)
        
    def fill_nozzles(self, info: AppInfo):
        self.ui.comboBoxNT1.setCurrentText(info.nozzle_type_1)
        self.ui.comboBoxNS1.setCurrentText(f'{info.nozzle_size_1}')
        self.ui.comboBoxND1.setCurrentText(f'{info.nozzle_deflection_1}')
        self.ui.lineEditNQ1.setText(str(info.nozzle_quantity_1))
        self.ui.comboBoxNT2.setCurrentText(info.nozzle_type_2)
        self.ui.comboBoxNT2.setCurrentText(f'{info.nozzle_size_2}')
        self.ui.comboBoxND2.setCurrentText(f'{info.nozzle_deflection_2}')
        self.ui.lineEditNQ2.setText(str(info.nozzle_quantity_2))
    
    @pyqtSlot(str)
    def _on_nozzle_1_selected(self, nozzle):
        self._on_nozzle_selected(nozzle, cBSize = self.ui.comboBoxNS1, cBDef = self.ui.comboBoxND1)
        
    @pyqtSlot(str)
    def _on_nozzle_2_selected(self, nozzle):
        self._on_nozzle_selected(nozzle, cBSize = self.ui.comboBoxNS2, cBDef = self.ui.comboBoxND2)
        
    def _on_nozzle_selected(self, nozzle, cBSize: QComboBox, cBDef: QComboBox):
        cBSize.clear()
        cBDef.clear()
        if nozzle not in AtomizationModel.nozzles:
            return
        #Check ls
        orif_a = []
        def_a = []
        if nozzle in AtomizationModel.ls_dict.keys():
            orif_a = AtomizationModel.ls_dict[nozzle]['Orifice']
            def_a = AtomizationModel.ls_dict[nozzle]['Angle']
        #Check hs
        orif_b = []
        def_b = []
        if nozzle in AtomizationModel.hs_dict.keys():
            orif_b = AtomizationModel.hs_dict[nozzle]['Orifice']
            def_b = AtomizationModel.hs_dict[nozzle]['Angle']
        #combine and remove duplicates
        orif_c = sorted(np.unique(orif_a+orif_b))
        def_c = sorted(np.unique(def_a+def_b))
        #Asign to comboboxes
        for item in orif_c:
            cBSize.addItem(str(item))
        for item in def_c:
            cBDef.addItem(str(item))
        #remove selection
        cBSize.setCurrentIndex(-1)
        cBDef.setCurrentIndex(-1)
    
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Validation
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def show_validation_error(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.critical)
        msg.setText("Input Validation Error")
        msg.setInformativeText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        result = msg.exec()
        if result == QMessageBox.Ok:
            self.raise_()
            self.activateWindow()