import os, math
from PyQt5.QtCore import QSettings
import numpy as np
import cv2
import json

import accupatt.config as cfg
from accupatt.helpers.sprayCardImageProcessor import SprayCardImageProcessor
class SprayCard:

    def __init__(self, name = '', filepath = None, dpi=600):

        self.filepath = filepath
        self.name = name
        self.threshold_type = None
        self.threshold_method_color = None
        self.threshold_method_grayscale = None
        self.threshold_grayscale = None
        self.threshold_color_hue = None
        self.threshold_color_saturation = None
        self.threshold_color_brightness = None
        self.dpi = dpi
        self.area_px2 = 0.0
        self.stain_areas_all_px2 = []
        self.stain_areas_valid_px2 = []
        self.spread_method = None
        self.spread_factor_a = None
        self.spread_factor_b = None
        self.spread_factor_c = None

        self._load_defaults()
    
    def image_original(self):
        img = cv2.imread(self.filepath)
        return img

    def image_processed(self, fillShapes):
        scp = SprayCardImageProcessor(self)
        # Returns processed image AND POPULATES STAIN AREA ARRAYS
        return SprayCardImageProcessor.image_contour(scp, fillShapes)

    def percent_coverage(self):
        #Protect from div/0 error or empty stain array
        if self.area_px2 == 0 or len(self.stain_areas_all_px2) == 0:
            return 0
        # Calculate coverage as percent of pixel area
        cov = sum(self.stain_areas_all_px2) / self.area_px2
        # Return value as percentage
        return cov*100.0

    def stains_per_in2(self):
        # Return a rounded int value
        return round(len(self.stain_areas_all_px2) / self._px2_to_in2(self.area_px2)) 

    def volumetric_stats(self):
        #P Protect agains empty array
        if len(self.stain_areas_valid_px2) == 0:
            return 0, 0, 0, 0
        drop_dia_um = []
        drop_vol_um3 = []
        drop_vol_um3_cum = []
        # Sort areas into ascending order of size
        self.stain_areas_valid_px2.sort()
        for area in self.stain_areas_valid_px2:
            # Convert px2 to um2
            area_um2 = self._px2_to_um2(area)
            # Calculate stain diameter assuming circular stain
            dia_um = math.sqrt((4.0 * area_um2) / math.pi)
            # Apply Spread Factors to get originating drop diameter
            drop_dia_um.append(self._stain_dia_to_drop_dia(dia_um))
            # Use drop diameter to calculate drop volume
            vol_um3 = (math.pi * dia_um**3) / 6.0
            # Build volume list
            drop_vol_um3.append(vol_um3)
        # Calculate volume sum
        drop_vol_um3_sum = sum(drop_vol_um3)
        # Calculate volume fractions
        dv01_vol = 0.10 * drop_vol_um3_sum
        dv05_vol = 0.50 * drop_vol_um3_sum
        dv09_vol = 0.90 * drop_vol_um3_sum
        # Convert lists to np arrays
        drop_dia_um = np.array(drop_dia_um, dtype=float, order='K')
        drop_vol_um3 = np.array(drop_vol_um3, dtype=float, order='K')
        # Create cumulative volume array
        drop_vol_um3_cum = np.cumsum(drop_vol_um3)
        # Interpolate drop diameters using volume fractions
        dv01 = np.interp(dv01_vol, drop_vol_um3_cum, drop_dia_um)
        dv05 = np.interp(dv05_vol, drop_vol_um3_cum, drop_dia_um)
        dv09 = np.interp(dv09_vol, drop_vol_um3_cum, drop_dia_um)
        # Calculate Relative Span
        rs = (dv09 - dv01) / dv05
        # Return rounded representative vol frac diameters as ints, rel span as float
        return round(dv01), round(dv05), round(dv09), rs

    def _px2_to_um2(self, area_px2):
        um_per_px = cfg.UM_PER_IN / self.dpi
        return area_px2 * um_per_px * um_per_px
    
    def _px2_to_in2(self, area_px2):
        return area_px2 / (self.dpi * self.dpi)

    def _stain_dia_to_drop_dia(self, stain_dia):
        if self.spread_method == cfg.SPREAD_METHOD_DIRECT:
            # D = A(S)^2 + B(S) + C
            return self.spread_factor_a * stain_dia * stain_dia + self.spread_factor_b * stain_dia + self.spread_factor_c
        elif self.spread_method == cfg.SPREAD_METHOD_ADAPTIVE:
            # D = S / ( A(S)^2 + B(S) + C )
            return stain_dia / (self.spread_factor_a * stain_dia * stain_dia + self.spread_factor_b * stain_dia + self.spread_factor_c)
        # DD = DS
        return stain_dia

    def _load_defaults(self):
        # Load in Settings
        self.settings = QSettings('BG Application Consulting','AccuPatt')
        if self.spread_method == None:
            self.method = self.settings.value('spread_factor_method', defaultValue=cfg.SPREAD_METHOD_ADAPTIVE, type=int)
        if self.spread_factor_a == None:
            self.spread_factor_a = self.settings.value('spread_factor_a', defaultValue=0.0, type=float)
        if self.spread_factor_b == None:
            self.spread_factor_b = self.settings.value('spread_factor_b', defaultValue=0.0009, type=float)
        if self.spread_factor_c == None:
            self.spread_factor_c = self.settings.value('spread_factor_c', defaultValue=1.6333, type=float)

    def set_threshold_type(self, type=cfg.THRESHOLD_TYPE_GRAYSCALE):
        self.threshold_type = type

    def set_threshold_method_grayscale(self, method=cfg.THRESHOLD_METHOD_AUTOMATIC):
        self.threshold_method_grayscale = method

    def set_threshold_grayscale(self, threshold: int):
        self.threshold_grayscale = threshold

    def set_threshold_method_color(self, method=cfg.THRESHOLD_METHOD_INCLUDE):
        self.threshold_method_color = method

    def set_threshold_color_hue(self, min: 0, max: 255):
        self.threshold_color_hue = [min,max]

    def set_threshold_color_saturation(self, min: 0, max: 255):
        self.threshold_color_saturation = [min,max]

    def set_threshold_color_brightness(self, min: 0, max: 255):
        self.threshold_color_brightness = [min,max]

    def to_json(self):
        '''
        convert the instance of this class to json
        '''
        return json.dumps(self, indent = 4, default=lambda o: o.__dict__)

    def load_from_json(json_dict, folder):
        sc = SprayCard()
        sc.name = json_dict['name']
        filepath = os.path.join(folder, sc.name+'.png')
        if os.path.exists(filepath): sc.filepath = filepath
        sc.dpi = json_dict['dpi']
        sc.threshold_type = json_dict['threshold_type']
        sc.threshold_method_color = json_dict['threshold_method_color']
        sc.threshold_method_grayscale = json_dict['threshold_method_grayscale']
        sc.threshold_grayscale = json_dict['threshold_grayscale']
        sc.threshold_color_hue = json_dict['threshold_color_hue']
        sc.threshold_color_saturation = json_dict['threshold_color_saturation']
        sc.threshold_color_brightness = json_dict['threshold_color_brightness']
        return sc

    