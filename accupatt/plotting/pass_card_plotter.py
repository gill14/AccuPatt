import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from scipy import interpolate

import accupatt.config as cfg
from aerial_spray_nozzle_models import AtomizationModel
from accupatt.models.passDataCard import PassDataCard
from accupatt.widgets.mplwidget import MplWidget


def plot(
    widget: MplWidget,
    cards: PassDataCard,
    loc_units: str,
    d: pd.DataFrame = pd.DataFrame(),
):
    if d.empty:
        d = cards.get_data_mod(loc_units=loc_units, doUnits=True, doCenter=False)
    ax = widget.canvas.ax
    ax.clear()
    ax.set_xlabel(f"Location ({loc_units})")
    ax.set_ylabel(cfg.get_card_plot_y_axis_label())
    if not d.empty:
        locs_i = np.linspace(d["loc"].iloc[0], d["loc"].iloc[-1], num=d.shape[0] * 10)
        y_i = interpolate.make_interp_spline(
            d["loc"], d[cfg.get_card_plot_y_axis()], k=1
        )(locs_i)
        if cfg.get_card_plot_shading():
            method = cfg.get_card_plot_shading_method()
            if method == cfg.CARD_PLOT_SHADING_METHOD_DSC:
                d = d.set_index("loc").sort_index()
                d["dv01"] = d["dv01"].interpolate(
                    method="slinear", fill_value="extrapolate"
                )
                d["dv05"] = d["dv05"].interpolate(
                    method="slinear", fill_value="extrapolate"
                )
                d = d.reset_index()
                kind = (
                    "slinear" if cfg.get_card_plot_shading_interpolate() else "nearest"
                )
                if kind == "slinear":
                    dv_i = interpolate.make_interp_spline(
                        d["loc"], np.array([d["dv01"], d["dv05"]]).T, k=1
                    )(locs_i).T
                else:
                    idx = np.abs(d["loc"].values[:, None] - locs_i[None, :]).argmin(axis=0)
                    dv_i = np.array([d["dv01"].values, d["dv05"].values])[:, idx]
                model = AtomizationModel()
                dsc_i = np.array(
                    [
                        model.dsc(dv01=dv01, dv05=dv05)
                        for dv01, dv05 in zip(dv_i[0], dv_i[1])
                    ]
                )
                categories = list(AtomizationModel.ref_nozzles)
                colors = [
                    AtomizationModel.ref_nozzles[cat]["Color"] for cat in categories
                ]
                for category, color in zip(categories, colors):
                    fill_mask = np.ma.masked_where(dsc_i != category, y_i)
                    if not fill_mask.count():
                        continue
                    diff = np.diff(np.asarray(np.ma.getmaskarray(fill_mask), dtype=int))
                    diff = np.append(diff, 0)
                    fill_mask[diff < 0] = y_i[diff < 0]
                    ax.fill_between(locs_i, fill_mask, color=color, alpha=0.7)
                legend_elements = [
                    Patch(facecolor=color, alpha=0.7, label=category)
                    for category, color in zip(categories, colors)
                ]
                ax.legend(handles=legend_elements, loc="center left", bbox_to_anchor=(1, 0.5))
        else:
            ax.fill_between(locs_i, 0, y_i, alpha=0.7)
        ax.plot(locs_i, y_i, color="black")
    widget.canvas.ax.set_ylim(bottom=0, auto=None)
    widget.canvas.draw()
