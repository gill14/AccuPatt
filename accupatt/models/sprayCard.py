import os
import numpy as np
import cv2
import json

from accupatt.models.sprayCardStats import SprayCardStats
class SprayCard:

    THRESHOLD_TYPE_GRAYSCALE = 0
    THRESHOLD_TYPE_COLOR = 1

    THRESHOLD_METHOD_AUTOMATIC = 0
    THRESHOLD_METHOD_MANUAL = 1

    THRESHOLD_METHOD_INCLUDE = 0
    THRESHOLD_METHOD_EXCLUDE = 1

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
        self.stats = SprayCardStats(dpi=dpi)

    
    def image_original(self):
        img = cv2.imread(self.filepath)
        return img

    def _image_threshold(self, img):
        if self.threshold_type == self.THRESHOLD_TYPE_GRAYSCALE:
            return self._image_threshold_grayscale(img)
        else:
            return self._image_threshold_color(img)

    def _image_threshold_grayscale(self, img):
        #Convert to grayscale
        img_gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        if self.threshold_method_grayscale == self.THRESHOLD_METHOD_AUTOMATIC:
            #Run Otsu Threshold, if threshold value is within ui-specified range, return it
            thresh_val,_img_thresh = cv2.threshold(img_gray,0,255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
            if thresh_val <= self.threshold_grayscale:
                return _img_thresh
        #If manually thresholding, or auto returned threshold value outside ui-specified range, run manual thresh and return it
        thresh_val,img_thresh = cv2.threshold(img_gray,self.threshold_grayscale,255,cv2.THRESH_BINARY_INV)
        return img_thresh

    def _image_threshold_color(self, img):
        #Use HSV colorspace
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        if self.threshold_color_hue is None or self.threshold_color_saturation is None or self.threshold_color_brightness is None:
            return None
        #Convenience arrays for user-defined HSB range values
        minHSV = np.array([self.threshold_color_hue[0], self.threshold_color_saturation[0], self.threshold_color_brightness[0]])
        maxHSV = np.array([self.threshold_color_hue[1], self.threshold_color_saturation[1], self.threshold_color_brightness[1]])
        # Binarize image with TRUE for HSB values in user-defined range
        mask = cv2.inRange(img_hsv, minHSV, maxHSV)
        # Invert image according to user defined method
        if self.threshold_method_color == self.THRESHOLD_METHOD_INCLUDE:
            mask = cv2.bitwise_not(mask)
        return mask

    def _image_watershed(self, img_src, img_thresh):
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
        markers = cv2.watershed(img_src,markers)
        return markers

    def image_contour(self, fillShapes=False):
        img_src = self.image_original()
        img_thresh = self._image_threshold(img=img_src)
        #Apply Watershed
        markers = self._image_watershed(img_src, img_thresh)
        #Re-thresh
        _, img_thresh = cv2.threshold(markers.astype(np.uint8), 0, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)
        #If fillshapes, use blank white image as src
        if fillShapes:
            img_src = np.zeros((img_src.shape[0], img_src.shape[1], 3), np.uint8)
            img_src[:] = (255, 255, 255)
        return self._image_contour(img_src, img_thresh, fillShapes)

    def _image_contour(self, img_src, img_thresh, fillShapes=False):
        # Place Holders for stains
        stains_all = []
        stains_validated = []
        # Use img_thresh to find contours
        contours, _ = cv2.findContours(img_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # When !fillShapes(default), set thickness will outline contours on img_src using these colors
        color_stain_not_counted = (138, 43, 226)
        color_stain_counted = color_stain_not_counted
        thickness = 1
        # When fillshapes, netagive thickness will fill contours on white image using these new colors
        if fillShapes: 
            thickness = -1
            color_stain_not_counted = (0, 0, 255) # Color all contours Red
            color_stain_counted = (255, 0, 0) # Color record-worthy contours Blue
        # Iterate thorugh each contour
        for i, c in enumerate(contours):
            # Check if in bounds
            x, y, w, h = cv2.boundingRect(c)
            # If contour is below the min pixel size, fail
            if c.shape[0] < 1:
                continue
            # Check if contour is entire image
            if w >=img_src.shape[1]-1 and h >= img_src.shape[0]-1:
                # Set area of image in stats
                self.stats.area_px2 = cv2.contourArea(c)
                continue
            # If not below size threshold or entire image, show contour
            cv2.drawContours(img_src, contours, i, color_stain_not_counted, thickness=thickness)
            # Add contour area to list
            stains_all.append(self.calc_contour_area(c))
            # If contour touches edge, fail
            if x <= 0 or y <= 0 or (x+w) >= img_src.shape[1]-1 or (y+h) >= img_src.shape[0]-1:
                continue
            # Draw record-worthy contour (over previously drawn contour, just new color)
            cv2.drawContours(img_src, contours, i, color_stain_counted, thickness=thickness)
            # Add validated contour area to list
            stains_validated.append(self.calc_contour_area(c))
            # If fillShapes, draw white borders on contours to show watershed seperation
            if fillShapes:
                cv2.drawContours(img_src, contours, i, (255,255,255), thickness=1)

        # Update stats with area lists
        self.stats.stain_areas_all_px2 = stains_all
        self.stats.stain_areas_valid_px2 = stains_validated

        return img_src

    def calc_contour_area(self, contour):
        # Default to simple Area
        return cv2.contourArea(contour)
        # ToDo include more area calculation options (mean feret, etc.)

    def set_threshold_type(self, type=THRESHOLD_TYPE_GRAYSCALE):
        self.threshold_type = type

    def set_threshold_method_grayscale(self, method=THRESHOLD_METHOD_AUTOMATIC):
        self.threshold_method_grayscale = method

    def set_threshold_grayscale(self, threshold: int):
        self.threshold_grayscale = threshold

    def set_threshold_method_color(self, method=THRESHOLD_METHOD_INCLUDE):
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

    