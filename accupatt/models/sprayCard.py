import math
import sqlite3
import uuid

import accupatt.config as cfg
import cv2
import numpy as np
from accupatt.helpers.atomizationModel import AtomizationModel
from openpyxl import load_workbook
from openpyxl_image_loader import SheetImageLoader
from PyQt6.QtCore import QSettings


class SprayCard:

    def __init__(self, id = '', name = '', filepath = None, dpi=600):
        self.id = id
        if self.id == '':
            self.id = str(uuid.uuid4())
        self.filepath = filepath
        self.name = name
        self.location = None
        self.location_units = None
        self.has_image = False
        self.include_in_composite = cfg.INCLUDE_IN_COMPOSITE_NO

        self.dpi = dpi
        self.area_px2 = 0.0
        self.stain_areas_all_px2 = []
        self.stain_areas_valid_px2 = []
        
        self.watershed = True

        self._load_defaults()
    
    def image_original(self):
        return sprayCardImageFileHandler.read_image_from_file(self)

    def images_processed(self):
        # Returns processed images as tuple (overlay on og, binary mask)
        # And Populates Stain Area Lists
        return SprayCardImageProcessor(sprayCard=self).draw_and_log_stains()

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

    def build_droplet_data(self):
        # Protect agains empty array
        if len(self.stain_areas_valid_px2) == 0:
            return [],[]
        drop_dia_um = []
        drop_vol_um3 = []
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
        return drop_dia_um, drop_vol_um3
    
    def volumetric_stats(self, drop_dia_um = None, drop_vol_um3 = None):
        # Protect agains empty array
        if len(self.stain_areas_valid_px2) == 0:
            return 0, 0, 0, 0, ''
        if drop_dia_um is None or drop_vol_um3 is None:
            drop_dia_um, drop_vol_um3 = self.build_droplet_data()
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
        return area_px2 / (self.dpi ** 2)

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
        self.settings = QSettings('accupatt','AccuPatt')
        if self.spread_method == None:
            self.method = self.settings.value('spread_factor_method', defaultValue=cfg.SPREAD_METHOD_ADAPTIVE, type=int)
        if self.spread_factor_a == None:
            self.spread_factor_a = self.settings.value('spread_factor_a', defaultValue=0.0, type=float)
        if self.spread_factor_b == None:
            self.spread_factor_b = self.settings.value('spread_factor_b', defaultValue=0.0009, type=float)
        if self.spread_factor_c == None:
            self.spread_factor_c = self.settings.value('spread_factor_c', defaultValue=1.6333, type=float)
    
    def save_image_to_file(self, image):
        return sprayCardImageFileHandler.save_image_to_file(self, image)

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
      
class sprayCardImageFileHandler:
    
    def read_image_from_file(sprayCard: SprayCard):
        if sprayCard.filepath == None or not sprayCard.has_image: return
        if sprayCard.filepath[-1] == 'x':
            return sprayCardImageFileHandler._read_image_from_xlsx(sprayCard=sprayCard)
        elif sprayCard.filepath[-1] == 'b':
            return sprayCardImageFileHandler._read_image_from_db(sprayCard=sprayCard)
        return
    
    def save_image_to_file(sprayCard: SprayCard, image):
        if sprayCard.filepath == None or sprayCard.filepath == '': return
        print(sprayCard.filepath)
        if sprayCard.filepath[-1] == 'b':
            return sprayCardImageFileHandler._write_image_to_db(sprayCard=sprayCard, image=image)
    
    def _read_image_from_xlsx(sprayCard: SprayCard):
        wb = load_workbook(sprayCard.filepath)
        # Get Image from applicable sheet
        image_PIL = SheetImageLoader(wb[sprayCard.name]).get('A1')
        #Convert PIL Image to CVImage
        return cv2.cvtColor(np.array(image_PIL), cv2.COLOR_RGB2BGR)
    
    def _read_image_from_db(sprayCard: SprayCard):
        img = None
        try:
            # Opens a file connection to the db
            conn = sqlite3.connect(sprayCard.filepath)
            # Get a cursor object
            c = conn.cursor()
            # SprayCard Table
            c.execute('''SELECT image FROM spray_cards WHERE id = ?''',(sprayCard.id,))
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
    
    def _write_image_to_db(sprayCard: SprayCard, image):
        success = False
        try:
            # Opens a file connection to the db
            db = sqlite3.connect(sprayCard.filepath)
            # Request update of card record in table spray_cards by sprayCard.id
            db.cursor().execute('''UPDATE spray_cards SET image = ? WHERE id = ?''',
                                (sqlite3.Binary(image), sprayCard.id))
            # Commit the change
            db.commit()
            sprayCard.has_image = True
            success = True
        # Catch the exception
        except Exception as e:
            # Roll back any change if something goes wrong
            db.rollback()
            raise e
        finally:
            # Close the db connection
            db.close()
        return success
class SprayCardImageProcessor:

    def __init__(self, sprayCard):
        self.sprayCard: SprayCard = sprayCard
        
    def draw_and_log_stains(self):
        img_src = self.sprayCard.image_original()
        img_thresh = self._image_threshold(img=img_src)
        # Find all contours (stains)
        contours, _ = cv2.findContours(img_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # Watershed Segmentation
        if self.sprayCard.watershed:
            # Find all contours via watershed
            contours = self._image_watershed(img_src.copy(), img_thresh.copy(), contours)
        # Get src overlay image
        img_overlay = self._image_stains(img=img_src, contours=contours, fillShapes=False)
        # Get Binary image
        img = np.zeros((img_src.shape[0], img_src.shape[1], 3), np.uint8)
        img[:] = (255, 255, 255)
        img_binary = self._image_stains(img=img, contours=contours, fillShapes=True)

        return img_overlay, img_binary

    def _image_threshold(self, img):
        if self.sprayCard.threshold_type == cfg.THRESHOLD_TYPE_GRAYSCALE:
            return self._image_threshold_grayscale(img)
        else:
            return self._image_threshold_color(img)

    def _image_threshold_grayscale(self, img):
        #Convert to grayscale
        img_gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        if self.sprayCard.threshold_method_grayscale == cfg.THRESHOLD_METHOD_AUTOMATIC:
            #Run Otsu Threshold, if threshold value is within ui-specified range, return it
            thresh_val,_img_thresh = cv2.threshold(
                src = img_gray,
                thresh = 0, # This val isn't used when Otsu's method is employed
                maxval = 255,
                type = cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
            if thresh_val <= self.sprayCard.threshold_grayscale:
                return _img_thresh
        #If manually thresholding, or auto returned threshold value outside ui-specified range, run manual thresh and return it
        _, img_thresh = cv2.threshold(
            src = img_gray,
            thresh = self.sprayCard.threshold_grayscale,
            maxval = 255,
            type = cv2.THRESH_BINARY_INV)
        return img_thresh

    def _image_threshold_color(self, img):
        #Use HSV colorspace
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        if self.sprayCard.threshold_color_hue is None or self.sprayCard.threshold_color_saturation is None or self.sprayCard.threshold_color_brightness is None:
            return None
        #Convenience arrays for user-defined HSB range values
        minHSV = np.array([self.sprayCard.threshold_color_hue[0], self.sprayCard.threshold_color_saturation[0], self.sprayCard.threshold_color_brightness[0]])
        maxHSV = np.array([self.sprayCard.threshold_color_hue[1], self.sprayCard.threshold_color_saturation[1], self.sprayCard.threshold_color_brightness[1]])
        # Binarize image with TRUE for HSB values in user-defined range
        mask = cv2.inRange(img_hsv, minHSV, maxHSV)
        # Invert image according to user defined method
        if self.sprayCard.threshold_method_color == cfg.THRESHOLD_METHOD_INCLUDE:
            mask = cv2.bitwise_not(mask)
        return mask

    def _image_watershed(self, img_src, img_thresh, contours_original):
        thresh = img_thresh
        # noise removal
        kernel = np.ones((3,3),np.uint8)
        opening = cv2.morphologyEx(thresh,cv2.MORPH_OPEN,kernel, iterations = 2)
        # sure background area
        sure_bg = cv2.dilate(opening,kernel,iterations=3)
        # Finding sure foreground area
        dist_transform = cv2.distanceTransform(opening,cv2.DIST_L2,5)
        _, sure_fg = cv2.threshold(dist_transform,0.2*dist_transform.max(),255,0)
        # Finding unknown region
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg,sure_fg)
        # Marker labelling
        _, markers = cv2.connectedComponents(sure_fg)
        # Add one to all labels so that sure background is not 0, but 1
        markers = markers+1
        # Now, mark the region of unknown with zero
        markers[unknown==255] = 0
        # Do watershed segmentation, then find the resultant contours
        img_thresh_ws = cv2.watershed(img_src,markers).astype(np.uint8)
        _, img_thresh_ws = cv2.threshold(img_thresh_ws, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        contours, hierarchy = cv2.findContours(img_thresh_ws, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # Loop over ws contours to exclude parent contours and apply fill
        contours_include = []
        for i, c in enumerate(contours):
            # If contour has no children (inner contours) draw and log it
            if hierarchy[0][i][2] == -1:
                cv2.drawContours(img_thresh_ws, contours, i, 255, cv2.FILLED)
                contours_include.append(c)
        # Loop over original contours to see which need added to
        # those found in contours_ws (typically the smaller ones)
        for c in contours_original:
            x, y, w, h = cv2.boundingRect(c)
            breakout = False
            # Loop over each pt in the bounding rect, if pt is in the contour, check if that pt 
            # is already painted on the img_thresh_ws... 
            # If so, skip it, breakout and continue outermost loop
            for _x in range(x, x+w):
                for _y in range(y, y+h):
                    if cv2.pointPolygonTest(c, [_x,_y], False) >= 0 and img_thresh_ws[_y,_x] == 255:
                        breakout = True
                        break       
                if breakout:
                    break
            if breakout:
                continue
            # Since c not already in contours_ws, add it
            contours_include.append(c)
            
        return contours_include

    def _image_stains(self, img, contours, fillShapes=False):
        # Card Size
        self.sprayCard.area_px2 = img.shape[0] * img.shape[1]
        # Clear stain lists
        self.sprayCard.stain_areas_all_px2 = []
        self.sprayCard.stain_areas_valid_px2 = []
        # When !fillShapes (default), set thickness will outline contours on img_src using these colors
        color_stain_counted = cfg.COLOR_STAIN_OUTLINE
        color_stain_not_counted = cfg.COLOR_STAIN_OUTLINE
        thickness = 1
        # When fillshapes, netagive thickness will fill contours on white image using these new colors
        if fillShapes: 
            thickness = -1
            color_stain_not_counted = cfg.COLOR_STAIN_FILL_ALL
            color_stain_counted = cfg.COLOR_STAIN_FILL_VALID      
        # Iterate thorugh each contour to find includables
        contours_include = []
        for c in contours:
            area = self._calc_contour_area(c)
            x, y, w, h = cv2.boundingRect(c)
            # If contour is below the min pixel size, don't count it anywhere
            if w < 3 or h < 3:
                continue
            # If contour is whole card, don't count it anywhere
            if area >= 0.95 * w * h:
                continue
            # If contour above min area size, count it for coverage only
            self.sprayCard.stain_areas_all_px2.append(area)
            # If contour touches edge, count it for coverage only
            if x <= 0 or y <= 0 or (x+w) >= img.shape[1]-1 or (y+h) >= img.shape[0]-1:
                continue
            # Passes all checks, include in droplet analysis
            contours_include.append(c)
            self.sprayCard.stain_areas_valid_px2.append(area)   
        if len(contours_include) > 0:
            # Draw all contours
            cv2.drawContours(img, contours, -1, color_stain_not_counted, thickness=thickness)
            # Draw record-worthy contour (over previously drawn contour, just new color)
            cv2.drawContours(img, contours_include, -1, color_stain_counted, thickness=thickness)
            if fillShapes:
                cv2.drawContours(img, contours, -1, (255,255,255), thickness=1)
        
        return img

    def _calc_contour_area(self, contour):
        # Default to simple Area
        return cv2.contourArea(contour)
        # ToDo include more area calculation options (mean feret, etc.)
    