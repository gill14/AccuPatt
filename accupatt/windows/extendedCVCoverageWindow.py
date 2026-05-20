import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

import accupatt.config as cfg
from accupatt.models.seriesDataCard import SeriesDataCard


def _round_to_step(val: float, units: str) -> float:
    if units == cfg.UNIT_FT:
        return float(round(val))
    return round(val * 2) / 2


class ExtendedCVCoverageWindow(QDialog):
    def __init__(self, series: SeriesDataCard, parent=None):
        super().__init__(parent=parent)
        self.series = series
        self._swaths: list[float] = []
        self._cvs: list[float] = []
        self._min_covs: list[float] = []
        self._mean_covs: list[float] = []
        self._max_covs: list[float] = []
        self._bands: list = []

        units = series.swath_units
        is_ft = units == cfg.UNIT_FT
        default_step = 2.0 if is_ft else 0.5
        decimals = 0 if is_ft else 1
        spin_min_val = 1.0 if is_ft else 0.5
        spin_max_val = 500.0 if is_ft else 200.0

        adj = series.swath_adjusted
        default_min = max(default_step, _round_to_step(0.25 * adj, units))
        default_max = _round_to_step(2.0 * adj, units)
        if default_max <= default_min:
            default_max = default_min + default_step

        self.setWindowTitle("Extended CV/Coverage Simulations")
        self.resize(1050, 560)
        self.setWindowFlag(Qt.WindowType.Window, True)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # ── Left pane ────────────────────────────────────────────────────────
        left_frame = QFrame()
        left_frame.setMaximumWidth(230)
        left_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Swath Width Range
        gb_range = QGroupBox("Swath Width Range")
        form = QFormLayout(gb_range)
        form.setSpacing(4)

        self.spinMin = QDoubleSpinBox()
        self.spinMin.setDecimals(decimals)
        self.spinMin.setSingleStep(default_step)
        self.spinMin.setMinimum(spin_min_val)
        self.spinMin.setMaximum(spin_max_val)
        self.spinMin.setValue(default_min)
        self.spinMin.setSuffix(f" {units}")
        form.addRow("Min:", self.spinMin)

        self.spinMax = QDoubleSpinBox()
        self.spinMax.setDecimals(decimals)
        self.spinMax.setSingleStep(default_step)
        self.spinMax.setMinimum(spin_min_val)
        self.spinMax.setMaximum(spin_max_val)
        self.spinMax.setValue(default_max)
        self.spinMax.setSuffix(f" {units}")
        form.addRow("Max:", self.spinMax)

        self.spinStep = QDoubleSpinBox()
        self.spinStep.setDecimals(decimals)
        self.spinStep.setSingleStep(default_step)
        self.spinStep.setMinimum(spin_min_val)
        self.spinStep.setMaximum(20.0 if is_ft else 10.0)
        self.spinStep.setValue(default_step)
        self.spinStep.setSuffix(f" {units}")
        form.addRow("Step:", self.spinStep)

        left_layout.addWidget(gb_range)

        # Application Method — wrapped in QGroupBox so font matches the others
        gb_method = QGroupBox("Application Method")
        method_vbox = QVBoxLayout(gb_method)
        method_vbox.setContentsMargins(4, 4, 4, 4)
        self.comboMethod = QComboBox()
        self.comboMethod.addItems(["Back & Forth", "Racetrack"])
        method_vbox.addWidget(self.comboMethod)
        left_layout.addWidget(gb_method)

        # Coverage Stacking
        gb_stacking = QGroupBox("Coverage Stacking")
        stacking_layout = QVBoxLayout(gb_stacking)
        stacking_layout.setSpacing(4)

        self.rbLinear = QRadioButton("Linear")
        self.rbLinear.setChecked(True)
        row_linear = QHBoxLayout()
        row_linear.setSpacing(4)
        row_linear.addWidget(self.rbLinear)
        row_linear.addWidget(self._info_label(
            "Coverage values are summed linearly across passes.\n"
            "Cumulative values may exceed 100% at overlap zones."
        ))
        row_linear.addStretch()
        stacking_layout.addLayout(row_linear)

        self.rbCompound = QRadioButton("Compound")
        row_compound = QHBoxLayout()
        row_compound.setSpacing(4)
        row_compound.addWidget(self.rbCompound)
        row_compound.addWidget(self._info_label(
            "Each pass covers only the remaining uncovered area.\n"
            "Cumulative coverage is bounded at 100%."
        ))
        row_compound.addStretch()
        stacking_layout.addLayout(row_compound)

        left_layout.addWidget(gb_stacking)

        # Targets
        gb_targets = QGroupBox("Targets")
        targets_form = QFormLayout(gb_targets)
        targets_form.setSpacing(4)

        self.spinTargetMinCov = QDoubleSpinBox()
        self.spinTargetMinCov.setRange(0.0, 200.0)
        self.spinTargetMinCov.setDecimals(1)
        self.spinTargetMinCov.setSingleStep(1.0)
        self.spinTargetMinCov.setValue(2.0)
        self.spinTargetMinCov.setSuffix(" %")
        targets_form.addRow("Min Coverage:", self.spinTargetMinCov)

        self.spinTargetMaxCov = QDoubleSpinBox()
        self.spinTargetMaxCov.setRange(0.0, 200.0)
        self.spinTargetMaxCov.setDecimals(1)
        self.spinTargetMaxCov.setSingleStep(1.0)
        self.spinTargetMaxCov.setValue(100.0)
        self.spinTargetMaxCov.setSuffix(" %")
        targets_form.addRow("Max Coverage:", self.spinTargetMaxCov)

        self.spinTargetMaxCV = QDoubleSpinBox()
        self.spinTargetMaxCV.setRange(0.0, 200.0)
        self.spinTargetMaxCV.setDecimals(1)
        self.spinTargetMaxCV.setSingleStep(1.0)
        self.spinTargetMaxCV.setValue(20.0)
        self.spinTargetMaxCV.setSuffix(" %")
        targets_form.addRow("Max CV:", self.spinTargetMaxCV)

        left_layout.addWidget(gb_targets)

        left_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        btn_copy = QPushButton("Copy Tabular Data to Clipboard")
        btn_copy.clicked.connect(self._copy_to_clipboard)
        left_layout.addWidget(btn_copy)

        main_layout.addWidget(left_frame)

        # ── Right pane: pyqtgraph plot ────────────────────────────────────────
        self._build_plot(units, adj)
        main_layout.addWidget(self.plot, stretch=1)

        # ── Debounce timer for live updates ───────────────────────────────────
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(150)
        self._timer.timeout.connect(self._update)

        self.spinMin.valueChanged.connect(self._schedule_update)
        self.spinMax.valueChanged.connect(self._schedule_update)
        self.spinStep.valueChanged.connect(self._schedule_update)
        self.comboMethod.currentIndexChanged.connect(self._schedule_update)
        self.rbLinear.toggled.connect(self._schedule_update)
        self.spinTargetMinCov.valueChanged.connect(self._schedule_update)
        self.spinTargetMaxCov.valueChanged.connect(self._schedule_update)
        self.spinTargetMaxCV.valueChanged.connect(self._schedule_update)

        # Initial paint
        self._update()

    @staticmethod
    def _info_label(tooltip: str) -> QLabel:
        lbl = QLabel("ⓘ")
        lbl.setToolTip(tooltip)
        lbl.setStyleSheet("color: #5b9bd5;")
        lbl.setCursor(Qt.CursorShape.WhatsThisCursor)
        return lbl

    def _build_plot(self, units: str, adj: float):
        self.plot = pg.PlotWidget()
        pi = self.plot.plotItem

        pi.showAxis("right")
        pi.setLabel("bottom", f"Swath Width ({units})")
        pi.setLabel("left", "Coverage CV (%)")
        pi.setLabel("right", "Coverage (%)")

        # Second ViewBox for the right (coverage) axis
        self._p2 = pg.ViewBox()
        pi.scene().addItem(self._p2)
        pi.getAxis("right").linkToView(self._p2)
        self._p2.setXLink(pi)
        pi.vb.sigResized.connect(self._sync_views)

        # Auto-range y-axis to visible data only
        pi.vb.setAutoVisible(y=True)
        self._p2.setAutoVisible(y=True)

        # Legend — inside axes, top-right
        self._legend = pi.addLegend(offset=(-10, 10))

        # CV curve (left axis)
        self._cv_curve = pi.plot([], [], pen=pg.mkPen("#4c78a8", width=2), name="CV %")

        # Coverage curves (right axis)
        self._min_cov_curve = pg.PlotCurveItem(
            [], [], pen=pg.mkPen("#54a24b", width=2)
        )
        self._mean_cov_curve = pg.PlotCurveItem(
            [], [], pen=pg.mkPen("#ffff66", width=2)
        )
        self._max_cov_curve = pg.PlotCurveItem(
            [], [], pen=pg.mkPen("#ff3300", width=2)
        )
        self._p2.addItem(self._min_cov_curve)
        self._p2.addItem(self._mean_cov_curve)
        self._p2.addItem(self._max_cov_curve)
        self._legend.addItem(self._min_cov_curve, "Min Coverage %")
        self._legend.addItem(self._mean_cov_curve, "Mean Coverage %")
        self._legend.addItem(self._max_cov_curve, "Max Coverage %")

        # Reference line at adjusted swath width
        pi.addItem(pg.InfiniteLine(
            pos=adj,
            angle=90,
            pen=pg.mkPen("gray", width=1, style=Qt.PenStyle.DashLine),
            label=f"Adj. Swath ({adj} {units})",
            labelOpts={
                "position": 0.95,
                "color": "gray",
                "fill": pg.mkBrush(0, 0, 0, 130),
            },
        ))

        # Cursor vertical line
        self._cursor_line = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen("white", width=1, style=Qt.PenStyle.DotLine),
        )
        self._cursor_line.setVisible(False)
        pi.addItem(self._cursor_line, ignoreBounds=True)

        # Cursor value bubble
        self._cursor_text = pg.TextItem(
            anchor=(0, 0),
            fill=pg.mkBrush(30, 30, 30, 210),
            border=pg.mkPen("gray", width=1),
        )
        self._cursor_text.setVisible(False)
        pi.addItem(self._cursor_text, ignoreBounds=True)

        self._proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self._on_mouse_moved,
        )

    def _sync_views(self):
        self._p2.setGeometry(self.plot.plotItem.vb.sceneBoundingRect())
        self._p2.linkedViewChanged(self.plot.plotItem.vb, self._p2.XAxis)

    @pyqtSlot()
    def _schedule_update(self):
        self._timer.start()

    def _update(self):
        min_sw = self.spinMin.value()
        max_sw = self.spinMax.value()
        step = self.spinStep.value()
        if step <= 0 or min_sw > max_sw:
            return

        mirror = self.comboMethod.currentIndex() == 0
        compound = self.rbCompound.isChecked()
        y_label = cfg.CARD_PLOT_Y_AXIS_COVERAGE

        avg_df = self.series.get_average_mod(y_label=y_label)
        if avg_df.empty:
            return

        swaths, cvs, min_covs, mean_covs, max_covs = [], [], [], [], []
        sw = min_sw
        while sw <= max_sw + step * 1e-6:
            cv, min_c, mean_c, max_c = self.series._calc_cv_coverage_stats(
                avg_df, y_label, sw, mirrorAdjacent=mirror, compound=compound
            )
            swaths.append(sw)
            cvs.append(cv)
            min_covs.append(min_c)
            mean_covs.append(mean_c)
            max_covs.append(max_c)
            sw = round(sw + step, 6)

        self._swaths = swaths
        self._cvs = cvs
        self._min_covs = min_covs
        self._mean_covs = mean_covs
        self._max_covs = max_covs

        arr = np.array(swaths, dtype=float)
        self._cv_curve.setData(arr, np.array(cvs, dtype=float))
        self._min_cov_curve.setData(arr, np.array(min_covs, dtype=float))
        self._mean_cov_curve.setData(arr, np.array(mean_covs, dtype=float))
        self._max_cov_curve.setData(arr, np.array(max_covs, dtype=float))

        self.plot.plotItem.vb.enableAutoRange(axis=pg.ViewBox.YAxis)
        self._p2.enableAutoRange(axis=pg.ViewBox.YAxis)
        self._sync_views()
        self._update_bands()

    def _update_bands(self):
        pi = self.plot.plotItem
        for band in self._bands:
            pi.removeItem(band)
        self._bands.clear()

        if not self._swaths:
            return

        target_min_cov = self.spinTargetMinCov.value()
        target_max_cov = self.spinTargetMaxCov.value()
        target_max_cv = self.spinTargetMaxCV.value()
        step = self.spinStep.value()

        valid = [
            cv <= target_max_cv
            and min_c >= target_min_cov
            and max_c <= target_max_cov
            for cv, min_c, max_c in zip(self._cvs, self._min_covs, self._max_covs)
        ]

        i = 0
        while i < len(valid):
            if valid[i]:
                j = i
                while j < len(valid) and valid[j]:
                    j += 1
                band = pg.LinearRegionItem(
                    values=[self._swaths[i] - step / 2, self._swaths[j - 1] + step / 2],
                    movable=False,
                    brush=pg.mkBrush(255, 255, 255, 40),
                    pen=pg.mkPen(None),
                )
                band.setZValue(-10)
                pi.addItem(band, ignoreBounds=True)
                self._bands.append(band)
                i = j
            else:
                i += 1

    def _on_mouse_moved(self, event):
        pos = event[0]
        pi = self.plot.plotItem
        vb = pi.vb
        if not self._swaths or not self.plot.sceneBoundingRect().contains(pos):
            self._cursor_line.setVisible(False)
            self._cursor_text.setVisible(False)
            return

        mouse_pt = vb.mapSceneToView(pos)
        x = mouse_pt.x()
        arr = np.array(self._swaths, dtype=float)
        idx = int(np.argmin(np.abs(arr - x)))
        sw = self._swaths[idx]

        self._cursor_line.setPos(sw)
        self._cursor_line.setVisible(True)

        x_range = vb.viewRange()[0]
        y_top = vb.viewRange()[1][1]
        anchor = (0, 0) if sw <= (x_range[0] + x_range[1]) / 2 else (1, 0)
        self._cursor_text.setAnchor(anchor)
        self._cursor_text.setPos(sw, y_top)

        units = self.series.swath_units
        is_ft = units == cfg.UNIT_FT
        sw_fmt = f"{sw:.0f}" if is_ft else f"{sw:.1f}"
        self._cursor_text.setText(
            f"{sw_fmt} {units}\n"
            f"CV: {self._cvs[idx]}%\n"
            f"Min Cov: {self._min_covs[idx]:.1f}%\n"
            f"Mean Cov: {self._mean_covs[idx]:.1f}%\n"
            f"Max Cov: {self._max_covs[idx]:.1f}%"
        )
        self._cursor_text.setVisible(True)

    @pyqtSlot()
    def _copy_to_clipboard(self):
        if not self._swaths:
            return
        units = self.series.swath_units
        is_ft = units == cfg.UNIT_FT
        fmt = "{:.0f}" if is_ft else "{:.1f}"
        headers = [f"Swath Width ({units})", "CV %", "Min Coverage %", "Mean Coverage %", "Max Coverage %"]
        rows = ["\t".join(headers)]
        for sw, cv, min_c, mean_c, max_c in zip(
            self._swaths, self._cvs, self._min_covs, self._mean_covs, self._max_covs
        ):
            rows.append("\t".join([
                f"{fmt.format(sw)} {units}",
                f"{cv} %",
                f"{min_c:.1f} %",
                f"{mean_c:.1f} %",
                f"{max_c:.1f} %",
            ]))
        QApplication.clipboard().setText("\n".join(rows))
