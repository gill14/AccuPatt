import copy

import numpy as np
import pandas as pd
import accupatt.config as cfg
from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.widgets.mplwidget import MplWidget
from PyQt6.QtWidgets import QTableWidget
from pyqtgraph import InfiniteLine, PlotWidget, setConfigOptions
from pyqtgraph.functions import mkPen, mkBrush
from scipy.stats import variation


class StringPlotter:
        
    def drawIndividuals(pyqtplotwidget1: PlotWidget, pyqtplotwidget2: PlotWidget, passData: Pass):
        #Setup Plot Prefs
        setConfigOptions(antialias=True, background='k', foreground='w')
        pyqtplotwidget1.clear()
        pyqtplotwidget2.clear()
        #Plot Individual (upper)
        trim_left, trim_right, trim_vertical = StringPlotter.drawIndividual(pyqtplotwidget1, passData)
        #Plot Individual Trimmed (lower)
        StringPlotter.drawIndividualTrim(pyqtplotwidget2, passData)
        #Return trim handles to parent
        return trim_left, trim_right, trim_vertical
        
    def drawIndividual(pyqtplotwidget: PlotWidget, passData: Pass):
        #Setup Plotter
        pyqtplotwidget.setLabel(axis='bottom',text='Location', units=passData.string.data_loc_units)
        pyqtplotwidget.setLabel(axis='left', text = 'Relative Dye Intensity')
        pyqtplotwidget.showGrid(x=True, y=True)
        # Add Legend
        pyqtplotwidget.plotItem.addLegend(offset=(5,5))
        #Check if data exists
        if passData.string.data.empty: return None, None, None
        #Plot data
        d = passData.string.data.copy()
        min = passData.string.findMin(d.copy(), passData.string.trim_l, passData.string.trim_r)
        x = np.array(passData.string.data['loc'].values, dtype=float)
        y = np.array(passData.string.data[passData.name].values, dtype=float)
        pyqtplotwidget.plot(name='Raw', pen='w').setData(x, y)
        #Create L, R and V Trim Handles
        trim_left = InfiniteLine(pos=x[0+passData.string.trim_l], movable=True, pen='y', hoverPen=mkPen('y',width=3), label='Trim L = {value:0.2f}', labelOpts={'color': 'y','position': 0.9})
        trim_right = InfiniteLine(pos=x[-1-passData.string.trim_r], movable=True, pen='y', hoverPen=mkPen('y',width=3), label='Trim R = {value:0.2f}', labelOpts={'color': 'y','position': 0.9})
        trim_vertical = InfiniteLine(pos=(min+passData.string.trim_v), angle=0, movable=True, pen='y', hoverPen=mkPen('y',width=3), label='Floor = {value:0.2f}', labelOpts={'color': 'y','position': 0.5})
        #Add Trim Handles
        pyqtplotwidget.addItem(trim_left)
        pyqtplotwidget.addItem(trim_right)
        pyqtplotwidget.addItem(trim_vertical)
        #Return Trim Handles to parent
        return trim_left, trim_right, trim_vertical
        
    def drawIndividualTrim(pyqtplotwidget: PlotWidget, passData: Pass):
        #Setup Plotter
        pyqtplotwidget.setLabel(axis='bottom',text='Location', units=passData.string.data_loc_units)
        pyqtplotwidget.setLabel(axis='left', text = 'Relative Dye Intensity')
        pyqtplotwidget.showGrid(x=True, y=True)
        # Add Legend
        pyqtplotwidget.plotItem.addLegend(offset=(5,5))
        #Check if data exists
        if passData.string.data.empty: return
        #Plot trimmed/rebased data
        ps = copy.copy(passData.string)
        ps.smooth=False
        ps.modifyData()
        x = np.array(ps.data_mod['loc'].values, dtype=float)
        y = np.array(ps.data_mod[ps.name].values, dtype=float)
        pyqtplotwidget.plot(name='Trimmed', pen='w').setData(x[y!=0], y[y!=0])
        #Plot smooth data on top of raw data
        if passData.string.smooth:
            ps.smooth=True
            ps.modifyData()
            y_smooth = np.array(ps.data_mod[ps.name].values, dtype=float)
            y_smooth[y_smooth==0] = np.nan
            pyqtplotwidget.plot(name='Trimmed, Smoothed', pen=mkPen('y', width=3)).setData(x[y!=0], y_smooth[y!=0])
        

    def drawOverlay(mplWidget, series: SeriesData):
        ax = mplWidget.canvas.ax
        ax.clear()

        ax.set_yticks([])
        ax.set_xlabel(f'Location ({series.info.swath_units})')
        for p in series.passes:
            if p.string.data_mod.empty: continue
            if p.include_in_composite:
                x = np.array(p.string.data_mod['loc'], dtype=float)
                y = np.array(p.string.data_mod[p.name], dtype=float)
                l, = ax.plot(x[y!=0], y[y!=0])
                l.set_label(p.name)
        ax.set_ylim(ymin=0)
        h,l = ax.get_legend_handles_labels()
        if len(h) > 0: ax.legend()
        mplWidget.canvas.fig.set_tight_layout(True)
        mplWidget.canvas.draw()

    def drawAverage(mplWidget, series: SeriesData):
        ax = mplWidget.canvas.ax
        ax.clear()
        # Only plot something if >= 1 passes included
        series_with_data = False
        p: Pass
        for p in series.passes:
           if not p.string.data.empty and p.include_in_composite:
                series_with_data = True
                break
        if series_with_data:
            # Get handles from series object
            sw = series.info.swath_adjusted
            try:
                int(sw)
            except:
                return
            pattern: pd.DataFrame = series.string.average.string.data_mod
            # Find average deposition inside swath width
            pattern_c = pattern[(pattern['loc']>=-sw/2) & (pattern['loc']<=sw/2)]
            avg = pattern_c['Average'].mean(axis='rows')
            # Plot rectangle, w = swath width, h = (1/2)* average dep inside swath width
            m = ax.fill_between([-sw/2,sw/2], 0, avg/2, facecolor='black', alpha=0.25)
            m.set_label('Effective Swath')
            # Plot average data_mod
            x = np.array(pattern['loc'], dtype=float)
            y = np.array(pattern['Average'], dtype=float)
            l, = ax.plot(x[y!=0], y[y!=0], color="black", linewidth=3)
            l.set_label('Average')
            ax.legend()
        # Plot beautification
        ax.set_xlabel(f'Location ({series.info.swath_units})')
        ax.set_yticks([])
        ax.set_ylim(ymin=0)
        mplWidget.canvas.fig.set_tight_layout(True)
        # Plot it
        mplWidget.canvas.draw()

    def drawSimulations(mplWidgetRT: MplWidget, mplWidgetBF: MplWidget, series: SeriesData):
        axes = [mplWidgetRT.canvas.ax, mplWidgetBF.canvas.ax]
        for ax in axes:
            ax.clear()
        # Only plot something if >= 1 passes included
        series_with_data = False
        p: Pass
        for p in series.passes:
           if not p.string.data.empty and p.include_in_composite:
                series_with_data = True
                break
        if series_with_data:
            # Get handles from series object
            sw = series.info.swath_adjusted
            pattern: pd.DataFrame = series.string.average.string.data_mod
            # Create an inverted copy pattern for B & F odd passes
            pattern_i: pd.DataFrame = pattern.copy()
            pattern_i['Average'] = pattern_i['Average'].values[::-1]
            # Find average deposition inside swath width
            pattern_c = pattern[(pattern['loc']>=-sw/2) & (pattern['loc']<=sw/2)]
            avg = pattern_c['Average'].mean(axis='rows')
            # Points inside 1 swath width for shifting
            pts = len(pattern_c.index)
            for ax in axes:
                # Plot the central pass
                #print(pattern)
                ax.fill_between(pattern['loc'], 0, pattern['Average'], label='Center')
                # Sum counter to always draw on top of
                sum: pd.DataFrame = pattern['Average'].copy()
                # Plot adjascent passes
                for i in range(int(series.string.simulated_adjascent_passes)):
                    p = pattern
                    # When B & F and odd pass, use inverted average
                    if (ax == mplWidgetBF.canvas.ax) & ((i%2)==0):
                        p = pattern_i
                    # Draw ith left pass, add to sum
                    left = p['Average'].copy().shift(periods=-(i+1)*pts)
                    ax.fill_between(p['loc'], sum, sum.add(left, fill_value=0), label=f'Left-{i+1}')
                    sum = sum.add(left, fill_value=0)
                    # Draw ith right pass, add to sum
                    right = p['Average'].copy().shift(periods=(i+1)*pts)
                    ax.fill_between(p['loc'], sum, sum.add(right, fill_value=0), label=f'Right-{i+1}')
                    sum = sum.add(right, fill_value=0)
                # Draw black line overlay on total
                ax.plot(pattern['loc'], sum, color='black')
                # Only plot within central swath width
                ax.set_xlim(-sw/2,sw/2)
                ax.set_ylim(ymin=0)
                # Draw Average Line for CV reference
                avg = sum.mean()
                m, = ax.plot([-sw/2,sw/2], [avg,avg], color='black', dashes=[5,5])
                m.set_label('Mean Dep.')
                # Plot Beautification
                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
                ax.set_yticks([])
                ax.set_xlabel(f'Location ({series.info.swath_units})')
                if(ax == mplWidgetRT.canvas.ax):
                    ax.set_ylabel('Racetrack')
                else:
                    ax.set_ylabel('Back & Forth')
        #Actually draw on the canvas
        mplWidgetRT.canvas.fig.set_tight_layout(True)
        mplWidgetRT.canvas.draw()
        mplWidgetBF.canvas.fig.set_tight_layout(True)
        mplWidgetBF.canvas.draw()

    def showCVTable(tableView: QTableWidget, series: SeriesData):
        # Only show values if >= 1 passes included
        series_with_data = False
        p: Pass
        for p in series.passes:
           if not p.string.data.empty and p.include_in_composite:
                series_with_data = True
                break
        sw = series.info.swath_adjusted
        swath_units = series.info.swath_units
        tv = tableView
        # Simulate various Swath Widths, incrimenting by 2 units (-/+) from the center
        for row in range(tv.rowCount()):
            item_sw = tv.item(row, 0)
            item_rt = tv.item(row, 1)
            item_bf = tv.item(row, 2)
            if not series_with_data:
                item_sw.setText('-')
                item_rt.setText('-')
                item_bf.setText('-')
                continue
            # Print swath width
            _sw = sw - (tv.rowCount()-1) + (2*row)
            item_sw.setText(f"{_sw} {swath_units}")
            # Calc and Print RT CV
            rt_cv = StringPlotter.calcCV(series, series.string.simulated_adjascent_passes, _sw, False)
            item_rt.setText(f"{rt_cv} %")
            # Calc and Print BF CV
            bf_cv = StringPlotter.calcCV(series, series.string.simulated_adjascent_passes, _sw, True)
            item_bf.setText(f"{bf_cv} %")

    def calcCV(series: SeriesData, numAdjascentPassesPerSide: int, swathWidth: float, isBackAndForth: bool):
        # Get handles from series object
        pattern: pd.DataFrame = series.string.average.string.data_mod
        # Create an inverted copy pattern for B & F odd passes
        if isBackAndForth:
            pattern_i: pd.DataFrame = pattern.copy()
            pattern_i['Average'] = pattern_i['Average'].values[::-1]
        # Find average deposition inside swath width
        pattern_c = pattern[(pattern['loc']>=-swathWidth/2) & (pattern['loc']<=swathWidth/2)]
        # Points inside 1 swath width for shifting
        pts = len(pattern_c.index)
        # Sum counter to always draw on top of, starting with initial central pass
        sum = pattern['Average'].copy()
        for i in range(numAdjascentPassesPerSide):
            p = pattern
            # When B & F and odd pass, use inverted average
            if isBackAndForth and i%2==0:
                p = pattern_i
            # Add ith Left pass contribution to sum
            left = p['Average'].copy().shift(periods=-(i+1)*pts)
            sum = sum.add(left, fill_value=0)
            # Add ith Right pass contribution to sum
            right = p['Average'].copy().shift(periods=(i+1)*pts)
            sum = sum.add(right, fill_value=0)
        # Create subset of summed vals inside swath width
        sumCenter = sum[sum.index.isin(pattern_c.index)]
        # Calculate and return the CV as an integer percentage
        return round(variation(sumCenter, axis=0) * 100)
