import math
from PyQt5.QtWidgets import QTableWidget
import numpy as np
import matplotlib.ticker

from accupatt.models.sprayCard import SprayCard

class CardPlotter:
    
    def plotDropletDistribution(mplWidget1, mplWidget2, sprayCard: SprayCard):
        
        bins = [x for x in range(0, 900, 50)]
        binned_cov = [0 for b in bins]
        binned_quant = [0 for b in bins]
        drop_dia_um = []
        cum_area = 0
        # Calculate Drop Diameters
        for area in sprayCard.stain_areas_valid_px2:
            cum_area += area
            # Convert px2 to um2
            area_um2 = sprayCard._px2_to_um2(area)
            # Calculate stain diameter assuming circular stain
            dia_um = math.sqrt((4.0 * area_um2) / math.pi)
            # Apply Spread Factors to get originating drop diameter
            drop_dia_um.append(sprayCard._stain_dia_to_drop_dia(dia_um))
        # Get an array of bins each drop dia belongs in (1-based)
        binned_dias = np.digitize(drop_dia_um, bins)
        # Get normalized values to put in each bin which will be plotted
        for area, bin in zip(sprayCard.stain_areas_valid_px2, binned_dias):
            binned_cov[bin-1] += area/cum_area
            binned_quant[bin-1] += 1/len(drop_dia_um)
        
        canvass = [mplWidget1.canvas, mplWidget2.canvas]
        for i, canvas in enumerate(canvass):
            ax = canvas.ax
            ax.clear()
            ax.set_xticks(bins)
            ax.set_xlabel('Droplet Diameter (microns)')
            ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
            if i == 0:
                weights = binned_cov
                ax.set_ylabel('Norm. Coverage')
            else:
                weights = binned_quant
                ax.set_ylabel('Norm. Quantity')
            ax.hist(bins, bins, weights=weights, rwidth=0.8)
            for label in ax.get_xticklabels(which='major'):
                label.set(rotation=30, horizontalalignment='right')
            canvas.fig.set_tight_layout(True)
            canvas.draw()
        
    def showCardStatTable(tableWidget: QTableWidget, sprayCard: SprayCard):
        if sprayCard == None or not sprayCard.has_image:
            # clear tv
            for row in range(tableWidget.rowCount()):
                tableWidget.item(row, 1).setText('')
            return
        dv01, dv05, dv09, rs, dsc = sprayCard.volumetric_stats()
        cov = sprayCard.percent_coverage()
        spsi = sprayCard.stains_per_in2()
        for row, val in zip([0,1,2,3,4,5,6],[dsc,dv01,dv05,dv09,rs,cov,spsi]):
            if type(val) is not str:
                if type(val) is int:
                    val = str(val) + ' \u03BC' + 'm'
                else:
                    val = f'{val:.2f}'
            if row == 5:
                val = val + '%'
            tableWidget.item(row,1).setText(val)
        tableWidget.resizeColumnsToContents()