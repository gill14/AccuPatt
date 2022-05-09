import os

import accupatt.config as cfg
from accupatt.models.passData import Pass
from PyQt6 import uic

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "passInfo.ui")
)


class PassInfoWidget(baseclass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

    def fill_from_pass(self, passData: Pass):
        _, gs_unit, gs, _ = passData.get_ground_speed()
        self.ui.lineEditGS.setText(gs)
        self.ui.comboBoxUnitsGS.addItems(cfg.UNITS_GROUND_SPEED)
        self.ui.comboBoxUnitsGS.setCurrentText(gs_unit)
        _, sh_unit, sh, _ = passData.get_spray_height()
        self.ui.lineEditSH.setText(sh)
        self.ui.comboBoxUnitsSH.addItems(cfg.UNITS_SPRAY_HEIGHT)
        self.ui.comboBoxUnitsSH.setCurrentText(sh_unit)
        _, _, ph, _ = passData.get_pass_heading()
        self.ui.lineEditPH.setText(ph)
        _, _, wd, _ = passData.get_wind_direction()
        self.ui.lineEditWD.setText(wd)
        _, ws_unit, ws, _ = passData.get_wind_speed()
        self.ui.lineEditWS.setText(ws)
        self.ui.comboBoxUnitsWS.addItems(cfg.UNITS_WIND_SPEED)
        self.ui.comboBoxUnitsWS.setCurrentText(ws_unit)
        _, t_unit, t, _ = passData.get_temperature()
        self.ui.lineEditT.setText(t)
        self.ui.comboBoxUnitsT.addItems(cfg.UNITS_TEMPERATURE)
        self.ui.comboBoxUnitsT.setCurrentText(t_unit)
        _, _, h, _ = passData.get_humidity()
        self.ui.lineEditH.setText(h)

    """
    Check if each field has an invalid value, else set the currently selected
    value to the passData object. Returns a string list of exceptions, or an
    empty list if no exceptions.
    """

    def validate_fields(self, passData: Pass) -> list[str]:
        p = passData
        excepts = []
        # Ground Speed
        if not p.set_ground_speed(
            self.ui.lineEditGS.text(), units=self.ui.comboBoxUnitsGS.currentText()
        ):
            excepts.append("-GROUND SPEED cannot be converted to a NUMBER")
        # Spray Height
        if not p.set_spray_height(
            self.ui.lineEditSH.text(), units=self.ui.comboBoxUnitsSH.currentText()
        ):
            excepts.append("-SPRAY HEIGHT cannot be converted to a NUMBER")
        # Pass Heading
        if not p.set_pass_heading(self.ui.lineEditPH.text()):
            excepts.append("-PASS HEADING cannot be converted to an INTEGER")
        # Wind Direction
        if not p.set_wind_direction(self.ui.lineEditWD.text()):
            excepts.append("-WIND DIRECTION cannot be converted to a NUMBER")
        # Wind Speed
        if not p.set_wind_speed(
            self.ui.lineEditWS.text(), units=self.ui.comboBoxUnitsWS.currentText()
        ):
            excepts.append("-WIND SPEED cannot be converted to a NUMBER")
        # Temperature
        if not p.set_temperature(
            self.ui.lineEditT.text(), units=self.ui.comboBoxUnitsT.currentText()
        ):
            excepts.append("-TEMPERATURE cannot be converted to a NUMBER")
        # Humidity
        if not p.set_humidity(self.ui.lineEditH.text()):
            excepts.append("-HUMIDITY cannot be converted to a NUMBER")
        return excepts
