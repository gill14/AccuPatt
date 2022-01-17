import os

import accupatt.config as cfg
import numpy as np
import pandas as pd
from accupatt.helpers.atomizationModel import AtomizationModel
from accupatt.models.appInfo import AppInfo
from PyQt5 import uic
from PyQt5.QtCore import (QDate, QDateTime, QSettings, QSignalBlocker,
                          pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import QComboBox, QMessageBox

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'seriesInfo.ui'))

class SeriesInfoWidget(baseclass):
    
    aircraftFile = os.path.join(os.getcwd(), 'resources', 'AgAircraftData.xlsx')
    
    target_swath_changed = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.info = None
        self.init_aircraft()
        self.init_spray_system()
        self.init_nozzles()
       
    def fill_from_info(self, info: AppInfo):
        self.info = info
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
        # Name
        self.ui.lineEditName.setText(info.flyin_name)
        self.ui.lineEditName.editingFinished.connect(self._commit_name)
        # Location
        self.ui.lineEditLocation.setText(info.flyin_location)
        self.ui.lineEditLocation.editingFinished.connect(self._commit_location)
        # Date
        self.ui.lineEditDate.setText(info.flyin_date)
        self.ui.dateEdit.setDateTime(QDateTime.currentDateTime())
        self.ui.dateEdit.dateChanged[QDate].connect(self._dateEdit_changed)
        # Analyst
        self.ui.lineEditAnalyst.setText(info.flyin_analyst)
    
    @pyqtSlot()
    def _commit_name(self):
        self.info.flyin_name = self.ui.lineEditName.text()
        
    @pyqtSlot()
    def _commit_location(self):
        self.info.flyin_location = self.ui.lineEditLocation.text()
        
    @pyqtSlot()
    def _commit_date(self):
        self.info.flyin_date = self.ui.lineEditDate.text()
    
    @pyqtSlot(QDate)   
    def _dateEdit_changed(self, date: QDate):
        self.ui.lineEditDate.setText(date.toString('d MMM yyyy'))
        self._commit_date()
        
    @pyqtSlot()
    def _commit_analyst(self):
        self.info.flyin_analyst = self.ui.lineEditAnalyst.text()
        
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Series
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def fill_series(self, info: AppInfo):
        # Registration Number
        self.ui.lineEditRegNum.setText(info.regnum)
        self.ui.lineEditRegNum.editingFinished.connect(self._commit_regnum)
        # Series Number
        self.ui.lineEditSeriesNum.setText(str(info.series))
        self.ui.lineEditSeriesNum.editingFinished.connect(self._commit_seriesnum)
        
    @pyqtSlot()
    def _commit_regnum(self):
        self.info.regnum = self.ui.lineEditRegNum.text()
        
    @pyqtSlot()
    def _commit_seriesnum(self):
        self.info.series = int(self.ui.lineEditSeriesNum.text())
        
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Applicator
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def fill_applicator(self, info: AppInfo):
        # Pilot
        self.ui.pilotLineEdit.setText(info.pilot)
        self.ui.pilotLineEdit.editingFinished.connect(self._commit_pilot)
        # Business
        self.ui.businessLineEdit.setText(info.business)
        self.ui.businessLineEdit.editingFinished.connect(self._commit_business)
        # Street
        self.ui.streetLineEdit.setText(info.street)
        self.ui.streetLineEdit.editingFinished.connect(self._commit_street)
        # City
        self.ui.cityLineEdit.setText(info.city)
        self.ui.cityLineEdit.editingFinished.connect(self._commit_city)
        # State
        self.ui.stateLineEdit.setText(info.state)
        self.ui.stateLineEdit.editingFinished.connect(self._commit_state)
        # ZIP
        self.ui.zipLineEdit.setText(info.zip)
        self.ui.zipLineEdit.editingFinished.connect(self._commit_zip)
        # Phone
        self.ui.phoneLineEdit.setText(info.phone)
        self.ui.phoneLineEdit.editingFinished.connect(self._commit_phone)
        # Email
        self.ui.emailLineEdit.setText(info.email)
        self.ui.emailLineEdit.editingFinished.connect(self._commit_email)
        
    @pyqtSlot()
    def _commit_pilot(self):
        self.info.pilot = self.ui.pilotLineEdit.text()
        
    @pyqtSlot()
    def _commit_business(self):
        self.info.business = self.ui.businessLineEdit.text()
        
    @pyqtSlot()
    def _commit_street(self):
        self.info.street = self.ui.streetLineEdit.text()
        
    @pyqtSlot()
    def _commit_city(self):
        self.info.city = self.ui.cityLineEdit.text()
        
    @pyqtSlot()
    def _commit_state(self):
        self.info.state = self.ui.stateLineEdit.text()
        
    @pyqtSlot()
    def _commit_zip(self):
        self.info.zip = self.ui.zipLineEdit.text()
        
    @pyqtSlot()
    def _commit_phone(self):
        self.info.phone = self.ui.phoneLineEdit.text()
        
    @pyqtSlot()
    def _commit_email(self):
        self.info.email = self.ui.emailLineEdit.text()
        
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Notes
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def fill_notes(self, info: AppInfo):
        # Setup Notes
        self.ui.plainTextEditNotesSetup.setPlainText(info.notes_setup)
        self.ui.plainTextEditNotesSetup.textChanged.connect(self._commit_notes_setup)
        # Analyst Notes
        self.ui.plainTextEditNotesAnalyst.setPlainText(info.notes_analyst)
        self.ui.plainTextEditNotesAnalyst.textChanged.connect(self._commit_notes_analyst)
        
    @pyqtSlot()
    def _commit_notes_setup(self):
        self.info.notes_setup = self.ui.plainTextEditNotesSetup.toPlainText()
        
    @pyqtSlot()
    def _commit_notes_analyst(self):
        self.info.notes_analyst = self.ui.plainTextEditNotesAnalyst.toPlainText()
        
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Aircraft
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def init_aircraft(self):
        self.ui.comboBoxMake.addItem('')
        self.aircraft_map = pd.read_excel(self.aircraftFile, sheet_name=None)
        self.ui.comboBoxMake.addItems(self.aircraft_map.keys())
        self.ui.comboBoxMake.setCurrentIndex(-1)
        self.ui.comboBoxMake.currentTextChanged[str].connect(self._on_make_selected)
        
        self.ui.comboBoxWingspanUnits.addItems(cfg.UNITS_LENGTH_LARGE)
        self.ui.comboBoxWingspanUnits.setCurrentText(cfg.UNIT_FT)
        self.ui.comboBoxWinglets.addItems(['Yes','No'])
        self.ui.comboBoxWinglets.setCurrentIndex(-1)
    
    def fill_aircraft(self, info: AppInfo):
        # Aircraft Make
        self.ui.comboBoxMake.setCurrentText(info.make)
        # Aircraft Model
        self.ui.comboBoxModel.setCurrentText(info.model)
        self.ui.comboBoxModel.currentTextChanged[str].connect(self._on_model_selected)
        # Wingspan Units
        self.ui.comboBoxWingspanUnits.setCurrentText(info.wingspan_units)
        self.ui.comboBoxWingspanUnits.currentTextChanged[str].connect(self._commit_wingspan_units)
        # Wingspan
        self.ui.lineEditWingspan.setText(info.strip_num(info.wingspan, zeroBlank=True))
        self.ui.lineEditWingspan.editingFinished.connect(self._commit_wingspan)
        # Winglets
        self.ui.comboBoxWinglets.setCurrentText(info.winglets)
        self.ui.comboBoxWinglets.currentTextChanged[str].connect(self._commit_winglets)
    
    @pyqtSlot(str)
    def _on_make_selected(self, make):
        self.ui.comboBoxModel.clear()
        self.ui.comboBoxModel.addItem('')
        if make in self.aircraft_map.keys():
            df = self.aircraft_map[make]
            self.ui.comboBoxModel.addItems(df['Model'])
            self.ui.comboBoxModel.setCurrentIndex(-1)
        if self.info is not None:
            self._commit_aircraft_make(make)
            
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
        if self.info is not None:
            self._commit_aircraft_model(model)
            
    def _commit_aircraft_make(self, text):
        self.info.make = text
        
    def _commit_aircraft_model(self, text):
        self.info.model = text
       
    @pyqtSlot(str)   
    def _commit_wingspan_units(self, text):
        self.info.wingspan_units = text 
        
    @pyqtSlot()
    def _commit_wingspan(self):
        self.info.set_wingspan(self.ui.lineEditWingspan.text())
        
    @pyqtSlot(str)
    def _commit_winglets(self, text):
        self.info.winglets = text
    
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
        # Target Swath
        self.ui.lineEditSwath.setText(info.strip_num(info.swath, zeroBlank=True))
        self.ui.lineEditSwath.editingFinished.connect(self._commit_swath)
        # Target Swath Units
        self.ui.comboBoxUnitsSwath.setCurrentText(info.swath_units)
        self.ui.comboBoxUnitsSwath.currentTextChanged[str].connect(self._commit_swath_units)
        # Target Rate
        self.ui.lineEditRate.setText(f'{info.strip_num(info.rate, zeroBlank=True)}')
        self.ui.lineEditRate.editingFinished.connect(self._commit_rate)
        # Target Rate Units
        self.ui.comboBoxUnitsRate.setCurrentText(info.rate_units)
        self.ui.comboBoxUnitsRate.currentTextChanged[str].connect(self._commit_rate_units)
        # Pressure
        self.ui.lineEditPressure.setText(f'{info.strip_num(info.pressure, zeroBlank=True)}')
        self.ui.lineEditPressure.editingFinished.connect(self._commit_pressure)
        # Pressure Units
        self.ui.comboBoxUnitsPressure.setCurrentText(info.pressure_units)
        self.ui.comboBoxUnitsPressure.currentTextChanged[str].connect(self._commit_pressure_units)
        # Boom Width
        self.ui.lineEditBoomWidth.setText(f'{info.strip_num(info.boom_width, zeroBlank=True)}')
        self.ui.lineEditBoomWidth.editingFinished.connect(self._commit_boom_width)
        # Boom Width Units
        self.ui.comboBoxUnitsBoomWidth.setCurrentText(info.boom_width_units)
        self.ui.comboBoxUnitsBoomWidth.currentTextChanged[str].connect(self._commit_boom_width_units)
        # Boom Drop
        self.ui.lineEditBoomDrop.setText(f'{info.strip_num(info.boom_drop, zeroBlank=True)}')
        self.ui.lineEditBoomDrop.editingFinished.connect(self._commit_boom_drop)
        # Boom Drop Units
        self.ui.comboBoxUnitsBoomDrop.setCurrentText(info.boom_drop_units)
        self.ui.comboBoxUnitsBoomDrop.currentTextChanged[str].connect(self._commit_boom_drop_units)
        # Nozzle Spacing
        self.ui.lineEditNozzleSpacing.setText(f'{info.strip_num(info.nozzle_spacing, zeroBlank=True)}')
        self.ui.lineEditNozzleSpacing.editingFinished.connect(self._commit_nozzle_spacing)
        # Nozzle Spacing Units
        self.ui.comboBoxUnitsNozzleSpacing.setCurrentText(info.nozzle_spacing_units)
        self.ui.comboBoxUnitsNozzleSpacing.currentTextChanged[str].connect(self._commit_nozzle_spacing_units)
        
    @pyqtSlot()
    def _commit_swath(self):
        self.info.set_swath(self.ui.lineEditSwath.text())
        self.info.set_swath_adjusted(self.ui.lineEditSwath.text())
        self.target_swath_changed.emit()
        
    @pyqtSlot(str)
    def _commit_swath_units(self, text):
        self.info.swath_units = text
        self.target_swath_changed.emit()
        
    @pyqtSlot()
    def _commit_rate(self):
        self.info.set_rate(self.ui.lineEditRate.text())
        
    @pyqtSlot(str)
    def _commit_rate_units(self, text):
        self.info.rate_units = text
        
    @pyqtSlot()
    def _commit_pressure(self):
        self.info.set_pressure(self.ui.lineEditPressure.text())
        
    @pyqtSlot(str)
    def _commit_pressure_units(self, text):
        self.info.pressure_units = text
        
    @pyqtSlot()
    def _commit_boom_width(self):
        self.info.set_boom_width(self.ui.lineEditBoomWidth.text())
    
    @pyqtSlot(str)
    def _commit_boom_width_units(self, text):
        self.info.boom_drop_units = text
        
    @pyqtSlot()
    def _commit_boom_drop(self):
        self.info.set_boom_drop(self.ui.lineEditBoomDrop.text())
        
    @pyqtSlot(str)
    def _commit_boom_drop_units(self, text):
        self.info.boom_drop_units = text
        
    @pyqtSlot()
    def _commit_nozzle_spacing(self):
        self.info.set_nozzle_spacing(self.ui.lineEditNozzleSpacing.text())
        
    @pyqtSlot(str)
    def _commit_nozzle_spacing_units(self, text):
        self.info.nozzle_spacing_units = text
    
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Nozzles
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def init_nozzles(self):
        nozzles = AtomizationModel.nozzles.insert(0,'')
        self.ui.comboBoxNT1.addItems(AtomizationModel.nozzles)
        self.ui.comboBoxNT1.setCurrentIndex(-1)
        self.ui.comboBoxNT1.currentTextChanged[str].connect(self._on_nozzle_1_selected)
        self.ui.comboBoxNT2.addItems(AtomizationModel.nozzles)
        self.ui.comboBoxNT2.setCurrentIndex(-1)
        self.ui.comboBoxNT2.currentTextChanged[str].connect(self._on_nozzle_2_selected)
        
    def fill_nozzles(self, info: AppInfo):
        # Nozzle Set #1
        self.ui.comboBoxNT1.setCurrentText(info.nozzle_type_1)
        self.ui.comboBoxNS1.setCurrentText(info.nozzle_size_1)
        self.ui.comboBoxNS1.currentTextChanged[str].connect(self._commit_nozzle_size_1)
        self.ui.comboBoxND1.setCurrentText(info.nozzle_deflection_1)
        self.ui.comboBoxND1.currentTextChanged[str].connect(self._commit_nozzle_deflection_1)
        self.ui.lineEditNQ1.setText(info.strip_num(info.nozzle_quantity_1, zeroBlank=True))
        self.ui.lineEditNQ1.editingFinished.connect(self._commit_nozzle_quantity_1)
        # Nozzle Set #2
        self.ui.comboBoxNT2.setCurrentText(info.nozzle_type_2)
        self.ui.comboBoxNS2.setCurrentText(info.nozzle_size_2)
        self.ui.comboBoxNS2.currentTextChanged[str].connect(self._commit_nozzle_size_2)
        self.ui.comboBoxND2.setCurrentText(info.nozzle_deflection_2)
        self.ui.comboBoxND2.currentTextChanged[str].connect(self._commit_nozzle_deflection_2)
        self.ui.lineEditNQ2.setText(info.strip_num(info.nozzle_quantity_2, zeroBlank=True))
        self.ui.lineEditNQ2.editingFinished.connect(self._commit_nozzle_quantity_2)
    
    @pyqtSlot(str)
    def _on_nozzle_1_selected(self, nozzle):
        self._on_nozzle_selected(nozzle, cBSize = self.ui.comboBoxNS1, cBDef = self.ui.comboBoxND1)
        if self.info is not None:
            self._commit_nozzle_type_1(nozzle)
        
    @pyqtSlot(str)
    def _on_nozzle_2_selected(self, nozzle):
        self._on_nozzle_selected(nozzle, cBSize = self.ui.comboBoxNS2, cBDef = self.ui.comboBoxND2)
        if self.info is not None:
            self._commit_nozzle_type_2(nozzle)
        
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
        cBSize.addItem('')
        cBDef.addItem('')
        for item in orif_c:
            cBSize.addItem(str(item))
        for item in def_c:
            cBDef.addItem(str(item))
        #remove selection
        cBSize.setCurrentIndex(-1)
        cBDef.setCurrentIndex(-1)
        
    def _commit_nozzle_type_1(self, text):
        self.info.nozzle_type_1 = text
        
    @pyqtSlot(str)
    def _commit_nozzle_size_1(self, text):
        self.info.nozzle_size_1= text
        
    @pyqtSlot(str)
    def _commit_nozzle_deflection_1(self, text):
        self.info.nozzle_deflection_1 = text
        
    @pyqtSlot()
    def _commit_nozzle_quantity_1(self):
        self.info.set_nozzle_quantity_1(self.ui.lineEditNQ1.text())
        
    def _commit_nozzle_type_2(self, text):
        self.info.nozzle_type_2 = text
        
    @pyqtSlot(str)
    def _commit_nozzle_size_2(self, text):
        self.info.nozzle_size_2= text
        
    @pyqtSlot(str)
    def _commit_nozzle_deflection_2(self, text):
        self.info.nozzle_deflection_2 = text
        
    @pyqtSlot()
    def _commit_nozzle_quantity_2(self):
        self.info.set_nozzle_quantity_2(self.ui.lineEditNQ2.text())
    
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
