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
    
    def plotDistribution(mplWidget1: MplWidget, mplWidget2: MplWidget, tableWidget: QTableWidget, sprayCard: SprayCard, passData: Pass = None, seriesData: SeriesData = None):
        # Create Composite if applicable
        composite: SprayCardComposite = CardPlotter.createRepresentativeComposite(sprayCard, passData, seriesData)
        # Create sorting bins
        bins = [x for x in range(0, 900, 50)]
        binned_cov = [0 for b in bins]
        binned_quant = [0 for b in bins]
        # Abort if no stains   
        if len(composite.stain_areas_valid_px2) > 0:
            # Convenience accessors
            area_list = composite.drop_vol_um3
            sum_area = sum(area_list)
            dia_list = composite.drop_dia_um
            # Get an array of bins each drop dia belongs in (1-based)
            binned_dia = np.digitize(dia_list, bins)
            # Sort values into bins 
            for area, bin in zip(area_list, binned_dia):
                binned_cov[bin-1] += area / sum_area
                binned_quant[bin-1] += 1
        CardPlotter._plotDistCov(mplWidget1, bins, binned_cov)
        CardPlotter._plotDistQuant(mplWidget2, bins, binned_quant)
        CardPlotter._plotDistStatTable(tableWidget,composite)
            
    
    def _plotDistCov(mplWidget: MplWidget, bins, binned_cov):
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xlabel('Droplet Diameter (microns')
        ax.set_xticks(bins)
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
        ax.set_ylabel('Spray Vol. Contrib.')
        # Populate data
        ax.hist(bins, bins, weights=binned_cov, rwidth=0.8)
        for label in ax.get_xticklabels(which='major'):
            label.set(rotation=30, horizontalalignment='right')
        # Plot
        mplWidget.canvas.fig.set_tight_layout(True)
        mplWidget.canvas.draw()
        
    def _plotDistQuant(mplWidget: MplWidget, bins, binned_quant):
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xticks(bins)
        ax.set_xlabel('Droplet Diameter (microns')
        ax.set_ylabel('Quantity')
        # Populate Data
        ax.hist(bins, bins, weights=binned_quant, rwidth=0.8)
        for label in ax.get_xticklabels(which='major'):
            label.set(rotation=30, horizontalalignment='right')
        # Plot
        mplWidget.canvas.fig.set_tight_layout(True)
        mplWidget.canvas.draw()
        
    def _plotDistStatTable(tableWidget: QTableWidget, composite: SprayCardComposite):
        # clear tv
        for row in range(tableWidget.rowCount()):
            tableWidget.item(row, 1).setText('-')
        # If no drops, return
        if len(composite.stain_areas_valid_px2) < 1:
            return
        # Calc values from composite
        dv01, dv05, dv09, rs, dsc = composite.volumetric_stats(composite.drop_dia_um.sort(), composite.drop_vol_um3.sort())
        cov = composite.percent_coverage()
        stains = len(composite.stain_areas_valid_px2)
        area = composite.area_in2
        spsi = round(stains / area)
        # Put vals in table
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
        
    def plotSpatial(mplWidget1: MplWidget, mplWidget2: MplWidget, sprayCards: List[SprayCard], loc_units, colorize = False):
        # Units for plot
        
        # Init vals as none
        locs, cov, dv01, dv05, dv09 = [None] * 5
        # Get a ist of valid cards with locations
        card: SprayCard
        scs = [card for card in sprayCards if card.has_image and card.include_in_composite and card.location is not None and card.location_units is not None]
        #Process each card for stats
        for card in scs:
            card.images_processed()
        # Remove cards with no stains
        scs = [card for card in scs if len(card.stain_areas_valid_px2)>0]
        # Populate arrays if cards available
        if len(scs) > 0:
           # Sort by location
            scs.sort(key=lambda x: x.location)
            # Calculate all card stats only once for speed
            stats = [card.volumetric_stats() for card in scs]
            # Create plottable series
            locs = [card.location for card in scs]
            units = [card.location_units for card in scs]
            # Modify loc units as necessary
            for i, (loc, unit) in enumerate(zip(locs, units)):
                if unit != loc_units:
                    if unit == cfg.UNIT_FT:
                        locs[i] = loc / cfg.FT_PER_M
                    else:
                        locs[i] = loc * cfg.FT_PER_M
            cov = [card.percent_coverage() for card in scs]
            dv01 = [stat[0] for stat in stats]
            dv05 = [stat[1] for stat in stats]
            dv09 = [stat[2] for stat in stats]
        # Plot
        CardPlotter._plotSpatialDV(mplWidget1, x=locs, y_01=dv01, y_05=dv05, y_09=dv09, x_units=loc_units)
        CardPlotter._plotSpatialCov(mplWidget2, x=locs, y_cov=cov, y_01=dv01, y_05=dv05, x_units=loc_units, fill_dsc=colorize)
        
    def _plotSpatialDV(mplWidget: MplWidget, x, y_01, y_05, y_09, x_units):
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xlabel(f'Location ({x_units})')
        ax.set_ylabel('Droplet Size (microns)')
        # Populate data if available
        if x is not None:
            ax.plot(x,y_09, label='Dv0.9')
            ax.plot(x,y_05, label='VMD')
            ax.plot(x,y_01, label='Dv0.1')
            # Legend
            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        # Draw the plots
        mplWidget.canvas.fig.set_tight_layout(True)
        mplWidget.canvas.draw()
        
    def _plotSpatialCov(mplWidget: MplWidget, x, y_cov, y_01, y_05, x_units, fill_dsc):
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xlabel(f'Location ({x_units})')
        ax.set_ylabel('Coverage')
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=100, decimals=0))
        # Populate data if available
        if x is not None:
            # Interpolate so that fill-between looks good
            locs_i = np.linspace(x[0],x[-1],num=1000)
            cov_i = np.interp(locs_i, x, y_cov)
            #Colorize
            if fill_dsc:
                # Get a np array of dsc's calculated for each interpolated loc
                dv01_i = np.interp(locs_i, x, y_01)
                dv05_i = np.interp(locs_i, x, y_05)
                dsc_i = np.array([AtomizationModel().dsc(dv01=dv01, dv05=dv05) for (dv01,dv05) in zip(dv01_i,dv05_i)])
                # Plot the fill data using dsc-specified colors
                categories = ['VF','F','M','C','VC','XC','UC']
                colors = ['red','orange','yellow','blue','green','lightgray','black']
                for (category, color) in zip(categories,colors):
                    ax.fill_between(locs_i, np.ma.masked_where(dsc_i != category, cov_i), color=color, label=category)
                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            # Plot base coverage without dsc fill
            ax.plot(locs_i,cov_i,color='black')
        # Draw the plots
        mplWidget.canvas.fig.set_tight_layout(True)
        mplWidget.canvas.draw()