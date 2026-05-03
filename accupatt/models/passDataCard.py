import numpy as np
import pandas as pd
from scipy import interpolate
import accupatt.config as cfg
from accupatt.helpers.atomizationModel import AtomizationModel
from accupatt.models.passDataBase import PassDataBase

from accupatt.models.sprayCard import SprayCard
from accupatt.widgets.mplwidget import MplWidget


class PassDataCard(PassDataBase):
    def __init__(self, name):
        super().__init__(name=name)
        # Card Data
        self.card_list: list[SprayCard] = []

    def _get_data_from_card_list(self):
        scs: list[SprayCard] = sorted(
            [
                card
                for card in self.card_list
                if card.has_image
                and card.include_in_composite
                and card.location is not None
                and card.location_units is not None
            ],
            key=lambda x: x.location,
        )
        return pd.DataFrame(
            {
                "name": [card.name for card in scs],
                "loc": [float(card.location) for card in scs],
                "loc_units": [card.location_units for card in scs],
                cfg.CARD_PLOT_Y_AXIS_COVERAGE: [card.stats.get_percent_coverage() for card in scs],
                cfg.CARD_PLOT_Y_AXIS_DEPOSITION: [card.stats.get_deposition() for card in scs],
                "dv01": [card.stats.get_dv01() for card in scs],
                "dv05": [card.stats.get_dv05() for card in scs],
                "dv09": [card.stats.get_dv09() for card in scs],
            }
        )

    def get_data_mod(self, loc_units, data=pd.DataFrame(), doUnits=True, doCenter=True) -> pd.DataFrame:
        if data.empty:
            data = self._get_data_from_card_list()
        if doUnits:
            self._adapt_location_units(data, loc_units)
        if doCenter:
            self._centerify(data, center=self.center, centerMethod=self.center_method)
        # Do more things potentially...
        return data

    def _adapt_location_units(self, d: pd.DataFrame, loc_units):
        mask = d["loc_units"] != loc_units
        ft_mask = mask & (d["loc_units"] == cfg.UNIT_FT)
        d.loc[ft_mask, "loc"] /= cfg.FT_PER_M
        d.loc[mask & ~ft_mask, "loc"] *= cfg.FT_PER_M

    def _centerify(self, d: pd.DataFrame, center, centerMethod):
        if not center or d.empty:
            return
        if centerMethod == cfg.CENTER_METHOD_CENTROID:
            # Use Centroid
            y = d[cfg.get_card_plot_y_axis()]
            c = (y * d["loc"]).sum() / y.sum()
        elif centerMethod == cfg.CENTER_METHOD_COD:
            # Use Center of Distribution
            # Trapezoid integration: weighted midpoint across each adjacent pair of cards
            y = d[cfg.get_card_plot_y_axis()].to_numpy()
            x = d["loc"].to_numpy()
            numerator = (y[:-1] * (x[1:] + x[:-1]) + (y[1:] - y[:-1]) * (2 * x[1:] + x[:-1]) / 3).sum()
            denominator = (y[1:] + y[:-1]).sum()
            c = numerator / denominator
        else:
            # No centering applied
            c = 0
        # Subtract the calculated center from the x vals
        d["loc"] -= c

    """
    Plot Methods
    """

    def _plotSpatialDV(self, mplWidget: MplWidget, x, y_01, y_05, y_09, x_units):
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xlabel(f"Location ({x_units})")
        ax.set_ylabel("Droplet Size (microns)")
        # Populate data if available
        if x is not None:
            ax.plot(x, y_09, label="$D_{V0.9}$")
            ax.plot(x, y_05, label="$VMD$")
            ax.plot(x, y_01, label="$D_{V0.1}$")
            # Legend
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        # Draw the plots
        mplWidget.canvas.draw()

    def plot(
        self,
        mplWidget: MplWidget,
        loc_units,
        # mod=True,
        d=pd.DataFrame(),
    ):
        if d.empty:
            d = self.get_data_mod(loc_units=loc_units, doUnits=True, doCenter=False)
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xlabel(f"Location ({loc_units})")
        ax.set_ylabel(cfg.get_card_plot_y_axis_label())
        # Populate data if available
        if not d["loc"].empty:
            # Interpolate so that fill-between looks good
            locs_i = np.linspace(
                d["loc"].iloc[0], d["loc"].iloc[-1], num=d.shape[0] * 10
            )
            y_i = interpolate.interp1d(d["loc"], d[cfg.get_card_plot_y_axis()], kind="slinear")(locs_i)

            # Colorize
            if cfg.get_card_plot_shading():
                method = cfg.get_card_plot_shading_method()
                if method == cfg.CARD_PLOT_SHADING_METHOD_DSC:
                    # Blank active cards need values for dv01/dv05 for shading, so interpolate
                    d = d.set_index("loc")
                    d = d.sort_index()
                    d["dv01"] = d["dv01"].interpolate(
                        method="slinear", fill_value="extrapolate"
                    )
                    d["dv05"] = d["dv05"].interpolate(
                        method="slinear", fill_value="extrapolate"
                    )
                    d = d.reset_index()
                    # Get a np array of dsc's calculated for each interpolated loc
                    kind = (
                        "slinear"
                        if cfg.get_card_plot_shading_interpolate()
                        else "nearest"
                    )
                    dv_i = interpolate.interp1d(
                        d["loc"],
                        np.array([d["dv01"], d["dv05"]]),
                        kind=kind,
                        fill_value="extrapolate",
                    )(locs_i)
                    model = AtomizationModel()
                    dsc_i = np.array(
                        [
                            model.dsc(dv01=dv01, dv05=dv05)
                            for dv01, dv05 in zip(dv_i[0], dv_i[1])
                        ]
                    )
                    # Plot the fill data using dsc-specified colors
                    categories = list(AtomizationModel.ref_nozzles)
                    colors = [
                        AtomizationModel.ref_nozzles[category]["Color"]
                        for category in categories
                    ]
                    for category, color in zip(categories, colors):
                        # Need to fill in gaps between color changes
                        fill_mask = np.ma.masked_where(dsc_i != category, y_i)
                        if not np.any(np.ma.getmask(fill_mask)):
                            continue
                        diff = np.diff(np.asarray(np.ma.getmask(fill_mask), dtype=int))
                        diff = np.append(diff, 0)  # To sync shape
                        # -1 vals are at trailing ends of unmasked regions
                        fill_mask[diff < 0] = y_i[diff < 0]
                        ax.fill_between(
                            locs_i,
                            fill_mask,
                            color=color,
                            alpha=0.7,
                            label=category,
                        )
                    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                elif method == cfg.CARD_PLOT_SHADING_METHOD_DEPOSITION_AVERAGE:
                    pass
                elif method == cfg.CARD_PLOT_SHADING_METHOD_DEPOSITION_TARGET:
                    pass
            else:
                ax.fill_between(locs_i, 0, y_i, alpha=0.7)
            # Plot base coverage without dsc fill
            ax.plot(locs_i, y_i, color="black")
        # Draw the plots
        # Must set ylim after plotting
        mplWidget.canvas.ax.set_ylim(bottom=0, auto=None)
        mplWidget.canvas.draw()

    """
    Conveneince
    """

    def has_data(self) -> bool:
        return len(self.card_list) > 0

    def is_active(self) -> bool:
        has_data = self.has_data()
        included = self.include_in_composite
        has_included_card = any([sc.include_in_composite for sc in self.card_list])
        return has_data and included and has_included_card
