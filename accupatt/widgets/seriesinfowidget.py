import os

import accupatt.config as cfg
import numpy as np
import pandas as pd
from accupatt.helpers.atomizationModel import AtomizationModel
from accupatt.models.appInfo import AppInfo, Nozzle
from PyQt6 import uic
from PyQt6.QtCore import QDate, QDateTime, pyqtSignal, pyqtSlot, QSignalBlocker
from PyQt6.QtWidgets import QComboBox, QMessageBox

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'seriesInfo.ui'))

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
        self.ui.lineEditAnalyst.editingFinished.connect(self._commit_analyst)
    
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
        # Nozzle Set Buttons
        self.ui.pushButtonNozzleSetAdd.pressed.connect(self._on_nozzle_set_add)
        self.ui.pushButtonNozzleSetRemove.pressed.connect(self._on_nozzle_set_remove)
        # Populate Nozzle Type ComboBox Items
        self.ui.comboBoxNT.addItems(sorted(AtomizationModel.nozzles_extended))
        self.ui.comboBoxNT.setCurrentIndex(-1)
        self.ui.comboBoxNT.currentTextChanged[str].connect(self._on_nozzle_selected)
        
    def fill_nozzles(self, info: AppInfo):
        cb_set: QComboBox = self.ui.comboBoxNozzleSet
        cb_set.clear()
        # Create first nozzle set be default if not exists
        if len(info.nozzles) < 1:
            info.nozzles.append(Nozzle())
        # Populate Nozzle Set ComboBox Items
        for n in info.nozzles:
            cb_set.addItem(f'Nozzle Set {n.id}')
        cb_set.currentIndexChanged[int].connect(self._on_nozzle_set_changed)
        self.ui.comboBoxNS.currentTextChanged[str].connect(self._commit_nozzle_size)
        self.ui.comboBoxND.currentTextChanged[str].connect(self._commit_nozzle_deflection)
        self.ui.lineEditNQ.editingFinished.connect(self._commit_nozzle_quantity)
        cb_set.setCurrentIndex(0)
        self._on_nozzle_set_changed(0)
    
    @pyqtSlot()
    def _on_nozzle_set_add(self):
        cb_set: QComboBox = self.ui.comboBoxNozzleSet
        new_num = cb_set.count()+1
        self.info.nozzles.append(Nozzle(id=new_num))
        cb_set.addItem(f'Nozzle Set {new_num}')
        cb_set.setCurrentIndex(cb_set.count()-1)
        
    @pyqtSlot()
    def _on_nozzle_set_remove(self):
        cb_set: QComboBox = self.ui.comboBoxNozzleSet
        index = cb_set.currentIndex()
        if index > 0:
            cb_set.removeItem(index)
            self.info.nozzles.pop(index)
        for i, n in enumerate(self.info.nozzles):
            n.id = i+1
            cb_set.setItemText(i, f'Nozzle Set {n.id}')
        self._on_nozzle_set_changed(index-1)
    
    @pyqtSlot(int)
    def _on_nozzle_set_changed(self, index):
        if index >= 0:
            self._loading_nozzle = True
            self.ui.comboBoxNT.setCurrentText(self.info.nozzles[index].type)
            self.ui.comboBoxNS.setCurrentText(self.info.nozzles[index].size)   
            self.ui.comboBoxND.setCurrentText(self.info.nozzles[index].deflection)
            self.ui.lineEditNQ.setText(str(self.info.nozzles[index].quantity))
            self._loading_nozzle = False               
    
    @pyqtSlot(str)
    def _on_nozzle_selected(self, nozzle):
        cBSize: QComboBox = self.ui.comboBoxNS
        cBDef: QComboBox = self.ui.comboBoxND
        cBSize.clear()
        cBDef.clear()
        # Populate Comboboxes
        orifices = AtomizationModel().get_orifices_for_nozzle(nozzle)
        cBSize.addItems([str(o) for o in orifices])
        deflections = AtomizationModel().get_deflections_for_nozzle(nozzle)
        cBDef.addItems([str(d) for d in deflections])
        #remove selection
        cBSize.setCurrentIndex(-1)
        cBDef.setCurrentIndex(-1)
        # Commmit signal
        if self.info is not None:
            self._commit_nozzle_type(nozzle)
  
    def _commit_nozzle_type(self, text):
        index = self.ui.comboBoxNozzleSet.currentIndex()
        if not self._loading_nozzle:
            self.info.nozzles[index].type = text
        
    @pyqtSlot(str)
    def _commit_nozzle_size(self, text):
        index = self.ui.comboBoxNozzleSet.currentIndex()
        if not self._loading_nozzle:
            self.info.nozzles[index].size = text
        
    @pyqtSlot(str)
    def _commit_nozzle_deflection(self, text):
        index = self.ui.comboBoxNozzleSet.currentIndex()
        if not self._loading_nozzle:
            self.info.nozzles[index].deflection = text
        
    @pyqtSlot()
    def _commit_nozzle_quantity(self):
        index = self.ui.comboBoxNozzleSet.currentIndex()
        if not self._loading_nozzle:
            self.info.nozzles[index].set_quantity(self.ui.lineEditNQ.text())
    
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Validation
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    def show_validation_error(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Input Validation Error")
        msg.setInformativeText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        result = msg.exec()
        if result == QMessageBox.StandardButton.Ok:
            self.raise_()
            self.activateWindow()
