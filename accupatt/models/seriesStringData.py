import numpy as np
import pandas as pd
import accupatt.config as cfg
from accupatt.models.passData import Pass

class SeriesStringData:
    
    def __init__(self, passes: list[Pass], swath_units: str):
        # Live feeds from Series Object
        self.passes = passes
        self.swath_units = swath_units
        # Options
        self.smooth = True
        self.smooth_window = cfg.get_string_smooth_window()
        self.smooth_order = cfg.get_string_smooth_order()
        self.equalize_integrals = True
        self.center = True
        self.center_method = cfg.get_center_method()
        self.simulated_adjascent_passes = 2
        # Convenience Runtime Placeholder
        self.average = Pass(name='Average')
        
    def modifyPatterns(self):
        active_passes = [p for p in self.passes if p.include_in_composite and not p.string.data.empty]
        print(f'MODIFYING SERIES -- ACTIVE PASSES = {active_passes}')
        if len(active_passes)==0:
            return
        # Apply individual pattern modifications
        for p in active_passes:
            p.string.modifyData(loc_units=self.swath_units)
        # Apply cross-pattern modifications
        self._equalizePatterns(self.equalize_integrals, active_passes)
        # Assign series string options to average Pass
        self.average.string.smooth = self.smooth
        self.average.string.center = self.center
        self.average.string.center_method = self.center_method
        # Generate and assign data to average Pass
        self.average.string.data = self._averagePattern(active_passes)
        self.average.string.smooth_window = self.smooth_window
        self.average.string.smooth_order = self.smooth_order
        #Apply avearge pattern modifications
        self.average.string.modifyData()

    def _equalizePatterns(self, isEqualize: bool, passes: list[Pass]):
        if not isEqualize:
            return
        #Integrate each pattern to find area under the curve
        areas = [np.trapz(y=p.string.data_mod[p.name], x=p.string.data_mod['loc'], axis=0) for p in passes]
        #Find the pass with the largest integral
        area_max = max(areas)
        #Scale each pass to equalize areas to the maxx above
        for i, p in enumerate(passes):
            p.string.data_mod[p.name] = p.string.data_mod[p.name].multiply(area_max/areas[i])

    def _averagePattern(self, passes: list[Pass]) -> pd.DataFrame:
        #df placeholder
        average_df = pd.DataFrame()
        for p in passes:
            s = p.string.data_mod.set_index('loc')[p.name]
            average_df = average_df.join(s, how='outer', lsuffix='_l', rsuffix='_r')
        #average_df.fillna(0)
        #take the column-wise average and add that series to the placeholder
        average_df.interpolate(limit_area='inside')
        average_df['Average'] = average_df.fillna(0).mean(axis='columns')
        average_df = average_df.reset_index()
        print('CREATING AVERAGE')
        print(average_df)
        return average_df