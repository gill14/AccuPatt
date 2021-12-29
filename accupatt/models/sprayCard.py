import math, cv2
import sqlite3
from PyQt5.QtCore import QSettings
import numpy as np
import uuid

import accupatt.config as cfg
from accupatt.helpers.sprayCardImageProcessor import SprayCardImageProcessor
from accupatt.helpers.atomizationModel import AtomizationModel
class SprayCard:

    def __init__(self, id = '', name = '', filepath = None, dpi=600):
        self.id = id
        if self.id == '':
            self.id = str(uuid.uuid4())
        self.filepath = filepath
        self.name = name
        self.location = None
        self.has_image = False
        self.include_in_composite = cfg.INCLUDE_IN_COMPOSITE_NO

        self.dpi = dpi
        self.area_px2 = 0.0
        self.stain_areas_all_px2 = []
        self.stain_areas_valid_px2 = []

        self._load_defaults()
    
    def image_original(self):
        return self._read_image_from_db()

    def image_processed(self, fillShapes):
        # Returns processed image
        # And Populates Stain Area Lists
        return SprayCardImageProcessor(sprayCard=self).image_contour(fillShapes)

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
        if self.area_px2 == 0:
            return 0
        return round(len(self.stain_areas_all_px2) / self._px2_to_in2(self.area_px2)) 

    def volumetric_stats(self):
        #P Protect agains empty array
        if len(self.stain_areas_valid_px2) == 0:
            return 0, 0, 0, 0, ''
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
        # Calculate the DSC
        dsc = AtomizationModel(nozzle=None, orifice=None, airspeed=None, pressure=None, angle=None).dsc(dv01=dv01, dv05=dv05)
        # Return rounded representative vol frac diameters as ints, rel span as float
        return round(dv01), round(dv05), round(dv09), rs, dsc

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
        self.threshold_type = cfg.THRESHOLD_TYPE__DEFAULT
        self.threshold_method_color = cfg.THRESHOLD_METHOD_COLOR__DEFAULT
        self.threshold_method_grayscale = cfg.THRESHOLD_METHOD_GRAYSCALE__DEFAULT
        self.threshold_grayscale = cfg.THRESHOLD_GRAYSCALE__DEFAULT
        self.threshold_color_hue = cfg.THRESHOLD_COLOR_HUE__DEFAULT
        self.threshold_color_saturation = cfg.THRESHOLD_COLOR_SATURATION__DEFAULT
        self.threshold_color_brightness = cfg.THRESHOLD_COLOR_BRIGHTNESS__DEFAULT
        self.spread_method = cfg.SPREAD_METHOD__DEFAULT
        self.spread_factor_a = cfg.SPREAD_FACTOR_A__DEFAULT
        self.spread_factor_b = cfg.SPREAD_FACTOR_B__DEFAULT
        self.spread_factor_c = cfg.SPREAD_FACTOR_C__DEFAULT
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

    def _read_image_from_db(self):
        if self.filepath == None: return
        img = None
        try:
            # Opens a file connection to the db
            conn = sqlite3.connect(self.filepath)
            # Get a cursor object
            c = conn.cursor()
            # SprayCard Table
            c.execute('''SELECT image FROM spray_cards WHERE id = ?''',(self.id,))
            # Convert the image to a numpy array
            image = np.asarray(bytearray(c.fetchone()[0]), dtype="uint8")
            # Decode the image to a cv2 image
            img = cv2.imdecode(image, cv2.IMREAD_COLOR)
        # Catch the exception
        except Exception as e:
            # Roll back any change if something goes wrong
            conn.rollback()
            raise e
        finally:
            # Close the db connection
            conn.close()
        return img
    
    def _write_image_to_db(self, image):
        try:
            # Opens a file connection to the db
            db = sqlite3.connect(self.filepath)
            # Request update of card record in table spray_cards by sprayCard.id
            db.cursor().execute('''UPDATE spray_cards SET image = ? WHERE id = ?''',
                                (sqlite3.Binary(image), self.id))
            # Commit the change
            db.commit()
        # Catch the exception
        except Exception as e:
            # Roll back any change if something goes wrong
            db.rollback()
            raise e
        finally:
            # Close the db connection
            db.close()
    
    def save_image_to_db(self, image):
        self._write_image_to_db(image=image)

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
    