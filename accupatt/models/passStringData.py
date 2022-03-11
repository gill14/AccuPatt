import numpy as np
import pandas as pd
import scipy.signal as sig
import accupatt.config as cfg

class PassStringData:
    
    def __init__(self, name):
        self.name = name
        # String Data Collection 
        self.wav_ex = cfg.get_spec_wav_em()
        self.wav_em = cfg.get_spec_wav_ex()
        self.integration_time_ms = cfg.get_spec_int_time_millis()
        # String Data
        self.data_ex = pd.DataFrame() #Holds Excitation Data
        self.data = pd.DataFrame() #Holds original Data
        self.data_mod = pd.DataFrame() #Holds data with all requested modifications
        self.data_loc_units = cfg.get_unit_data_location()
        # String Data Mod Options
        self.trim_l = 0
        self.trim_r = 0
        self.trim_v = 0.0
        self.rebase = False
        self.center = True
        self.center_method = cfg.get_center_method()
        self.smooth = True
        self.smooth_window = cfg.get_string_smooth_window()
        self.smooth_order = cfg.get_string_smooth_order()
        
    def modifyData(self, loc_units=None):
        if self.data.empty: 
            return
        self.data_mod = self.data.copy()
        # Assert location units if provided
        self.reLoc(self.data_mod, loc_units)
        # Trim it horizontally
        self.trimLR(self.data_mod, self.trim_l, self.trim_r)
        # Rebase it
        self.rebaseIt(self.data_mod, self.rebase, self.trim_l, self.trim_r)
        # Trim it vertically
        self.trimV(self.data_mod, self.trim_v)
        #Center it
        self.centerify(self.data_mod, self.center_method)
        #Smooth it
        self.smoothIt(self.data_mod, self.smooth, self.smooth_window, self.smooth_order)

    def reLoc(self, d: pd.DataFrame, loc_units: str = None):
        if loc_units == None or loc_units == self.data_loc_units:
            return
        if loc_units == cfg.UNIT_FT:
            # Convert loc from M to FT
            d['loc'] = d['loc'].multiply(cfg.FT_PER_M)
        else:
            # Convert loc from FT to M
            d['loc'] = d['loc'].divide(cfg.FT_PER_M)

    def trimLR(self, d: pd.DataFrame, trimL: int = 0, trimR: int = 0):
        # Left trimmed points set to -1
        d.loc[d.index[:trimL],self.name] = -1
        # Right trimmed points set to -1
        d.loc[d.index[(-1-trimR):],self.name] = -1
        #Find new min inside untrimmed area
        min = self.findMin(d, trimL, trimR)
        #subtract min from all points
        d[self.name] = d[self.name].sub(min)
        #clip all negative values (from trimmed areas) to 0
        d[self.name] = d[self.name].clip(lower=0)
    
    def findMin(self, d: pd.DataFrame, trimL: int = 0, trimR: int = 0) -> float:
        return d[trimL:-1-trimR][self.name].min()
       
    def rebaseIt(self, d: pd.DataFrame, isRebase: bool = False, trimL: int = 0, trimR: int = 0):
        if not isRebase:
            return
        print('rebasing')
        # Calculate trimmed/untrimmed distances
        untrimmed_dist = d.at[d.index[-1], 'loc'] - d.at[d.index[0], 'loc']
        trimmed_dist = d.at[d.index[-1-trimR], 'loc'] - d.at[d.index[trimL], 'loc']
        # Drop data points outside trimmed area
        d.drop(d[d.index < trimL].index, inplace = True)
        d.drop(d[d.index > d.index[-1-trimR]].index, inplace= True)
        # Rebase locations according to ratio of untrimmed:trimmed length
        d['loc'] = d['loc'].multiply(untrimmed_dist / trimmed_dist)
        
    def trimV(self, d: pd.DataFrame, trimV: float = 0.0):
        #Trim Vertical
        d[self.name] = d[self.name].sub(trimV)
        #clip all negative values (from trimmed areas) to 0
        d[self.name] = d[self.name].clip(lower=0)
        print(d)

    def centerify(self, d: pd.DataFrame, centerMethod):
        if centerMethod == cfg.CENTER_METHOD_CENTROID:
            #Use Centroid
            c = self._calcCentroid(d)
        elif centerMethod == cfg.CENTER_METHOD_COD:
            #Use Center of Distribution
            c = self._calcCenterOfDistribution(d)
        else:
            # No centering applied
            c = 0
        # Subtract the calculated center from the x vals
        d['loc'] = d['loc'].sub(c)

    def _calcCentroid(self, d: pd.DataFrame):
        return (d[self.name] * d['loc']).sum() / d[self.name].sum()

    def _calcCenterOfDistribution(self, d: pd.DataFrame):
        sumNumerator = 0.0
        sumDenominator = 0.0
        for i in range(0,len(d.index)-1, 1):
            D = d.at[i, self.name]
            Dn = d.at[i+1, self.name]
            X = d.at[i, 'loc']
            Xn = d.at[i+1, 'loc']
            #Calc Numerator and add to summation
            sumNumerator += (D*(Xn+X) + (Dn-D)*(2*Xn+X)/3)
            sumDenominator += (Dn+D)
        #Calc and return CoD
        return sumNumerator / sumDenominator

    def smoothIt(self, d: pd.DataFrame, isSmooth: bool, window: float, order: int):
        if not isSmooth:
            return
        # Calculate the integer smoothing window
        _window = int(np.ceil(np.abs(d['loc'].abs().idxmin() - d['loc'].sub(window).abs().idxmin())))
        # Round it up to the next odd integer if needed
        _window = _window + 1 if _window % 2 == 0 else _window
        print(_window)
        # Smooth y vals
        d[self.name] = sig.savgol_filter(d[self.name], _window, order)
        # Clip y vals below 0
        d[self.name] = d[self.name].clip(lower=0)

    def setData(self, x_data, y_data, y_ex_data):
        self.data = pd.DataFrame(data=list(zip(x_data,y_data)), columns=['loc', self.name])
        self.data_ex = pd.DataFrame(data=list(zip(x_data, y_ex_data)), columns=['loc', self.name])

    def setTrims(self, trim_l = None, trim_r = None, trim_v = None):
        if trim_l is not None:
            self.trim_l = trim_l
        if trim_r is not None:
            self.trim_r = trim_r
        if trim_v is not None:
            self.trim_v = trim_v