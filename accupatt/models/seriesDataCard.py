import numpy as np
import pandas as pd
import accupatt.config as cfg
from accupatt.models.passDataCard import PassDataCard
from accupatt.models.passData import Pass
from accupatt.models.seriesDataBase import SeriesDataBase
from accupatt.widgets.mplwidget import MplWidget


class SeriesDataCard(SeriesDataBase):
    def __init__(self, passes: list[Pass]):
        super().__init__(passes)

    def _get_active_passes(self) -> list[Pass]:
        activePasses: list[Pass] = []
        for p in self.passes:
            if p.cards.is_active():
                activePasses.append(p)
        return activePasses

    def _get_average(self) -> pd.DataFrame:
        active_passes = self._get_active_passes()
        if not active_passes:
            return pd.DataFrame()

        y_axis = cfg.get_card_plot_y_axis()
        cols = ["loc", cfg.CARD_PLOT_Y_AXIS_COVERAGE, cfg.CARD_PLOT_Y_AXIS_DEPOSITION, "dv01", "dv05"]
        dfs = [
            p.cards.get_data_mod(loc_units=self.swath_units)[cols]
            .set_index("loc")
            .add_suffix(f"_{p.name}")
            for p in active_passes
        ]

        dd = pd.concat(dfs, axis=1).sort_index()
        dd = dd.interpolate(method="slinear", limit_area="inside")

        y_cols = dd.columns[dd.columns.str.contains(y_axis)]
        dd[y_cols] = dd[y_cols].fillna(0)

        avg = pd.DataFrame(index=dd.index)
        avg[y_axis] = dd[y_cols].mean(axis=1)
        avg["dv01"] = dd.loc[:, dd.columns.str.startswith("dv01")].mean(axis=1)
        avg["dv05"] = dd.loc[:, dd.columns.str.startswith("dv05")].mean(axis=1)
        avg["loc_units"] = self.swath_units
        return avg.reset_index()

    def plotOverlay(self, mplWidget: MplWidget):
        # Setup and clear the plotter
        self._config_mpl_plotter(mplWidget)
        mplWidget.canvas.ax.set_ylabel(cfg.get_card_plot_y_axis_label())
        active_passes = self._get_active_passes()
        # Iterate over plottable passes
        for p in active_passes:
            data = p.cards.get_data_mod(loc_units=self.swath_units)
            # Numpy-ize dataframe columns to plot
            x = np.array(data["loc"], dtype=float)
            y = np.array(data[cfg.get_card_plot_y_axis()], dtype=float)
            # Plot non-zero data, and label the series with the pass name
            mplWidget.canvas.ax.plot(x[y != 0], y[y != 0], linewidth=1, label=p.name)
        # Add a legend if applicable
        if len(active_passes) > 1:
            mplWidget.canvas.ax.legend()
        # Must set ylim after plotting
        mplWidget.canvas.ax.set_ylim(bottom=0, auto=None)
        # Draw the plot regardless if passes were plotted to it
        mplWidget.canvas.draw()

    def plotAverage(self, mplWidget: MplWidget):
        # Setup and clear the plotter
        self._config_mpl_plotter(mplWidget)

        avg = self._get_average()
        if avg.empty:
            mplWidget.canvas.draw()
            return
        avgPass = PassDataCard(name="average")
        avgPass.center = self.center
        avgPass.center_method = self.center_method
        avg = avgPass.get_data_mod(loc_units=self.swath_units, data=avg)
        # Must re-add loc_units, as it is stripped during get_data_mod
        avg["loc_units"] = self.swath_units
        avgPass.plot(mplWidget=mplWidget, loc_units=self.swath_units, d=avg)
        if cfg.get_card_plot_average_dash_overlay():
            method = cfg.get_card_plot_average_dash_overlay_method()
            y_axis = cfg.get_card_plot_y_axis()
            if method == cfg.DASH_OVERLAY_METHOD_ISHA:
                # Find average deposition inside swath width
                half_swath = self.swath_adjusted / 2
                dash_x = [-half_swath, -half_swath, half_swath, half_swath]
                a_c = avg[(avg["loc"] >= -half_swath) & (avg["loc"] <= half_swath)]
                a_c_mean = a_c[y_axis].mean(axis="rows")
                dash_y = [0, a_c_mean / 2, a_c_mean / 2, 0]
                dash_label = "Effective Swath"
            else:
                dash_x = [avg["loc"].iloc[0], avg["loc"].iloc[-1]]
                a_mean = avg[y_axis].mean(axis="rows")
                dash_y = [a_mean, a_mean]
                dash_label = f"Avg. {cfg.get_card_plot_y_axis_label()}"
            mplWidget.canvas.ax.plot(
                dash_x,
                dash_y,
                color="black",
                linewidth=1,
                dashes=(3, 2),
                label=dash_label,
            )
            if not cfg.get_card_plot_shading():
                mplWidget.canvas.ax.legend()
            # Must set ylim after plotting
            mplWidget.canvas.ax.set_ylim(bottom=0, auto=None)
            # Plot it
            mplWidget.canvas.draw()

    def plotRacetrack(self, mplWidget: MplWidget):
        self._plotSimulation(mplWidget)

    def plotBackAndForth(self, mplWidget: MplWidget):
        self._plotSimulation(
            mplWidget,
            mirrorAdjascent=True,
        )

    def _plotSimulation(self, mplWidget: MplWidget, mirrorAdjascent=False):
        showEntireWindow = (
            cfg.get_card_simulation_view_window() == cfg.CARD_SIMULATION_VIEW_WINDOW_ALL
        )
        super()._plotSimulation(mplWidget, showEntireWindow, mirrorAdjascent)

    # Overrides for superclass

    def get_average_mod(self):
        avg = self._get_average()
        avgPass = PassDataCard(name="average")
        avgPass.center = self.center
        avgPass.center_method = self.center_method
        return avgPass.get_data_mod(loc_units=self.swath_units, data=avg)
    
    def get_average_y_label(self):
        return cfg.get_card_plot_y_axis()
