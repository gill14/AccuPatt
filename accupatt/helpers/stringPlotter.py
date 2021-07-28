import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as sig
from scipy.stats import variation

class StringPlotter:

    def drawIndividual(mplCanvas, pattern):
        d = pattern.data
        dm = pattern.data_mod

        ax = mplCanvas.ax
        ax.clear()
        #ax.plot(d['loc'],d[pattern.name])
        ax.plot(dm['loc'],dm[pattern.name])

        mplCanvas.draw()

    def drawIndividualTrims(mplCanvas1, mplCanvas2, pattern):
        d = pattern.data.copy()
        #find what will be min after L/R trim
        dd = d.copy()
        #Trim Left
        dd.loc[:pattern.trim_l-1,[pattern.name]] = -1
        #Trim Right
        dd.loc[(dd[pattern.name].size-pattern.trim_r):,[pattern.name]] = -1
        #Find new min inside untrimmed area
        min = dd[dd>-1].loc[:,[pattern.name]].min(skipna=True)
        #Remove min from pattern to accurately show how trim_v will be applied later
        d[pattern.name] = d.loc[:,[pattern.name]].sub(min, axis=1)
        d[pattern.name] = d[[pattern.name]].clip(lower=0)

        ax1 = mplCanvas1.ax
        ax1.clear()
        ax1.plot(d['loc'],d[pattern.name])

        xL = pd.to_numeric(d.iloc[:pattern.trim_l,0])
        xR = pd.to_numeric(d.iloc[d[pattern.name].size-pattern.trim_r:,0])
        xC = pd.to_numeric(d.iloc[pattern.trim_l:d[pattern.name].size-pattern.trim_r,0])
        y1 = d[pattern.name].min()
        y2 = d[pattern.name].max()

        #Trims
        if len(xL) > 0:
            print('left fill')
            print(xL)
            ax1.fill_between(xL, y1, y2, facecolor='black', alpha=0.4)
        if len(xR) > 0:
            print('right fill')
            print(xR)
            ax1.fill_between(xR, y1, y2, facecolor='black', alpha=0.4)
        if pattern.trim_v > 0:
            ax1.fill_between(xC, y1, pattern.trim_v, facecolor='black', alpha=0.4)
        ax1.set_ylabel('Pre-Trim')
        mplCanvas1.fig.set_tight_layout(True)
        mplCanvas1.draw()

        ax2 = mplCanvas2.ax
        ax2.clear()
        ax2.plot(pattern.data_mod['loc'], pattern.data_mod[pattern.name])
        ax2.set_ylabel('Post-Trim')
        mplCanvas2.fig.set_tight_layout(True)
        mplCanvas2.draw()

    def drawOverlay(mplCanvas, series):
        ax = mplCanvas.ax
        ax.clear()

        ax.set_yticks([])
        ax.set_xlabel(f'Location ({series.info.swath_units})')
        for key in series.passes.keys():
            p = series.passes[key]
            if p.include_in_composite:
                l, = ax.plot(p.data_mod['loc'], p.data_mod[key])
                l.set_label(p.name)
        ax.set_ylim(ymin=0)
        ax.legend()
        mplCanvas.fig.set_tight_layout(True)
        mplCanvas.draw()

    def drawAverage(mplCanvas, series):
        ax = mplCanvas.ax
        ax.clear()
        ax.set_yticks([])
        ax.set_xlabel(f'Location ({series.info.swath_units})')

        l, = ax.plot(series.patternAverage.data_mod['loc'], series.patternAverage.data_mod['Average'], color="black", linewidth=3)
        l.set_label('Average')
        ax.set_ylim(ymin=0)
        ax.legend()
        mplCanvas.fig.set_tight_layout(True)
        mplCanvas.draw()

    def drawSimulations(mplCanvasRacetrack, mplCanvasBackAndForth, series, numAdjascentPassesPerSide):
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
            for i in range(numAdjascentPassesPerSide):
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

    def showCVTable(tableView, series, numAdjascentPassesPerSide):
        swath = series.info.swath_adjusted
        swath_units = series.info.swath_units
        tv = tableView
        for row in range(tv.rowCount()):
            #Print swath
            sw = swath - (tv.rowCount()-1) + (2*row)
            tv.item(row, 0).setText(f"{sw} {swath_units}")
            #Print RT CV
            rt_cv = StringPlotter.calcCV(series, numAdjascentPassesPerSide, sw, False)
            tv.item(row, 1).setText(f"{rt_cv} %")
            #Print BF CV
            bf_cv = StringPlotter.calcCV(series, numAdjascentPassesPerSide, sw, True)
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
