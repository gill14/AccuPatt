import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pyqtgraph
from pyqtgraph.functions import mkPen
import scipy.signal as sig
from scipy.stats import variation

class StringPlotter:
        
    def drawIndividuals(pyqtplotwidget1, pyqtplotwidget2, passData):
        trim_left, trim_right, trim_vertical = StringPlotter.drawIndividual(pyqtplotwidget1, passData)
        StringPlotter.drawIndividualTrim(pyqtplotwidget2, passData)
        return trim_left, trim_right, trim_vertical
        
    def drawIndividual(pyqtplotwidget, passData):
        d = passData.data
        _,min = passData.trimLR(d.copy())
        
        pyqtgraph.setConfigOptions(antialias=True)
        pyqtgraph.setConfigOption('background', 'k')
        pyqtgraph.setConfigOption('foreground', 'w')
        w = pyqtplotwidget
        w.setWindowTitle(f'{passData.name} Raw Data')
        w.clear()
        p = w.addPlot(labels =  {'left':'Relative Dye Intensity', 'bottom':'Location'})
        p.showGrid(x=True, y=True)
        x = np.array(passData.data['loc'].values, dtype=float)
        y = np.array(passData.data[passData.name].values, dtype=float)
        
        p.plot(name='Raw', pen='w').setData(x, y)
       
        #Trim Handles
        trim_left = pyqtgraph.InfiniteLine(pos=x[0+passData.trim_l], movable=True, pen='y', hoverPen=mkPen('y',width=3), label='Trim L = {value:0.2f}', labelOpts={'color': 'y','position': 0.9})
        trim_right = pyqtgraph.InfiniteLine(pos=x[-1-passData.trim_r], movable=True, pen='y', hoverPen=mkPen('y',width=3), label='Trim R = {value:0.2f}', labelOpts={'color': 'y','position': 0.9})
        #Find new min inside untrimmed area
        #min = d.loc[d.index[0+passData.trim_l:-1-passData.trim_r],passData.name].min(skipna=True)
        trim_vertical = pyqtgraph.InfiniteLine(pos=(min+passData.trim_v), angle=0, movable=True, pen='y', hoverPen=mkPen('y',width=3), label='Floor = {value:0.2f}', labelOpts={'color': 'y','position': 0.5})
        #trim_left.addMarker('<|>', position=0.2)
        p.addItem(trim_left)
        p.addItem(trim_right)
        p.addItem(trim_vertical)
        
        return trim_left, trim_right, trim_vertical
        
    def drawIndividualTrim(pyqtplotwidget, passData):
        if not isinstance(passData.data, pd.DataFrame): return
        d,_ = passData.trimLR(passData.data.copy())
        d = passData.trimV(d)
        w = pyqtplotwidget
        w.clear()
        w.setWindowTitle(f'{passData.name} Raw Data')
        p = w.addPlot(labels =  {'left':'Relative Dye Intensity', 'bottom':'Location'})
        p.showGrid(x=True, y=True)
        x = np.array(d['loc'].values, dtype=float)
        y = np.array(d[passData.name].values, dtype=float)
        passData.modifyData(isCenter=False, isSmooth=True)
        y_smooth = np.array(passData.data_mod[passData.name].values, dtype=float)
        p.plot(name='Emission', pen='w').setData(x, y)
        p.plot(name='Smooth', pen=mkPen('y', width=3)).setData(x, y_smooth)

    def drawOverlay(mplCanvas, series):
        ax = mplCanvas.ax
        ax.clear()

        ax.set_yticks([])
        ax.set_xlabel(f'Location ({series.info.swath_units})')
        for key in series.passes.keys():
            p = series.passes[key]
            if not isinstance(p.data, pd.DataFrame): continue
            if p.include_in_composite:
                l, = ax.plot(p.data_mod['loc'], p.data_mod[key])
                l.set_label(p.name)
        ax.set_ylim(ymin=0)
        h,l = ax.get_legend_handles_labels()
        if len(h) > 0: ax.legend()
        mplCanvas.fig.set_tight_layout(True)
        mplCanvas.draw()

    def drawAverage(mplCanvas, series):
        ax = mplCanvas.ax
        ax.clear()
        ax.set_yticks([])
        ax.set_xlabel(f'Location ({series.info.swath_units})')

        #Get adjusted swath from series object
        swathWidth = series.info.swath_adjusted
        #Find number of points per swathwidth for shifting
        loc = series.patternAverage.data_mod['loc'].copy()
        center = loc[(loc>=-swathWidth/2) & (loc<=swathWidth/2)]
        pts = center.count().item()
        loc = pd.to_numeric(series.patternAverage.data_mod['loc'].copy())
        sumCenter = series.patternAverage.data_mod['Average'][series.patternAverage.data_mod['Average'].index.isin(center.index)]
        avg = sumCenter.mean(axis='rows')
        #m, = ax.plot([-swathWidth/2,swathWidth/2], [avg,avg], color='black', dashes=[5,5])
        m = ax.fill_between([-swathWidth/2,swathWidth/2], 0, avg/2, facecolor='black', alpha=0.25)
        m.set_label('Effective Swath')

        l, = ax.plot(series.patternAverage.data_mod['loc'], series.patternAverage.data_mod['Average'], color="black", linewidth=3)
        l.set_label('Average')
        ax.set_ylim(ymin=0)
        ax.legend()
        mplCanvas.fig.set_tight_layout(True)
        mplCanvas.draw()

    def drawSimulations(mplCanvasRacetrack, mplCanvasBackAndForth, series):
        #Get adjusted swath from series object
        swathWidth = series.info.swath_adjusted
        #Find number of points per swathwidth for shifting
        loc = series.patternAverage.data_mod['loc'].copy()
        center = loc[(loc>=-swathWidth/2) & (loc<=swathWidth/2)]
        pts = center.count().item()
        loc = pd.to_numeric(series.patternAverage.data_mod['loc'].copy())
        #Quick identifiers for readability
        a = series.patternAverage.data_mod['Average'].copy()
        ai = series.patternAverageInverted.data_mod['AverageInverted'].copy()

        axes = [mplCanvasRacetrack.ax, mplCanvasBackAndForth.ax]
        for ax in axes:
            #Clear it
            ax.clear()
            ax.set_yticks([])
            ax.set_xlabel(f'Location ({series.info.swath_units})')
            if(ax == mplCanvasRacetrack.ax):
                ax.set_ylabel('Racetrack')
            else:
                ax.set_ylabel('Back & Forth')
            #Plot the central pass
            f = ax.fill_between(loc, 0, a, label='Center')

            sum = a.copy()
            for i in range(series.string_simulated_adjascent_passes):
                aa = a.copy()
                #When B&F and odd pass, use inverted average
                if (ax == mplCanvasBackAndForth.ax) & ((i%2)==0):
                    aa = ai.copy()
                #Left
                left = aa.copy().shift(periods=-(i+1)*pts)
                ax.fill_between(loc, sum, sum.add(left, fill_value=0), label=f'Left-{i+1}')
                sum = sum.add(left, fill_value=0)
                #Right
                right = aa.copy().shift(periods=(i+1)*pts)
                ax.fill_between(loc, sum, sum.add(right, fill_value=0), label=f'Right-{i+1}')
                sum = sum.add(right, fill_value=0)
            #Set black overlay on total
            ax.plot(loc, sum, color='black')
            ax.set_xlim(-swathWidth/2,swathWidth/2)
            ax.set_ylim(ymin=0)
            #Set Average Line for CV reference
            sumCenter = sum[sum.index.isin(center.index)]
            avg = sumCenter.mean(axis='rows')
            m, = ax.plot([-swathWidth/2,swathWidth/2], [avg,avg], color='black', dashes=[5,5])
            m.set_label('Mean Dep.')
            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        #Actually draw on the canvas
        mplCanvasRacetrack.fig.set_tight_layout(True)
        mplCanvasRacetrack.draw()
        mplCanvasBackAndForth.fig.set_tight_layout(True)
        mplCanvasBackAndForth.draw()

    def showCVTable(tableView, series):
        swath = series.info.swath_adjusted
        swath_units = series.info.swath_units
        tv = tableView
        for row in range(tv.rowCount()):
            #Print swath
            sw = swath - (tv.rowCount()-1) + (2*row)
            tv.item(row, 0).setText(f"{sw} {swath_units}")
            #Print RT CV
            rt_cv = StringPlotter.calcCV(series, series.string_simulated_adjascent_passes, sw, False)
            tv.item(row, 1).setText(f"{rt_cv} %")
            #Print BF CV
            bf_cv = StringPlotter.calcCV(series, series.string_simulated_adjascent_passes, sw, True)
            tv.item(row, 2).setText(f"{bf_cv} %")

    def calcCV(series, numAdjascentPassesPerSide, swathWidth, isBackAndForth):
        #Find number of points per swathwidth for shifting
        loc = series.patternAverage.data_mod['loc'].copy()
        center = loc[(loc>=-swathWidth/2) & (loc<=swathWidth/2)]
        pts = center.count().item()
        #loc = pd.to_numeric(series.patternAverage.data_mod['loc'].copy())
        #Quick identifiers for readability
        a = series.patternAverage.data_mod['Average'].copy()
        ai = series.patternAverageInverted.data_mod['AverageInverted'].copy()

        sum = a.copy()
        for i in range(numAdjascentPassesPerSide):
            aa = a.copy()
            #When B&F and odd pass, use inverted average
            if (isBackAndForth) & ((i%2)==0):
                aa = ai.copy()
            #Left
            left = aa.copy().shift(periods=-(i+1)*pts)
            sum = sum.add(left, fill_value=0)
            #Right
            right = aa.copy().shift(periods=(i+1)*pts)
            sum = sum.add(right, fill_value=0)
        #Calc it
        sumCenter = sum[sum.index.isin(center.index)]
        return round(variation(sumCenter, axis=0) * 100)
