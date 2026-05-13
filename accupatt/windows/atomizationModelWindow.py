"""Interactive atomization-model dialog.

GUI replication of the USDA AATRU spreadsheet, extended to support a second
nozzle set (multi-model). Pick a nozzle (and optionally a second), dial in
orifice / angle / quantity, then airspeed and pressure; outputs update live.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import accupatt.config as cfg
from accupatt.helpers.atomizationModel import AtomizationModel, AtomizationModelMulti
from accupatt.helpers.atomizationModel.nozzles import NOZZLES
from accupatt.helpers.atomizationModel.reference import DSC_REFERENCE


_PARSED_NAMES: dict[str, tuple[str, ...]] = {
    "CP09": ("CP09 Deflection", "CP09 SS"),
    "Davidon TriSet": ("Davidon TriSet Deflection", "Davidon TriSet SS"),
}


def _internal_names(user_name: str) -> tuple[str, ...]:
    if user_name in _PARSED_NAMES:
        return _PARSED_NAMES[user_name]
    return (user_name,) if user_name in NOZZLES else ()


def _descriptor_for(user_name: str) -> str:
    for internal in _internal_names(user_name):
        nz = NOZZLES.get(internal)
        if nz and nz.angle_description.lower() not in {"no deflection", ""}:
            return nz.angle_description
    for internal in _internal_names(user_name):
        nz = NOZZLES.get(internal)
        if nz:
            return nz.angle_description
    return "Angle"


def _envelope(user_name: str, attr: str) -> tuple[float, float] | None:
    vals: list[float] = []
    for internal in _internal_names(user_name):
        nz = NOZZLES.get(internal)
        if not nz:
            continue
        for m in nz.models:
            vals.extend(getattr(m, attr))
    if not vals:
        return None
    return min(vals), max(vals)


def _fmt(x) -> str:
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)


def _parse_number(s: str):
    s = s.strip()
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


class NozzleSetWidget(QGroupBox):
    """A single (nozzle, orifice, angle, quantity) block."""

    changed = pyqtSignal()

    def __init__(self, title: str, nozzle_options: list[str], parent=None):
        super().__init__(title, parent=parent)
        self._building = False

        self.cb_nozzle = QComboBox()
        self.cb_nozzle.addItem("")
        for name in nozzle_options:
            self.cb_nozzle.addItem(name)

        self.cb_orifice = QComboBox()
        self.cb_angle = QComboBox()
        self.spin_quantity = QSpinBox()
        self.spin_quantity.setRange(0, 99)
        self.spin_quantity.setValue(0)

        self.lbl_orifice = QLabel("Orifice:")
        self.lbl_angle = QLabel("Angle:")

        self.lbl_orifice_range = QLabel("")
        self.lbl_angle_range = QLabel("")
        for w in (self.lbl_orifice_range, self.lbl_angle_range):
            w.setStyleSheet("color: gray;")

        grid = QGridLayout(self)
        grid.addWidget(QLabel("Nozzle:"), 0, 0)
        grid.addWidget(self.cb_nozzle, 0, 1, 1, 2)
        grid.addWidget(self.lbl_orifice, 1, 0)
        grid.addWidget(self.cb_orifice, 1, 1)
        grid.addWidget(self.lbl_orifice_range, 1, 2)
        grid.addWidget(self.lbl_angle, 2, 0)
        grid.addWidget(self.cb_angle, 2, 1)
        grid.addWidget(self.lbl_angle_range, 2, 2)
        grid.addWidget(QLabel("Quantity:"), 3, 0)
        grid.addWidget(self.spin_quantity, 3, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        self._set_dependents_enabled(False)

        self.cb_nozzle.currentTextChanged[str].connect(self._on_nozzle_changed)
        self.cb_orifice.currentTextChanged[str].connect(lambda _: self._emit_changed())
        self.cb_angle.currentTextChanged[str].connect(lambda _: self._emit_changed())
        self.spin_quantity.valueChanged.connect(lambda _: self._emit_changed())

    # ---- internal ----

    def _set_dependents_enabled(self, enabled: bool):
        self.cb_orifice.setEnabled(enabled)
        self.cb_angle.setEnabled(enabled)
        self.spin_quantity.setEnabled(enabled)

    def _emit_changed(self):
        if not self._building:
            self.changed.emit()

    def _on_nozzle_changed(self, name: str):
        self._building = True
        self.cb_orifice.clear()
        self.cb_angle.clear()
        self.lbl_orifice_range.setText("")
        self.lbl_angle_range.setText("")
        if not name:
            self._set_dependents_enabled(False)
            self.spin_quantity.setValue(0)
            self._building = False
            self._emit_changed()
            return

        helper = AtomizationModel()
        orifices = helper.get_orifices_for_nozzle(name)
        angles = helper.get_deflections_for_nozzle(name)
        self.cb_orifice.addItems(["", *[str(o) for o in orifices]])
        self.cb_angle.addItems(["", *[str(a) for a in angles]])

        desc = _descriptor_for(name)
        self.lbl_angle.setText(f"{desc}:")
        if orifices:
            self.lbl_orifice_range.setText(f"{orifices[0]} to {orifices[-1]}")
        if angles:
            self.lbl_angle_range.setText(", ".join(str(a) for a in angles))

        self._set_dependents_enabled(True)
        # Auto-default to quantity = 1 once a nozzle is chosen.
        if self.spin_quantity.value() == 0:
            self.spin_quantity.setValue(1)
        self._building = False
        self._emit_changed()

    # ---- public ----

    def is_complete(self) -> bool:
        return bool(
            self.cb_nozzle.currentText()
            and self.cb_orifice.currentText()
            and self.cb_angle.currentText()
            and self.spin_quantity.value() > 0
        )

    def values(self) -> tuple[str, object, object, int] | None:
        if not self.is_complete():
            return None
        return (
            self.cb_nozzle.currentText(),
            _parse_number(self.cb_orifice.currentText()),
            _parse_number(self.cb_angle.currentText()),
            self.spin_quantity.value(),
        )

    def nozzle_name(self) -> str:
        return self.cb_nozzle.currentText()

    def populate(self, nozzle_type: str, orifice, angle, quantity: int) -> bool:
        """Set fields from stored values. Returns True if the nozzle type matched."""
        if not nozzle_type:
            return False
        idx = self.cb_nozzle.findText(nozzle_type)
        if idx < 0:
            return False
        self.cb_nozzle.setCurrentIndex(idx)
        if orifice not in (None, ""):
            o_idx = self.cb_orifice.findText(str(orifice))
            if o_idx >= 0:
                self.cb_orifice.setCurrentIndex(o_idx)
        if angle not in (None, ""):
            a_idx = self.cb_angle.findText(str(angle))
            if a_idx >= 0:
                self.cb_angle.setCurrentIndex(a_idx)
        if quantity and quantity > 0:
            self.spin_quantity.setValue(int(quantity))
        return True


class AtomizationModelWindow(QDialog):
    OUT_NA = "--"

    def __init__(self, parent=None, series=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Atomization Model")
        self._last_total_gpm: float = -1.0
        self._build_ui()
        if series is not None:
            self._prefill_from_series(series)
        self._connect()
        self._update_conditions_enabled()
        self._update_range_labels()
        self._recalc()
        self._recalc_boom_flow()

    # ---- prefill ----

    def _prefill_from_series(self, series):
        info = series.info

        # Nozzle sets — up to two populated entries from the series.
        sets = [self.set1, self.set2]
        for widget, n in zip(sets, [n for n in info.nozzles if n.type]):
            widget.populate(n.type, n.size, n.deflection, n.quantity)

        # Pressure (psi).
        pressure_psi = info.get_pressure(units=cfg.UNIT_PSI)
        if pressure_psi and pressure_psi > 0:
            self.le_pressure.setText(_fmt(round(pressure_psi, 3)))

        # Airspeed mean (mph) across all passes.
        try:
            airspeed_mph, _, _ = series.get_airspeed_mean(
                units=cfg.UNIT_MPH, string_included=True, cards_included=True,
            )
        except Exception:
            airspeed_mph = 0
        if airspeed_mph and airspeed_mph > 0:
            self.le_airspeed.setText(_fmt(round(float(airspeed_mph), 3)))

        # Swath width (ft) — convert from meters if needed.
        if info.swath and info.swath > 0:
            if info.swath_units == cfg.UNIT_FT:
                swath_ft = float(info.swath)
            elif info.swath_units == cfg.UNIT_M:
                swath_ft = float(info.swath) * cfg.FT_PER_M
            else:
                swath_ft = 0.0
            if swath_ft > 0:
                self.le_swath.setText(_fmt(round(swath_ft, 3)))

        # Application rate (GPA) — convert from L/ha if needed.
        if info.rate and info.rate > 0:
            if info.rate_units == cfg.UNIT_GPA:
                gpa = float(info.rate)
            elif info.rate_units == cfg.UNIT_LPHA:
                # 1 GPA = L_PER_GAL × ac_per_ha (≈ 2.47105) L/ha ≈ 9.354 L/ha
                gpa = float(info.rate) / (cfg.L_PER_GAL * 2.47105)
            else:
                gpa = 0.0
            if gpa > 0:
                self.le_gpa.setText(_fmt(round(gpa, 3)))

    # ---- UI ----

    def _build_ui(self):
        root = QVBoxLayout(self)

        nozzle_options = list(AtomizationModel.nozzles)

        self.set1 = NozzleSetWidget("Step 1: Nozzle Set 1", nozzle_options)
        self.set2 = NozzleSetWidget("Step 2: Nozzle Set 2 (optional)", nozzle_options)

        sets_row = QHBoxLayout()
        sets_row.addWidget(self.set1)
        sets_row.addWidget(self.set2)
        root.addLayout(sets_row)

        # Shared operating conditions
        self.conditions_box = QGroupBox("Step 3: Operating Conditions")
        cond_grid = QGridLayout(self.conditions_box)
        self.le_pressure = QLineEdit()
        self.le_pressure.setValidator(QDoubleValidator(0.0, 1e6, 3))
        self.le_airspeed = QLineEdit()
        self.le_airspeed.setValidator(QDoubleValidator(0.0, 1e6, 3))
        self.lbl_pressure_range = QLabel("")
        self.lbl_airspeed_range = QLabel("")
        for w in (self.lbl_pressure_range, self.lbl_airspeed_range):
            w.setStyleSheet("color: gray;")
        cond_grid.addWidget(QLabel("Pressure (psi):"), 0, 0)
        cond_grid.addWidget(self.le_pressure, 0, 1)
        cond_grid.addWidget(self.lbl_pressure_range, 0, 2)
        cond_grid.addWidget(QLabel("Airspeed (mph):"), 1, 0)
        cond_grid.addWidget(self.le_airspeed, 1, 1)
        cond_grid.addWidget(self.lbl_airspeed_range, 1, 2)
        cond_grid.setColumnStretch(1, 1)
        cond_grid.setColumnStretch(2, 1)

        # Step 4: Boom Flow Required — sits next to Step 3.
        boom_box = QGroupBox("Step 4: Calculate Boom Flow Required (optional)")
        boom_grid = QGridLayout(boom_box)
        self.le_gpa = QLineEdit()
        self.le_gpa.setValidator(QDoubleValidator(0.0, 1e6, 3))
        self.le_swath = QLineEdit()
        self.le_swath.setValidator(QDoubleValidator(0.0, 1e6, 3))
        self.out_required_gpm = QLabel(self.OUT_NA)
        boom_grid.addWidget(QLabel("Application Rate (GPA):"), 0, 0)
        boom_grid.addWidget(self.le_gpa, 0, 1)
        boom_grid.addWidget(QLabel("Swath Width (ft):"), 1, 0)
        boom_grid.addWidget(self.le_swath, 1, 1)
        boom_grid.addWidget(QLabel("Required Boom Flow (gpm):"), 2, 0)
        boom_grid.addWidget(self.out_required_gpm, 2, 1)
        boom_grid.setColumnStretch(1, 1)

        conditions_row = QHBoxLayout()
        conditions_row.addWidget(self.conditions_box)
        conditions_row.addWidget(boom_box)
        root.addLayout(conditions_row)

        # Outputs — DV values are merged into their colored DSC chips.
        out_box = QGroupBox("Output")
        out_grid = QGridLayout(out_box)
        out_grid.setColumnStretch(1, 1)
        out_grid.setColumnStretch(4, 1)
        # Visual gutter between the DSC-chip column and the ancillary stats.
        out_grid.setColumnMinimumWidth(2, 28)

        self.out_dsc01 = self._make_dsc_label()
        self.out_dsc05 = self._make_dsc_label()
        self.out_dsc09 = self._make_dsc_label()
        self.out_dsc = self._make_dsc_label(big=True)
        self.out_rs = QLabel(self.OUT_NA)
        self.out_v100 = QLabel(self.OUT_NA)
        self.out_v200 = QLabel(self.OUT_NA)
        self.out_gpm = QLabel(self.OUT_NA)

        # Left column: DV/DSC chips
        out_grid.addWidget(QLabel("DV0.1 (µm):"), 0, 0)
        out_grid.addWidget(self.out_dsc01, 0, 1)
        out_grid.addWidget(QLabel("DV0.5 (µm):"), 1, 0)
        out_grid.addWidget(self.out_dsc05, 1, 1)
        out_grid.addWidget(QLabel("DV0.9 (µm):"), 2, 0)
        out_grid.addWidget(self.out_dsc09, 2, 1)
        out_grid.addWidget(QLabel("DSC:"), 3, 0)
        out_grid.addWidget(self.out_dsc, 3, 1)

        # Right column: ancillary stats (col 2 left blank as a gutter)
        out_grid.addWidget(QLabel("Relative Span:"), 0, 3)
        out_grid.addWidget(self.out_rs, 0, 4)
        out_grid.addWidget(QLabel("%V<100 µm:"), 1, 3)
        out_grid.addWidget(self.out_v100, 1, 4)
        out_grid.addWidget(QLabel("%V<200 µm:"), 2, 3)
        out_grid.addWidget(self.out_v200, 2, 4)
        out_grid.addWidget(QLabel("Total Flow Rate (gpm):"), 3, 3)
        out_grid.addWidget(self.out_gpm, 3, 4)

        root.addWidget(out_box)

        self.setMinimumWidth(820)

    def _make_dsc_label(self, big: bool = False) -> QLabel:
        lbl = QLabel(self.OUT_NA)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setAutoFillBackground(True)
        lbl.setMinimumWidth(80)
        if big:
            f = lbl.font()
            f.setBold(True)
            f.setPointSize(f.pointSize() + 2)
            lbl.setFont(f)
            lbl.setMinimumHeight(28)
        else:
            lbl.setMinimumHeight(20)
        lbl.setStyleSheet("background-color: #FFFFFF; color: black; border: 1px solid #888;")
        return lbl

    # ---- wiring ----

    def _connect(self):
        self.set1.changed.connect(self._on_set_changed)
        self.set2.changed.connect(self._on_set_changed)
        self.le_pressure.textChanged.connect(lambda _: self._recalc())
        self.le_airspeed.textChanged.connect(lambda _: self._on_airspeed_changed())
        self.le_gpa.textChanged.connect(lambda _: self._recalc_boom_flow())
        self.le_swath.textChanged.connect(lambda _: self._recalc_boom_flow())

    def _on_airspeed_changed(self):
        self._recalc()
        self._recalc_boom_flow()

    def _on_set_changed(self):
        self._update_conditions_enabled()
        self._update_range_labels()
        self._recalc()

    def _update_conditions_enabled(self):
        any_nozzle = bool(self.set1.nozzle_name() or self.set2.nozzle_name())
        self.conditions_box.setEnabled(any_nozzle)
        if not any_nozzle:
            self.lbl_pressure_range.setText("")
            self.lbl_airspeed_range.setText("")

    def _update_range_labels(self):
        active = [n for n in (self.set1.nozzle_name(), self.set2.nozzle_name()) if n]
        as_env = _intersection_envelope(active, "airspeeds")
        p_env = _intersection_envelope(active, "pressures")
        self.lbl_airspeed_range.setText(
            f"{_fmt(as_env[0])} to {_fmt(as_env[1])} mph" if as_env else ""
        )
        self.lbl_pressure_range.setText(
            f"{_fmt(p_env[0])} to {_fmt(p_env[1])} psi" if p_env else ""
        )

    # ---- compute ----

    def _recalc(self):
        sets = [s.values() for s in (self.set1, self.set2)]
        sets = [s for s in sets if s is not None]
        pressure_txt = self.le_pressure.text().strip()
        airspeed_txt = self.le_airspeed.text().strip()
        if not sets or not pressure_txt or not airspeed_txt:
            self._clear_outputs()
            return
        try:
            pressure = float(pressure_txt)
            airspeed = float(airspeed_txt)
        except ValueError:
            self._clear_outputs()
            return

        # Validate every active set against the model up-front so that one
        # out-of-range set takes everything to "--" rather than being silently
        # dropped from a weighted mean.
        per_set_gpms: list[float] = []
        for n, o, a, _q in sets:
            single = AtomizationModel(
                nozzle=n, orifice=o, airspeed=airspeed, pressure=pressure, angle=a,
            )
            if single.dv05() < 0:
                self._clear_outputs()
                return
            per_set_gpms.append(single.calc_gpm())

        if len(sets) == 1:
            n, o, a, qty = sets[0]
            m = AtomizationModel(
                nozzle=n, orifice=o, airspeed=airspeed, pressure=pressure, angle=a,
            )
            dv01, dv05, dv09 = m.dv01(), m.dv05(), m.dv09()
            v100, v200 = m.p_lt_100(), m.p_lt_200()
            total_gpm = per_set_gpms[0] * qty
        else:
            mm = AtomizationModelMulti()
            for n, o, a, q in sets:
                mm.addNozzleSet(name=n, orifice=o, airspeed=airspeed,
                                pressure=pressure, angle=a, quantity=q)
            dv01, dv05, dv09 = mm.dv01(), mm.dv05(), mm.dv09()
            v100, v200 = mm.p_lt_100(), mm.p_lt_200()
            total_gpm = sum(g * q for g, (_, _, _, q) in zip(per_set_gpms, sets))

        if any(v < 0 for v in (dv01, dv05, dv09, v100, v200)):
            self._clear_outputs()
            return

        rs = (dv09 - dv01) / dv05 if dv05 else float("nan")
        self.out_rs.setText(f"{rs:.3f}")
        self.out_v100.setText(str(v100))
        self.out_v200.setText(str(v200))
        self._paint_dsc(self.out_dsc01, dv01, "DV01", prefix=str(dv01))
        self._paint_dsc(self.out_dsc05, dv05, "DV05", prefix=str(dv05))
        self._paint_dsc(self.out_dsc09, dv09, "DV09", prefix=str(dv09))
        composite = self._composite_dsc(dv01, dv05)
        self._paint_dsc_label(self.out_dsc, composite)
        self._render_total_gpm(total_gpm)

    def _composite_dsc(self, dv01: int, dv05: int) -> str:
        helper = AtomizationModel()
        return helper.dsc(dv01=dv01, dv05=dv05)

    def _recalc_boom_flow(self):
        airspeed_txt = self.le_airspeed.text().strip()
        gpa_txt = self.le_gpa.text().strip()
        sw_txt = self.le_swath.text().strip()
        try:
            airspeed = float(airspeed_txt)
            gpa = float(gpa_txt)
            sw = float(sw_txt)
        except ValueError:
            self.out_required_gpm.setText(self.OUT_NA)
        else:
            required = (gpa * airspeed * sw) / 495.0
            self.out_required_gpm.setText(f"{required:.3f}")
        # Re-render total flow so its (% of req'd) suffix tracks the boom-flow state.
        self._render_total_gpm(self._last_total_gpm)

    def _clear_outputs(self):
        for lbl in (self.out_rs, self.out_v100, self.out_v200):
            lbl.setText(self.OUT_NA)
        for lbl in (self.out_dsc01, self.out_dsc05, self.out_dsc09, self.out_dsc):
            self._paint_dsc_label(lbl, "")
        self._render_total_gpm(-1)

    def _paint_dsc(self, label: QLabel, dv: int, dv_key: str, prefix: str = ""):
        category = ""
        for cat, ref in DSC_REFERENCE.items():
            if ref[dv_key][0] <= dv <= ref[dv_key][1]:
                category = cat
                break
        self._paint_dsc_label(label, category, prefix=prefix)

    def _paint_dsc_label(self, label: QLabel, category: str, prefix: str = ""):
        if not category:
            label.setText(self.OUT_NA)
            label.setStyleSheet(
                "background-color: #FFFFFF; color: black; border: 1px solid #888;"
            )
            return
        color = DSC_REFERENCE[category]["Color"]
        text_color = "white" if category in {"VF", "C", "UC"} else "black"
        label.setText(f"{prefix} - {category}" if prefix else category)
        label.setStyleSheet(
            f"background-color: {color}; color: {text_color}; border: 1px solid #444;"
        )

    def _render_total_gpm(self, total_gpm: float):
        self._last_total_gpm = total_gpm
        if total_gpm < 0:
            self.out_gpm.setText(self.OUT_NA)
            return
        required_txt = self.out_required_gpm.text()
        suffix = ""
        try:
            required = float(required_txt)
            if required > 0:
                pct = (total_gpm / required) * 100.0
                suffix = f"  ({pct:.1f}% of req'd)"
        except ValueError:
            pass
        self.out_gpm.setText(f"{total_gpm:.3f}{suffix}")


def _intersection_envelope(names: list[str], attr: str) -> tuple[float, float] | None:
    """Tightest envelope across a set of nozzles (each independently spans LS+HS)."""
    envs = [_envelope(n, attr) for n in names]
    envs = [e for e in envs if e]
    if not envs:
        return None
    lo = max(e[0] for e in envs)
    hi = min(e[1] for e in envs)
    if lo > hi:
        return None
    return lo, hi
