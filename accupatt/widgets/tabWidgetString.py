import os

import accupatt.config as cfg
from PyQt6.QtCore import Qt, QPointF, QTimer, pyqtSlot, QSignalBlocker
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QCheckBox, QGraphicsProxyWidget, QPushButton
from pyqtgraph import PlotWidget

from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.plotting import pass_string_plotter, series_string_plotter, series_base_plotter
from accupatt.widgets.tabWidgetBase import TabWidgetBase
from accupatt.windows.stringPass import StringPass
from accupatt.windows.stringPlotOptions import StringPlotOptions


class TabWidgetString(TabWidgetBase):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(
            ui_file=os.path.join(os.getcwd(), "resources", "stringMainWidget.ui"),
            subtype="string",
            parent=parent,
            *args,
            **kwargs,
        )

        self.checkBoxPassRebase: QCheckBox = self.ui.checkBoxPassRebase
        self.checkBoxPassRebase.stateChanged[int].connect(self.passRebaseChanged)

        self.checkBoxSeriesEqualize: QCheckBox = self.ui.checkBoxSeriesEqualize
        self.checkBoxSeriesEqualize.stateChanged[int].connect(
            self.seriesEqualizeChanged
        )

        self.plotWidgetIndividual: PlotWidget = self.ui.plotWidgetIndividual
        self.plotWidgetIndividualTrim: PlotWidget = self.ui.plotWidgetIndividualTrim

        self._snr_proxy: QGraphicsProxyWidget | None = None
        self._floor_line_ref: object | None = None

    """
    External Method to fill data
    """

    def setData(self, seriesData: SeriesData):
        super().setData(seriesData=seriesData)
        with QSignalBlocker(self.checkBoxSeriesEqualize):
            self.checkBoxSeriesEqualize.setChecked(
                self.seriesData.string.equalize_integrals
            )

    """
    Pass List Widget
    """

    @pyqtSlot()
    def passSelectionChanged(self):
        if not (passData := self.getCurrentPass()):
            return
        self.checkBoxPassCenter.setEnabled(not passData.string.rebase)
        with QSignalBlocker(self.checkBoxPassRebase):
            self.checkBoxPassRebase.setChecked(passData.string.rebase)
        super().passSelectionChanged()

    """
    Edit Pass Button & Methods
    """

    @pyqtSlot()
    def editPass(self):
        if passData := self.getCurrentPass():
            e = StringPass(passData=passData, parent=self.parent())
            e.accepted.connect(self.onEditPassAccepted)
            e.show()

    """
    Pass Data Mod Options
    """

    @pyqtSlot(int)
    def passRebaseChanged(self, checkstate):
        if passData := self.getCurrentPass():
            passData.string.rebase = Qt.CheckState(checkstate) == Qt.CheckState.Checked
            if passData.string.rebase:
                passData.string.center = True
                self.checkBoxPassCenter.setChecked(passData.string.center)
            self.checkBoxPassCenter.setEnabled(not passData.string.rebase)
            self.updatePlots(
                modify=True, individuals=True, composites=True, simulations=True
            )

    """
    Series Data Mod Options
    """

    @pyqtSlot(int)
    def seriesEqualizeChanged(self, checkstate):
        self.seriesData.string.equalize_integrals = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updatePlots(modify=True, composites=True, simulations=True)

    @pyqtSlot()
    def clickedPlotOptions(self):
        spo = StringPlotOptions(parent=self)
        spo.request_update_plots[bool, bool, bool].connect(
            lambda a, b, c: self.updatePlots(individuals=a, composites=b, simulations=c)
        )
        spo.show()

    """
    Individual Passes Tab
    """

    @pyqtSlot(object)
    def _updateTrimL(self, object):
        self.getCurrentPass().string.user_set_trim_left(object.value())
        self.updatePlots(
            modify=True, individuals=True, composites=True, simulations=True
        )

    @pyqtSlot(object)
    def _updateTrimR(self, object):
        self.getCurrentPass().string.user_set_trim_right(object.value())
        self.updatePlots(
            modify=True, individuals=True, composites=True, simulations=True
        )

    @pyqtSlot(object)
    def _updateTrimFloor(self, object):
        self.getCurrentPass().string.user_set_trim_floor(object.value())
        self.updatePlots(
            modify=True, individuals=True, composites=True, simulations=True
        )

    """
    Simulations Tab
    """

    """
    Plot triggers
    """

    def modify_triggered(self):
        self.seriesData.string.modifyPatterns()

    def individuals_triggered(self, passData: Pass):
        self._remove_snr_button()
        passData.string.snr_result = pass_string_plotter.compute_snr(passData.string)
        line_left, line_right, line_vertical = pass_string_plotter.plot_individual(
            self.plotWidgetIndividual, passData.string
        )
        if (
            line_left is not None
            and line_right is not None
            and line_vertical is not None
        ):
            line_left.sigPositionChangeFinished.connect(self._updateTrimL)
            line_right.sigPositionChangeFinished.connect(self._updateTrimR)
            line_vertical.sigPositionChangeFinished.connect(self._updateTrimFloor)
            self._add_snr_button(line_vertical)
        pass_string_plotter.plot_individual_trim(
            self.plotWidgetIndividualTrim, passData.string
        )

    """
    SNR Snap Button
    """

    def _add_snr_button(self, floor_line):
        self._floor_line_ref = floor_line
        btn = QPushButton("Snap to SNR=3")
        btn.setStyleSheet("""
            QPushButton {
                color: yellow;
                border: 1px solid yellow;
                border-radius: 3px;
                padding: 2px 14px;
                background-color: rgba(0, 0, 0, 128);
                font-weight: normal;
            }
            QPushButton:hover {
                border: 2px solid yellow;
                font-weight: bold;
            }
        """)
        # Pre-size to bold font metrics so the proxy widget frame is wide enough
        # before hover occurs and the text never clips.
        bold_font = QFont(btn.font())
        bold_font.setBold(True)
        btn.setMinimumWidth(
            QFontMetrics(bold_font).horizontalAdvance(btn.text()) + 32
        )
        self._snr_proxy = QGraphicsProxyWidget()
        self._snr_proxy.setWidget(btn)
        self.plotWidgetIndividual.scene().addItem(self._snr_proxy)
        btn.clicked.connect(self._runSNRTest)
        floor_line.sigPositionChanged.connect(self._updateSNRButtonPos)
        self.plotWidgetIndividual.plotItem.vb.sigRangeChanged.connect(
            self._updateSNRButtonPos
        )
        self._updateSNRButtonPos()

    def _remove_snr_button(self):
        if self._snr_proxy is not None:
            self.plotWidgetIndividual.scene().removeItem(self._snr_proxy)
            self._snr_proxy = None
        self._floor_line_ref = None

    @pyqtSlot()
    def _updateSNRButtonPos(self):
        if self._snr_proxy is None or self._floor_line_ref is None:
            return
        vb = self.plotWidgetIndividual.plotItem.vb
        x_range = vb.viewRange()[0]
        center_x = (x_range[0] + x_range[1]) / 2
        floor_y = self._floor_line_ref.value()
        scene_pos = vb.mapViewToScene(QPointF(center_x, floor_y))
        sz = self._snr_proxy.widget().sizeHint()
        # scene y increases downward — +10 px places button just below the floor line
        self._snr_proxy.setPos(scene_pos.x() - sz.width() / 2, scene_pos.y() + 10)

    @pyqtSlot()
    def _runSNRTest(self):
        if not (passData := self.getCurrentPass()):
            return
        result = passData.string.snr_result
        if result is None:
            return
        N_rms, y_bar, *_ = result
        passData.string.user_set_trim_floor(y_bar + 3 * N_rms)
        # Defer the replot so Qt finishes the current mouse-release event on the
        # proxy widget before _remove_snr_button() destroys it from the scene.
        QTimer.singleShot(
            0,
            lambda: self.updatePlots(
                modify=True, individuals=True, composites=True, simulations=True
            ),
        )

    def composites_triggered(self):
        series_string_plotter.plot_overlay(self.plotWidgetOverlay, self.seriesData.string)
        series_string_plotter.plot_average(self.plotWidgetAverage, self.seriesData.string)

    def simulations_triggered(self):
        series_string_plotter.plot_racetrack(self.plotWidgetRacetrack, self.seriesData.string)
        series_string_plotter.plot_back_and_forth(
            self.plotWidgetBackAndForth, self.seriesData.string
        )
        series_base_plotter.plot_cv_table(self.tableWidgetCV, self.seriesData.string)
