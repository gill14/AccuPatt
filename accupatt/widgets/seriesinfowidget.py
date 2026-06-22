import os

import accupatt.config as cfg
import numpy as np
import pandas as pd
from aerial_spray_nozzle_models import AtomizationModel
from aerial_spray_nozzle_models.nozzles import NOZZLES
from accupatt.helpers.dBBridge import load_from_db
from accupatt.models.appInfo import AppInfo, Nozzle
from accupatt.widgets.passObservablesWidget import PassObservablesWidget
from PyQt6 import uic
from PyQt6.QtCore import QDate, pyqtSignal, pyqtSlot, QSignalBlocker
from PyQt6.QtWidgets import QComboBox, QFileDialog, QMessageBox, QWidget

from accupatt.models.seriesData import SeriesData

_NOZZLE_PARSED_NAMES: dict[str, list[str]] = {
    "CP09":         ["CP09 SS", "CP09 Deflection"],
    "Davidon TriSet": ["Davidon TriSet SS", "Davidon TriSet Deflection"],
    "CAS LF-5":     ["CAS LF-5 SS", "CAS LF-5 Deflection"],
    "CP-07-3E":     ["CP-07-3E SS", "CP-07-3E Deflection"],
}

def _angle_descriptor(nozzle: str) -> str:
    internals = _NOZZLE_PARSED_NAMES.get(nozzle, [nozzle])
    for name in internals:
        nz = NOZZLES.get(name)
        if nz and nz.angle_description.lower() not in {"no deflection", ""}:
            return nz.angle_description
    for name in internals:
        nz = NOZZLES.get(name)
        if nz:
            return nz.angle_description
    return "Angle"

Ui_Form, baseclass = uic.loadUiType(
    cfg.resource_path("resources", "seriesInfo.ui")
)


class SeriesInfoWidget(baseclass):
    aircraftFile = cfg.resource_path("resources", "AgAircraftData.xlsx")

    target_swath_changed = pyqtSignal()
    request_file_save = pyqtSignal()
    request_open_pass_manager = pyqtSignal()
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
        self._loading_nozzle = False
        self._pass_obs = PassObservablesWidget(parent=self)
        self.ui.groupBoxPassObservables.layout().addWidget(self._pass_obs)
        self._pass_obs.request_open_pass_manager.connect(self.request_open_pass_manager)
        self.ui.buttonString.clicked.connect(self._openStringTab)
        self.ui.buttonCards.clicked.connect(self._openCardTab)
        # Insert pass observables table into the tab chain: NQ → table → Notes
        QWidget.setTabOrder(self.ui.lineEditNQ, self._pass_obs._table_view)
        QWidget.setTabOrder(self._pass_obs._table_view, self.ui.plainTextEditNotesSetup)

    def fill_from_info(self, info: AppInfo):
        self.info = info
        self.fill_flyin(info)
        self.fill_series(info)
        self.fill_applicator(info)
        self.fill_notes(info)
        self.fill_aircraft(info)
        self.fill_spray_system(info)
        self.fill_nozzles(info)

    def set_series_data(self, series_data: SeriesData):
        self._pass_obs.set_pass_list(series_data.passes)

    def refresh_passes(self):
        self._pass_obs.refresh()

    def _openStringTab(self):
        self.request_file_save.emit()
        self.request_open_string_tab.emit()

    def _openCardTab(self):
        self.request_file_save.emit()
        self.request_open_card_tab.emit()

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    Fly-In
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""

    def init_flyin(self):
        self.ui.lineEditName.editingFinished.connect(self._commit_name)
        self.ui.lineEditLocation.editingFinished.connect(self._commit_location)
        self.ui.dateEdit.dateChanged[QDate].connect(self._commit_date)
        self.ui.lineEditAnalyst.editingFinished.connect(self._commit_analyst)

    def fill_flyin(self, info: AppInfo):
        self.ui.lineEditName.setText(info.flyin_name)
        self.ui.lineEditLocation.setText(info.flyin_location)
        date = QDate.fromString(info.flyin_date, "d MMM yyyy")
        if not date.isValid():
            date = QDate.currentDate()
            info.flyin_date = date.toString("d MMM yyyy")
        with QSignalBlocker(self.ui.dateEdit):
            self.ui.dateEdit.setDate(date)
        self.ui.lineEditAnalyst.setText(info.flyin_analyst)

    @pyqtSlot()
    def _commit_name(self):
        self.info.flyin_name = self.ui.lineEditName.text()

    @pyqtSlot()
    def _commit_location(self):
        self.info.flyin_location = self.ui.lineEditLocation.text()

    @pyqtSlot()
    def _commit_date(self):
        self.info.flyin_date = self.ui.dateEdit.date().toString("d MMM yyyy")

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
        self._update_identifier_label()

    def _update_identifier_label(self):
        reg = self.ui.lineEditRegNum.text().strip()
        try:
            series_str = f"{int(self.ui.lineEditSeriesNum.text()):02d}"
        except ValueError:
            series_str = self.ui.lineEditSeriesNum.text().strip()
        self.ui.labelIdentifierValue.setText(f"{reg} {series_str}".strip())

    @pyqtSlot()
    def _commit_regnum(self):
        self.info.regnum = self.ui.lineEditRegNum.text()
        self._update_identifier_label()

    @pyqtSlot()
    def _commit_seriesnum(self):
        self.info.series = int(self.ui.lineEditSeriesNum.text())
        self._update_identifier_label()

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
        self.ui.comboBoxWingspanUnits.setCurrentText(cfg.get_unit_wingspan())
        self.ui.comboBoxWinglets.addItems(["Yes", "No"])
        self.ui.comboBoxWinglets.setCurrentIndex(-1)
        self.ui.comboBoxModel.currentTextChanged[str].connect(self._on_model_selected)
        self.ui.comboBoxWingspanUnits.currentTextChanged[str].connect(
            self._commit_wingspan_units
        )
        self.ui.lineEditWingspan.editingFinished.connect(self._commit_wingspan)
        self.ui.comboBoxWinglets.currentTextChanged[str].connect(self._commit_winglets)

    def fill_aircraft(self, info: AppInfo):
        model = info.model
        self.ui.comboBoxMake.setCurrentText(info.make)
        self.ui.comboBoxModel.setCurrentText(model)
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
        self.ui.comboBoxUnitsSwath.setCurrentText(cfg.get_unit_swath())
        self.ui.comboBoxUnitsRate.addItems(cfg.UNITS_RATE)
        self.ui.comboBoxUnitsRate.setCurrentText(cfg.get_unit_rate())
        self.ui.comboBoxUnitsPressure.addItems(cfg.UNITS_PRESSURE)
        self.ui.comboBoxUnitsPressure.setCurrentText(cfg.get_unit_pressure())
        self.ui.comboBoxUnitsBoomWidth.addItems(cfg.UNITS_BOOM_WIDTH)
        self.ui.comboBoxUnitsBoomWidth.setCurrentText(cfg.get_unit_boom_width())
        self.ui.comboBoxUnitsBoomDrop.addItems(cfg.UNITS_LENGTH_SMALL)
        self.ui.comboBoxUnitsBoomDrop.setCurrentText(cfg.get_unit_boom_drop())
        self.ui.comboBoxUnitsNozzleSpacing.addItems(cfg.UNITS_LENGTH_SMALL)
        self.ui.comboBoxUnitsNozzleSpacing.setCurrentText(cfg.get_unit_nozzle_spacing())
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
        self.target_swath_changed.emit()

    @pyqtSlot()
    def _commit_rate(self):
        self.info.set_rate(self.ui.lineEditRate.text())

    @pyqtSlot(str)
    def _commit_rate_units(self, text):
        self.info.set_rate_units(text)

    @pyqtSlot()
    def _commit_pressure(self):
        self.info.set_pressure(self.ui.lineEditPressure.text())

    @pyqtSlot(str)
    def _commit_pressure_units(self, text):
        self.info.set_pressure_units(text)

    @pyqtSlot()
    def _commit_boom_width(self):
        self.info.set_boom_width(self.ui.lineEditBoomWidth.text())

    @pyqtSlot(str)
    def _commit_boom_width_units(self, text):
        self.info.set_boom_width_units(text)

    @pyqtSlot()
    def _commit_boom_drop(self):
        self.info.set_boom_drop(self.ui.lineEditBoomDrop.text())

    @pyqtSlot(str)
    def _commit_boom_drop_units(self, text):
        self.info.set_boom_drop_units(text)

    @pyqtSlot()
    def _commit_nozzle_spacing(self):
        self.info.set_nozzle_spacing(self.ui.lineEditNozzleSpacing.text())

    @pyqtSlot(str)
    def _commit_nozzle_spacing_units(self, text):
        self.info.set_nozzle_spacing_units(text)

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
            cb_set.addItem(f"Set {n.id}")

        cb_set.setCurrentIndex(0)
        self._on_nozzle_set_changed(0)

    @pyqtSlot()
    def _on_nozzle_set_add(self):
        cb_set: QComboBox = self.ui.comboBoxNozzleSet
        new_num = cb_set.count() + 1
        self.info.nozzles.append(Nozzle(id=new_num))
        cb_set.addItem(f"Set {new_num}")
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
            cb_set.setItemText(i, f"Set {n.id}")
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
        # Update deflection label to reflect nozzle's angle descriptor
        self.ui.label_20.setText(f"{_angle_descriptor(nozzle)}:")
        # Commit signal
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
