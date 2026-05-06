import numpy as np
from pyqtgraph import InfiniteLine, PlotWidget, setConfigOptions
from pyqtgraph.functions import mkPen

from accupatt.models.passDataString import PassDataString


def plot_individual(
    widget: PlotWidget, string: PassDataString
) -> tuple[InfiniteLine, InfiniteLine, InfiniteLine]:
    _configure(widget, string.data_loc_units)
    if string.data.empty:
        return None, None, None
    min_ = string.findMin(string.data, string.trim_l, string.trim_r)
    x = string.data["loc"].to_numpy(dtype=float)
    y = string.data[string.name].to_numpy(dtype=float)
    floor = min_ + string.trim_v
    widget.plotItem.plot(name="Raw", pen="w").setData(x, y)
    trim_left = InfiniteLine(
        pos=x[0 + string.trim_l],
        movable=True,
        pen="y",
        hoverPen=mkPen("y", width=3),
        label="Trim L = {value:0.2f}",
        labelOpts={"color": "y", "position": 0.9},
    )
    trim_right = InfiniteLine(
        pos=x[-1 - string.trim_r],
        movable=True,
        pen="y",
        hoverPen=mkPen("y", width=3),
        label="Trim R = {value:0.2f}",
        labelOpts={"color": "y", "position": 0.9},
    )
    trim_vertical = InfiniteLine(
        pos=floor,
        angle=0,
        movable=True,
        pen="y",
        hoverPen=mkPen("y", width=3),
        label="Floor = {value:0.2f}",
        labelOpts={"color": "y", "position": 0.5},
    )
    widget.addItem(trim_left)
    widget.addItem(trim_right)
    widget.addItem(trim_vertical)
    return trim_left, trim_right, trim_vertical


def plot_individual_trim(widget: PlotWidget, string: PassDataString):
    _configure(widget, string.data_loc_units)
    if string.data.empty:
        return
    rebase_str = ", Rebased" if string.rebase else ""

    # Trimmed, unsmoothed — use to establish the active (non-zero) extent
    d = string.get_data_mod(smooth_override=False)
    nz = np.flatnonzero(d[string.name])
    if not nz.size:
        return
    sl = slice(nz[0], nz[-1] + 1)
    x = d["loc"].to_numpy(dtype=float)[sl]
    y = d[string.name].to_numpy(dtype=float)[sl]
    widget.plotItem.plot(name=f"Trimmed{rebase_str}", pen="w").setData(x, y)

    if string.smooth:
        d_smooth = string.get_data_mod()
        y_smooth = d_smooth[string.name].to_numpy(dtype=float)[sl]
        widget.plotItem.plot(
            name=f"Trimmed{rebase_str}, Smoothed", pen=mkPen("y", width=3)
        ).setData(x, y_smooth)
        valid = y_smooth[y_smooth > 0]
        if valid.size:
            padding = (valid.max() - valid.min()) * 0.05
            widget.plotItem.setYRange(
                valid.min() - padding, valid.max() + padding, padding=0
            )

def _configure(widget: PlotWidget, loc_units: str):
    setConfigOptions(antialias=True, background="k", foreground="w")
    widget.plotItem.clear()
    widget.plotItem.setLabel(axis="bottom", text="Location", units=loc_units)
    widget.plotItem.setLabel(axis="left", text="Dye Intensity")
    widget.plotItem.showGrid(x=True, y=True)
    widget.plotItem.addLegend(offset=(5, 5))
