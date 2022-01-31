from typing import List

import accupatt.config as cfg
import matplotlib.ticker
import numpy as np
from accupatt.helpers.atomizationModel import AtomizationModel
from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.models.sprayCard import SprayCard
from accupatt.widgets.mplwidget import MplWidget
from PyQt6.QtWidgets import QTableWidget


class SprayCardComposite(SprayCard):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drop_dia_um = []
        self.drop_vol_um3 = []
        self.area_in2 = 0.0
    
class CardPlotter:
    
    def createRepresentativeComposite(sprayCard: SprayCard = None, passData: Pass = None, seriesData: SeriesData = None) -> SprayCardComposite:
        cards = []
        composite = SprayCardComposite()
        # If seriesData is passed in, compute series-wise dist
        if seriesData is not None:
            for p in seriesData.passes:
                for c in p.spray_cards:
                    cards.append(c)
        # If passData is passed in, compute pass-wise dist
        elif passData is not None:
            for c in passData.spray_cards:
                cards.append(c)
        elif sprayCard is not None:
            cards.append(sprayCard)
        # If either pass-wise or series-wise, re-compute all cards and create composite
        for card in cards:
            if card.has_image and card.include_in_composite:
                # Do the image processing
                card.images_processed()
                # Glob into representative composite card
                composite.area_px2 += card.area_px2
                composite.area_in2 += card._px2_to_in2(card.area_px2)
                dd, dv = card.build_droplet_data()
                composite.drop_dia_um.extend(dd)
                composite.drop_vol_um3.extend(dv)
                composite.stain_areas_all_px2.extend(card.stain_areas_all_px2)
                composite.stain_areas_valid_px2.extend(card.stain_areas_valid_px2)
                
        return composite
    
    def clearDropletDistributionPlots(mplWidget1, mplWidget2):
        canvass = [mplWidget1.canvas, mplWidget2.canvas]
        for canvas in canvass:
            ax = canvas.ax
            ax.clear()
            canvas.fig.set_tight_layout(True)
            canvas.draw()
    
    def plotDropletDistribution(mplWidget1, mplWidget2, sprayCard: SprayCardComposite):
        # Clear Plots
        CardPlotter.clearDropletDistributionPlots(mplWidget1, mplWidget2) 
        # Abort if no stains   
        if len(sprayCard.stain_areas_valid_px2) <= 0:
            return
        # Create sorting bins
        bins = [x for x in range(0, 900, 50)]
        binned_cov = [0 for b in bins]
        binned_quant = [0 for b in bins]
        # Convenience accessors
        area_list = sprayCard.drop_vol_um3
        sum_area = sum(area_list)
        dia_list = sprayCard.drop_dia_um
        # Get an array of bins each drop dia belongs in (1-based)
        binned_dia = np.digitize(dia_list, bins)
        # Sort values into bins 
        for area, bin in zip(area_list, binned_dia):
            binned_cov[bin-1] += area / sum_area
            binned_quant[bin-1] += 1
        # Coverage Plot
        ax = mplWidget1.canvas.ax
        ax.set_xticks(bins)
        ax.set_xlabel('Droplet Diameter (microns')
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
        ax.set_ylabel('Spray Vol. Contrib.')
        ax.hist(bins, bins, weights=binned_cov, rwidth=0.8)
        for label in ax.get_xticklabels(which='major'):
            label.set(rotation=30, horizontalalignment='right')
        mplWidget1.canvas.fig.set_tight_layout(True)
        mplWidget1.canvas.draw()
        # Quantity Plot
        ax = mplWidget2.canvas.ax
        ax.set_xticks(bins)
        ax.set_xlabel('Droplet Diameter (microns')
        ax.set_ylabel('Quantity')
        ax.hist(bins, bins, weights=binned_quant, rwidth=0.8)
        for label in ax.get_xticklabels(which='major'):
            label.set(rotation=30, horizontalalignment='right')
        mplWidget2.canvas.fig.set_tight_layout(True)
        mplWidget2.canvas.draw()
    
    def clearCardStatTable(tableWidget: QTableWidget):
        # clear tv
        for row in range(tableWidget.rowCount()):
            tableWidget.item(row, 1).setText('-')
        
    def showCardStatTable(tableWidget: QTableWidget, composite: SprayCardComposite):
        if len(composite.stain_areas_valid_px2) < 1:
            # clear tv
            CardPlotter.clearCardStatTable(tableWidget)
            return
        dv01, dv05, dv09, rs, dsc = composite.volumetric_stats(composite.drop_dia_um.sort(), composite.drop_vol_um3.sort())
        cov = composite.percent_coverage()
        stains = len(composite.stain_areas_valid_px2)
        area = composite.area_in2
        spsi = round(stains / area)
        
        for row, val in zip([0,1,2,3,4,5,6,7,8],[dsc,dv01,dv05,dv09,rs,cov,area,stains,spsi]):
            if row >= 1 and row <= 3:
                val = str(val) + ' \u03BC' + 'm'
            elif row == 4:
                val = f'{val:.2f}'
            elif row == 5:
                val = f'{val:.2f}%'
            elif row == 6:
                val = f'{val:.2f} in2'
            elif row >= 7 and row <= 8:
                val = str(val)
            tableWidget.item(row,1).setText(val)
        tableWidget.resizeColumnsToContents()
        
    def plotSpatial(mplWidget1: MplWidget, mplWidget2: MplWidget, sprayCards: List[SprayCard], colorize = False):
        # Units for plot - TODO 
        units = cfg.UNIT_FT
        # Setup Axes
        ax1 = mplWidget1.canvas.ax
        ax1.clear()
        ax1.set_xlabel(f'Location ({units})')
        ax1.set_ylabel('Droplet Size (microns)')
        ax2 = mplWidget2.canvas.ax
        ax2.clear()
        ax2.set_xlabel(f'Location ({units})')
        ax2.set_ylabel('Coverage')
        #ax2.set_ylim(ymin=0)
        ax2.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=100, decimals=0))
        # Get a sorted list of valid cards with locations
        card: SprayCard
        scs = [card for card in sprayCards if card.has_image and card.include_in_composite and card.location is not None]
        #Process each card for stats
        for card in scs:
            card.images_processed()
        # Remove cards with no stains
        scs = [card for card in scs if len(card.stain_areas_valid_px2)>0]
        if len(scs) > 0:
           # Sort by location
            scs.sort(key=lambda x: x.location)
            # Calculate all card stats only once for speed
            stats = [card.volumetric_stats() for card in scs]
            # Create plottable series
            locs = [card.location for card in scs]
            cov = [card.percent_coverage() for card in scs]
            dv01 = [stat[0] for stat in stats]
            dv05 = [stat[1] for stat in stats]
            dv09 = [stat[2] for stat in stats]
            # Plot DSC by location
            ax1.plot(locs,dv09, label='Dv0.9')
            ax1.plot(locs,dv05, label='VMD')
            ax1.plot(locs,dv01, label='Dv0.1')
            ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            # Interpolate so that fill-between looks good
            locs_i = np.linspace(locs[0],locs[-1],num=1000)
            cov_i = np.interp(locs_i, locs, cov)
            #Colorize
            if colorize:
                # Get a np array of dsc's calculated for each interpolated loc
                dv01_i = np.interp(locs_i, locs, dv01)
                dv05_i = np.interp(locs_i, locs, dv05)
                dsc_i = np.array([AtomizationModel().dsc(dv01=dv01, dv05=dv05) for (dv01,dv05) in zip(dv01_i,dv05_i)])
                # Plot the fill data using dsc-specified colors
                categories = ['VF','F','M','C','VC','XC','UC']
                colors = ['red','orange','yellow','blue','green','lightgray','black']
                for (category, color) in zip(categories,colors):
                    ax2.fill_between(locs_i, np.ma.masked_where(dsc_i != category, cov_i), color=color, label=category)
                ax2.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            # Plot base coverage
            ax2.plot(locs_i,cov_i,color='black')
        # Draw the plots
        mplWidget1.canvas.fig.set_tight_layout(True)
        mplWidget1.canvas.draw()
        mplWidget2.canvas.fig.set_tight_layout(True)
        mplWidget2.canvas.draw()
        