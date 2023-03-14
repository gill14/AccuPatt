import os

import accupatt.config as cfg
import numpy as np
import pandas as pd
from accupatt.helpers.atomizationModel import AtomizationModel
from accupatt.helpers.dBBridge import load_from_db
from accupatt.models.appInfo import AppInfo, Nozzle
from PyQt6 import uic
from PyQt6.QtCore import QDate, QDateTime, pyqtSignal, pyqtSlot, QSignalBlocker
from PyQt6.QtWidgets import QComboBox, QFileDialog, QMessageBox

from accupatt.models.seriesData import SeriesData

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "seriesInfo.ui")
)


class SeriesInfoWidget(baseclass):

    aircraftFile = os.path.join(os.getcwd(), "resources", "AgAircraftData.xlsx")

    target_swath_changed = pyqtSignal()
    request_open_pass_filler = pyqtSignal()
    request_open_string_tab = pyqtSignal()
    request_open_card_tab = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.info = AppInfo()
        self.init_flyin()
        self.init_series()
        self.init_applicator()
        self.init_notes()
        self.init_aircraft()
        self.init_spray_system()
        self.init_nozzles()
        self.ui.buttonPassObservables.clicked.connect(self._openPassDataFiller)
        self.ui.buttonString.clicked.connect(self._openStringTab)
        self.ui.buttonCards.clicked.connect(self._openCardTab)

    def fill_from_info(self, info: AppInfo):
        self.info = info
        self.fill_flyin(info)
        self.fill_series(info)
        self.fill_applicator(info)
        self.fill_notes(info)
        self.fill_aircraft(info)
        self.fill_spray_system(info)
        self.fill_nozzles(info)

    def _openPassDataFiller(self):
        self.request_open_pass_filler.emit()

    def _openStringTab(self):
        self.request_open_string_tab.emit()

    def _openCardTab(self):
        self.request_open_card_tab.emit()

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    Fly-In
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""

    def init_flyin(self):
        self.ui.lineEditName.editingFinished.connect(self._commit_name)
        self.ui.lineEditLocation.editingFinished.connect(self._commit_location)
        self.ui.dateEdit.setDateTime(QDateTime.currentDateTime())
        self.ui.dateEdit.dateChanged[QDate].connect(self._dateEdit_changed)
        self.ui.lineEditAnalyst.editingFinished.connect(self._commit_analyst)

    def fill_flyin(self, info: AppInfo):
        self.ui.lineEditName.setText(info.flyin_name)
        self.ui.lineEditLocation.setText(info.flyin_location)
        self.ui.lineEditDate.setText(info.flyin_date)
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
        self.ui.lineEditDate.setText(date.toString("d MMM yyyy"))
        self._commit_date()

    @pyqtSlot()
    def _commit_analyst(self):
        self.info.flyin_analyst = self.ui.lineEditAnalyst.text()

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    Series
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""

    def init_series(self):
        self.ui.lineEditRegNum.editingFinished.connect(self._commit_regnum)
        self.ui.lineEditSeriesNum.editingFinished.connect(self._commit_seriesnum)

    def fill_series(self, info: AppInfo):
        self.ui.lineEditRegNum.setText(info.regnum)
        self.ui.lineEditSeriesNum.setText(str(info.series))

    @pyqtSlot()
    def _commit_regnum(self):
        self.info.regnum = self.ui.lineEditRegNum.text()

    @pyqtSlot()
    def _commit_seriesnum(self):
        self.info.series = int(self.ui.lineEditSeriesNum.text())

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    Applicator
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""

    def init_applicator(self):
        self.ui.pilotLineEdit.editingFinished.connect(self._commit_pilot)
        self.ui.businessLineEdit.editingFinished.connect(self._commit_business)
        self.ui.streetLineEdit.editingFinished.connect(self._commit_street)
        self.ui.cityLineEdit.editingFinished.connect(self._commit_city)
        self.ui.stateLineEdit.editingFinished.connect(self._commit_state)
        self.ui.zipLineEdit.editingFinished.connect(self._commit_zip)
        self.ui.phoneLineEdit.editingFinished.connect(self._commit_phone)
        self.ui.emailLineEdit.editingFinished.connect(self._commit_email)
        self.ui.buttonLoadBusiness.clicked.connect(self._load_business_from_file)

    def fill_applicator(self, info: AppInfo):
        self.ui.pilotLineEdit.setText(info.pilot)
        self.ui.businessLineEdit.setText(info.business)
        self.ui.streetLineEdit.setText(info.street)
        self.ui.cityLineEdit.setText(info.city)
        self.ui.stateLineEdit.setText(info.state)
        self.ui.zipLineEdit.setText(info.zip)
        self.ui.phoneLineEdit.setText(info.phone)
        self.ui.emailLineEdit.setText(info.email)

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

    @pyqtSlot()
    def _load_business_from_file(self):
        print("triggered")
        file, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Choose File",
            directory=cfg.get_datafile_dir(),
            filter="AccuPatt (*.db)",
        )
        if file == "":
            return
        series = SeriesData()
        load_from_db(file, s=series)
        self.ui.businessLineEdit.setText(series.info.business)
        self._commit_business()
        self.ui.streetLineEdit.setText(series.info.street)
        self._commit_street()
        self.ui.cityLineEdit.setText(series.info.city)
        self._commit_city()
        self.ui.stateLineEdit.setText(series.info.state)
        self._commit_state()
        self.ui.zipLineEdit.setText(series.info.zip)
        self._commit_zip()
        self.ui.phoneLineEdit.setText(series.info.phone)
        self._commit_phone()
        self.ui.emailLineEdit.setText(series.info.email)
        self._commit_email()

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    Notes
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""

    def init_notes(self):
        self.ui.plainTextEditNotesSetup.textChanged.connect(self._commit_notes_setup)
        self.ui.plainTextEditNotesAnalyst.textChanged.connect(
            self._commit_notes_analyst
        )

    def fill_notes(self, info: AppInfo):
        self.ui.plainTextEditNotesSetup.setPlainText(info.notes_setup)
        self.ui.plainTextEditNotesAnalyst.setPlainText(info.notes_analyst)

    @pyqtSlot()
    def _commit_notes_setup(self):
        self.info.notes_setup = self.ui.plainTextEditNotesSetup.toPlainText()

    @pyqtSlot()
    def _commit_notes_analyst(self):
        self.info.notes_analyst = self.ui.plainTextEditNotesAnalyst.toPlainText()

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    Aircraft
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""

    def init_aircraft(self):
        self.ui.comboBoxMake.addItem("")
        self.aircraft_map = pd.read_excel(self.aircraftFile, sheet_name=None)
        self.ui.comboBoxMake.addItems(self.aircraft_map.keys())
        self.ui.comboBoxMake.setCurrentIndex(-1)
        self.ui.comboBoxMake.currentTextChanged[str].connect(self._on_make_selected)

        self.ui.comboBoxWingspanUnits.addItems(cfg.UNITS_LENGTH_LARGE)
        self.ui.comboBoxWingspanUnits.setCurrentIndex(-1)
        self.ui.comboBoxWinglets.addItems(["Yes", "No"])
        self.ui.comboBoxWinglets.setCurrentIndex(-1)
        self.ui.comboBoxModel.currentTextChanged[str].connect(self._on_model_selected)
        self.ui.comboBoxWingspanUnits.currentTextChanged[str].connect(
            self._commit_wingspan_units
        )
        self.ui.lineEditWingspan.editingFinished.connect(self._commit_wingspan)
        self.ui.comboBoxWinglets.currentTextChanged[str].connect(self._commit_winglets)

    def fill_aircraft(self, info: AppInfo):
        self.ui.comboBoxMake.setCurrentText(info.make)
        self.ui.comboBoxModel.setCurrentText(info.model)
        with QSignalBlocker(self.ui.comboBoxWingspanUnits):
            self.ui.comboBoxWingspanUnits.setCurrentIndex(-1)
            self.ui.comboBoxWingspanUnits.setCurrentText(info.wingspan_units)
        self.ui.lineEditWingspan.setText(info.strip_num(info.wingspan, zeroBlank=True))
        self.ui.comboBoxWinglets.setCurrentText(info.winglets)

    @pyqtSlot(str)
    def _on_make_selected(self, make):
        self.ui.comboBoxModel.clear()
        self.ui.comboBoxModel.addItem("")
        if make in self.aircraft_map.keys():
            df = self.aircraft_map[make]
            self.ui.comboBoxModel.addItems(df["Model"])
            self.ui.comboBoxModel.setCurrentIndex(-1)
        if self.info is not None:
            self._commit_aircraft_make(make)

    @pyqtSlot(str)
    def _on_model_selected(self, model):
        self.ui.lineEditWingspan.clear()
        make = self.ui.comboBoxMake.currentText()
        if make in self.aircraft_map.keys():
            df = self.aircraft_map[make]
            if model != "" and df[df["Model"].str.contains(model)].any().any():
                df = df.set_index("Model")
                ws = df.at[model, "Wingspan (FT)"]
                if self.ui.comboBoxWingspanUnits.currentText() == "m":
                    ws = ws / cfg.FT_PER_M
                    self.ui.lineEditWingspan.setText(f"{round(ws, 2):.2f}")
                else:
                    self.ui.lineEditWingspan.setText(str(round(ws)))
                self._commit_wingspan()
        if self.info is not None:
            self._commit_aircraft_model(model)

    def _commit_aircraft_make(self, text):
        self.info.make = text

    def _commit_aircraft_model(self, text):
        self.info.model = text

    @pyqtSlot(str)
    def _commit_wingspan_units(self, text):
        self.info.set_wingspan_units(text)
        cfg.set_unit_wingspan(text)

    @pyqtSlot()
    def _commit_wingspan(self):
        self.info.set_wingspan(self.ui.lineEditWingspan.text())

    @pyqtSlot(str)
    def _commit_winglets(self, text):
        self.info.winglets = text

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    Spray System
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""

    def init_spray_system(self):
        self.ui.comboBoxUnitsSwath.addItems(cfg.UNITS_LENGTH_LARGE)
        self.ui.comboBoxUnitsSwath.setCurrentIndex(-1)
        self.ui.comboBoxUnitsRate.addItems(cfg.UNITS_RATE)
        self.ui.comboBoxUnitsRate.setCurrentIndex(-1)
        self.ui.comboBoxUnitsPressure.addItems(cfg.UNITS_PRESSURE)
        self.ui.comboBoxUnitsPressure.setCurrentIndex(-1)
        self.ui.comboBoxUnitsBoomWidth.addItems(cfg.UNITS_LENGTH_LARGE)
        self.ui.comboBoxUnitsBoomWidth.addItem("%")
        self.ui.comboBoxUnitsBoomWidth.setCurrentIndex(-1)
        self.ui.comboBoxUnitsBoomDrop.addItems(cfg.UNITS_LENGTH_SMALL)
        self.ui.comboBoxUnitsBoomDrop.setCurrentIndex(-1)
        self.ui.comboBoxUnitsNozzleSpacing.addItems(cfg.UNITS_LENGTH_SMALL)
        self.ui.comboBoxUnitsNozzleSpacing.setCurrentIndex(-1)
        self.ui.lineEditSwath.editingFinished.connect(self._commit_swath)
        self.ui.comboBoxUnitsSwath.currentTextChanged[str].connect(
            self._commit_swath_units
        )
        self.ui.lineEditRate.editingFinished.connect(self._commit_rate)
        self.ui.comboBoxUnitsRate.currentTextChanged[str].connect(
            self._commit_rate_units
        )
        self.ui.lineEditPressure.editingFinished.connect(self._commit_pressure)
        self.ui.comboBoxUnitsPressure.currentTextChanged[str].connect(
            self._commit_pressure_units
        )
        self.ui.lineEditBoomWidth.editingFinished.connect(self._commit_boom_width)
        self.ui.comboBoxUnitsBoomWidth.currentTextChanged[str].connect(
            self._commit_boom_width_units
        )
        self.ui.lineEditBoomDrop.editingFinished.connect(self._commit_boom_drop)
        self.ui.comboBoxUnitsBoomDrop.currentTextChanged[str].connect(
            self._commit_boom_drop_units
        )
        self.ui.lineEditNozzleSpacing.editingFinished.connect(
            self._commit_nozzle_spacing
        )
        self.ui.comboBoxUnitsNozzleSpacing.currentTextChanged[str].connect(
            self._commit_nozzle_spacing_units
        )

    def fill_spray_system(self, info: AppInfo):
        self.ui.lineEditSwath.setText(info.strip_num(info.swath, zeroBlank=True))
        with QSignalBlocker(self.ui.comboBoxUnitsSwath):
            self.ui.comboBoxUnitsSwath.setCurrentIndex(-1)
            self.ui.comboBoxUnitsSwath.setCurrentText(info.swath_units)
        self.ui.lineEditRate.setText(f"{info.strip_num(info.rate, zeroBlank=True)}")
        with QSignalBlocker(self.ui.comboBoxUnitsRate):
            self.ui.comboBoxUnitsRate.setCurrentIndex(-1)
            self.ui.comboBoxUnitsRate.setCurrentText(info.rate_units)
        self.ui.lineEditPressure.setText(
            f"{info.strip_num(info.pressure, zeroBlank=True)}"
        )
        with QSignalBlocker(self.ui.comboBoxUnitsPressure):
            self.ui.comboBoxUnitsPressure.setCurrentIndex(-1)
            self.ui.comboBoxUnitsPressure.setCurrentText(info.pressure_units)
        self.ui.lineEditBoomWidth.setText(
            f"{info.strip_num(info.boom_width, zeroBlank=True)}"
        )
        with QSignalBlocker(self.ui.comboBoxUnitsBoomWidth):
            self.ui.comboBoxUnitsBoomWidth.setCurrentIndex(-1)
            self.ui.comboBoxUnitsBoomWidth.setCurrentText(info.boom_width_units)
        self.ui.lineEditBoomDrop.setText(
            f"{info.strip_num(info.boom_drop, zeroBlank=True)}"
        )
        with QSignalBlocker(self.ui.comboBoxUnitsBoomDrop):
            self.ui.comboBoxUnitsBoomDrop.setCurrentIndex(-1)
            self.ui.comboBoxUnitsBoomDrop.setCurrentText(info.boom_drop_units)
        self.ui.lineEditNozzleSpacing.setText(
            f"{info.strip_num(info.nozzle_spacing, zeroBlank=True)}"
        )
        with QSignalBlocker(self.ui.comboBoxUnitsNozzleSpacing):
            self.ui.comboBoxUnitsNozzleSpacing.setCurrentIndex(-1)
            self.ui.comboBoxUnitsNozzleSpacing.setCurrentText(info.nozzle_spacing_units)

    @pyqtSlot()
    def _commit_swath(self):
        self.info.set_swath(self.ui.lineEditSwath.text())
        self.target_swath_changed.emit()

    @pyqtSlot(str)
    def _commit_swath_units(self, text):
        self.info.set_swath_units(text)
        cfg.set_unit_swath(text)
        self.target_swath_changed.emit()

    @pyqtSlot()
    def _commit_rate(self):
        self.info.set_rate(self.ui.lineEditRate.text())

    @pyqtSlot(str)
    def _commit_rate_units(self, text):
        self.info.set_rate_units(text)
        cfg.set_unit_rate(text)

    @pyqtSlot()
    def _commit_pressure(self):
        self.info.set_pressure(self.ui.lineEditPressure.text())

    @pyqtSlot(str)
    def _commit_pressure_units(self, text):
        self.info.set_pressure_units(text)
        cfg.set_unit_pressure(text)

    @pyqtSlot()
    def _commit_boom_width(self):
        self.info.set_boom_width(self.ui.lineEditBoomWidth.text())

    @pyqtSlot(str)
    def _commit_boom_width_units(self, text):
        self.info.set_boom_width_units(text)
        cfg.set_unit_boom_width(text)

    @pyqtSlot()
    def _commit_boom_drop(self):
        self.info.set_boom_drop(self.ui.lineEditBoomDrop.text())

    @pyqtSlot(str)
    def _commit_boom_drop_units(self, text):
        self.info.set_boom_drop_units(text)
        cfg.set_unit_boom_drop(text)

    @pyqtSlot()
    def _commit_nozzle_spacing(self):
        self.info.set_nozzle_spacing(self.ui.lineEditNozzleSpacing.text())

    @pyqtSlot(str)
    def _commit_nozzle_spacing_units(self, text):
        self.info.set_nozzle_spacing_units(text)
        cfg.set_unit_nozzle_spacing(text)

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    Nozzles
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""

    def init_nozzles(self):
        # Nozzle Set Buttons
        self.ui.pushButtonNozzleSetAdd.pressed.connect(self._on_nozzle_set_add)
        self.ui.pushButtonNozzleSetRemove.pressed.connect(self._on_nozzle_set_remove)
        # Populate Nozzle Type ComboBox Items
        self.ui.comboBoxNT.addItems(sorted(AtomizationModel.nozzles_extended))
        self.ui.comboBoxNT.setCurrentIndex(-1)
        self.ui.comboBoxNT.currentTextChanged[str].connect(self._on_nozzle_selected)
        self.ui.comboBoxNozzleSet.currentIndexChanged[int].connect(
            self._on_nozzle_set_changed
        )
        self.ui.comboBoxNS.currentTextChanged[str].connect(self._commit_nozzle_size)
        self.ui.comboBoxND.currentTextChanged[str].connect(
            self._commit_nozzle_deflection
        )
        self.ui.lineEditNQ.editingFinished.connect(self._commit_nozzle_quantity)

    def fill_nozzles(self, info: AppInfo):
        cb_set: QComboBox = self.ui.comboBoxNozzleSet
        cb_set.clear()
        # Create first nozzle set be default if not exists
        if len(info.nozzles) < 1:
            info.nozzles.append(Nozzle())
        # Populate Nozzle Set ComboBox Items
        for n in info.nozzles:
            cb_set.addItem(f"Nozzle Set {n.id}")

        cb_set.setCurrentIndex(0)
        self._on_nozzle_set_changed(0)

    @pyqtSlot()
    def _on_nozzle_set_add(self):
        cb_set: QComboBox = self.ui.comboBoxNozzleSet
        new_num = cb_set.count() + 1
        self.info.nozzles.append(Nozzle(id=new_num))
        cb_set.addItem(f"Nozzle Set {new_num}")
        cb_set.setCurrentIndex(cb_set.count() - 1)

    @pyqtSlot()
    def _on_nozzle_set_remove(self):
        cb_set: QComboBox = self.ui.comboBoxNozzleSet
        index = cb_set.currentIndex()
        if index > 0:
            cb_set.removeItem(index)
            self.info.nozzles.pop(index)
        for i, n in enumerate(self.info.nozzles):
            n.id = i + 1
            cb_set.setItemText(i, f"Nozzle Set {n.id}")
        self._on_nozzle_set_changed(index - 1)

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
        # remove selection
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

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    Validation
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""

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

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    Validation
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""
