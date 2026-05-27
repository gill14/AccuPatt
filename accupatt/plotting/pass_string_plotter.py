import numpy as np
from pyqtgraph import InfiniteLine, LinearRegionItem, PlotWidget, TextItem, setConfigOptions
from pyqtgraph.functions import mkBrush, mkPen

import accupatt.config as cfg
from accupatt.models.passDataString import PassDataString

_SAT_LEVEL = 65535.0  # 16-bit spectrometer ceiling (AU)


def _display_scale() -> float:
    return 1.0 / cfg.AU_PER_PERCENT_16_BIT if cfg.get_spectrometer_display_unit() == cfg.SPECTROMETER_DISPLAY_UNIT_RELATIVE else 1.0


def plot_individual(
    widget: PlotWidget, string: PassDataString
) -> tuple[InfiniteLine, InfiniteLine, InfiniteLine]:
    _configure(widget, string.data_loc_units)
    if string.data.empty:
        return None, None, None
    scale = _display_scale()
    min_ = string.findMin(string.data, string.trim_l, string.trim_r)
    x = string.data["loc"].to_numpy(dtype=float)
    y_raw = string.data[string.name].to_numpy(dtype=float)
    y_disp = y_raw * scale
    floor_disp = (min_ + string.trim_v) * scale
    # Draw SNR overlay first so data and trim lines render on top
    if string.snr_result is not None:
        N_rms, y_bar, noise_x_start, noise_x_end = string.snr_result
        _plot_snr_overlay(widget, x, y_disp, N_rms * scale, y_bar * scale, noise_x_start, noise_x_end)
    widget.plotItem.plot(name="Raw", pen="w").setData(x, y_disp)
    _plot_saturation_warning(widget, x, y_raw, y_disp)
    trim_left = InfiniteLine(
        pos=x[0 + string.trim_l],
        movable=True,
        pen="y",
        hoverPen=mkPen("y", width=3),
        label="Trim L = {value:0.2f}",
        labelOpts={"color": "y", "position": 0.95, "anchor": (0, 0)},
    )
    trim_right = InfiniteLine(
        pos=x[-1 - string.trim_r],
        movable=True,
        pen="y",
        hoverPen=mkPen("y", width=3),
        label="Trim R = {value:0.2f}",
        labelOpts={"color": "y", "position": 0.95, "anchor": (1, 0)},
    )
    trim_vertical = InfiniteLine(
        pos=floor_disp,
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


def compute_snr(string: PassDataString) -> tuple | None:
    """Find noise floor via min contiguous 5% window; return (N_rms, y_bar, x_start, x_end)."""
    if string.data.empty:
        return None
    x = string.data["loc"].to_numpy(dtype=float)
    y = string.data[string.name].to_numpy(dtype=float)
    trim_l, trim_r = string.trim_l, string.trim_r
    end_idx = len(y) - trim_r if trim_r > 0 else len(y)
    x_trim = x[trim_l:end_idx]
    y_trim = y[trim_l:end_idx]
    if len(y_trim) < 20:
        return None
    min_ = float(y_trim.min())
    y_base = y_trim - min_
    window = max(2, int(len(y_base) * 0.05))
    best_start, best_sum = 0, float("inf")
    for i in range(len(y_base) - window + 1):
        s = float(np.sum(y_base[i : i + window]))
        if s < best_sum:
            best_sum, best_start = s, i
    noise_region = y_base[best_start : best_start + window]
    N_rms = float(np.std(noise_region, ddof=1))
    if N_rms < 1e-9:
        return None
    # y_bar in raw y-space: mean of the noise window above the absolute minimum
    y_bar = min_ + float(np.mean(noise_region))
    return N_rms, y_bar, float(x_trim[best_start]), float(x_trim[best_start + window - 1])


def _plot_snr_overlay(
    widget: PlotWidget,
    x: np.ndarray,
    y: np.ndarray,
    N_rms: float,
    y_bar: float,
    noise_x_start: float,
    noise_x_end: float,
):
    snr3_y = y_bar + 3 * N_rms
    snr10_y = y_bar + 10 * N_rms
    large_y = max(y.max() * 10, snr10_y * 100, 1e9)

    _no_line = mkPen(None)
    for values, color in [
        ((y_bar, snr3_y), (220, 50, 50, 50)),
        ((snr3_y, snr10_y), (220, 180, 0, 50)),
        ((snr10_y, large_y), (50, 200, 50, 50)),
    ]:
        region = LinearRegionItem(
            values=values,
            orientation="horizontal",
            brush=mkBrush(*color),
            movable=False,
        )
        region.lines[0].setPen(_no_line)
        region.lines[1].setPen(_no_line)
        widget.addItem(region, ignoreBounds=True)

    # Highlight noise floor region with a bold red line
    mask = (x >= noise_x_start) & (x <= noise_x_end)
    if mask.any():
        widget.plotItem.plot(
            name="Noise Floor", pen=mkPen("r", width=3)
        ).setData(x[mask], y[mask])


def _plot_saturation_warning(widget: PlotWidget, x: np.ndarray, y_raw: np.ndarray, y_disp: np.ndarray):
    sat_mask = y_raw >= _SAT_LEVEL
    if not sat_mask.any():
        return
    _sat_color = (255, 140, 0)
    widget.plotItem.plot(
        name="Saturated", pen=mkPen(_sat_color, width=3)
    ).setData(x[sat_mask], y_disp[sat_mask])
    warning = TextItem(
        text="⚠ Saturation Detected",
        color=_sat_color,
        anchor=(1, 0),
    )
    widget.addItem(warning)
    warning.setPos(x[-1], float(y_disp.max()))


def plot_individual_trim(widget: PlotWidget, string: PassDataString):
    _configure(widget, string.data_loc_units)
    if string.data.empty:
        return
    scale = _display_scale()
    rebase_str = ", Rebased" if string.rebase else ""

    # Trimmed, unsmoothed — use to establish the active (non-zero) extent
    d = string.get_data_mod(smooth_override=False)
    nz = np.flatnonzero(d[string.name])
    if not nz.size:
        return
    sl = slice(nz[0], nz[-1] + 1)
    x = d["loc"].to_numpy(dtype=float)[sl]
    y = d[string.name].to_numpy(dtype=float)[sl] * scale
    widget.plotItem.plot(name=f"Trimmed{rebase_str}", pen="w").setData(x, y)

    if string.smooth:
        d_smooth = string.get_data_mod()
        y_smooth = d_smooth[string.name].to_numpy(dtype=float)[sl] * scale
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
    widget.plotItem.setLabel(axis="left", text="Intensity (%)" if _display_scale() != 1.0 else "Intensity (AU)")
    widget.plotItem.getAxis("left").enableAutoSIPrefix(False)
    widget.plotItem.showGrid(x=True, y=True)
    widget.plotItem.addLegend(offset=(5, 5))
