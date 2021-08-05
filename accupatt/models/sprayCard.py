import os
import numpy as np
import cv2
import json

from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from scipy import ndimage
import imutils
import random as rng
import matplotlib.pyplot as plt

from accupatt.models.seriesData import SeriesData

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

    
    def image_original(self):
        img = cv2.imread(self.filepath)
        return img

    def image_threshold(self, inverted=False):
        img_thresh = None
        if self.threshold_type == self.THRESHOLD_TYPE_GRAYSCALE:
            img_thresh = self._image_threshold_grayscale(img=self.image_original())
        else:
            img_thresh = self._image_threshold_color(img=self.image_original())
        # Make this optional later
        img_thresh = self._image_close_holes(img_thresh)
        # Only inverted for display
        if inverted:
            img_thresh = cv2.bitwise_not(img_thresh)
        return img_thresh

    def _image_threshold_grayscale(self, img=None):
        # Otsu's thresholding after Gaussian filtering
        img_gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        #img_blur = cv2.GaussianBlur(img_gray,(5,5),0)
        if self.threshold_method_grayscale == self.THRESHOLD_METHOD_AUTOMATIC:
            thresh_val,img_thresh = cv2.threshold(img_gray,self.threshold_grayscale,255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            print('OTSU'+str(thresh_val))
        else:
            _,img_thresh = cv2.threshold(img_gray,self.threshold_grayscale,255,cv2.THRESH_BINARY)
            print(self.threshold_grayscale)
        return img_thresh

    def _image_threshold_color(self, img=None):
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        if self.threshold_color_hue is None or self.threshold_color_saturation is None or self.threshold_color_brightness is None:
            return None
        minHSV = np.array([self.threshold_color_hue[0], self.threshold_color_saturation[0], self.threshold_color_brightness[0]])
        maxHSV = np.array([self.threshold_color_hue[1], self.threshold_color_saturation[1], self.threshold_color_brightness[1]])
        mask = cv2.inRange(img_hsv, minHSV, maxHSV)
        if self.threshold_method_color == self.THRESHOLD_METHOD_INCLUDE:
            mask = cv2.bitwise_not(mask)
        return mask

    def _image_close_holes(self, img_thresh):
        kernel = np.ones((3,3),np.uint8)
        return cv2.morphologyEx(img_thresh, cv2.MORPH_CLOSE, kernel, iterations = 1)

    def image_contour(self, fillShapes=False):
        img_src = self.image_original()
        #If fillshapes, use blank white image
        if fillShapes:
            img_src = np.zeros((img_src.shape[0], img_src.shape[1], 3), np.uint8)
            img_src[:] = (255, 255, 255)
        return self._image_contour(img_src=img_src, fillShapes=fillShapes)

    def _image_contour(self, img_src, fillShapes=False):
        img_thresh = self.image_threshold(inverted=False)
        contours, _ = cv2.findContours(img_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        minEllipse = [None]*len(contours)
        for i, c in enumerate(contours):
            if c.shape[0] > 5:
                minEllipse[i] = cv2.fitEllipse(c)
        # set thickness based on fillShape input param
        color_contours = (138, 43, 226)
        color_shapes = color_contours
        thickness = 1
        if fillShapes: 
            thickness = -1
            color_contours = (0, 0, 255)
            color_shapes = (255, 0, 0)
            img_src[img_thresh==0] = [0, 0, 255]
        
        # draw elipses on img_src
        for i, c in enumerate(contours):
            # draw contours on img_src
            #cv2.drawContours(img_src, contours, i, color_contours, thickness=1)
            #Check if in bounds
            x, y, w, h = cv2.boundingRect(c)
            if x <= 0 or y <= 0 or w >=img_src.shape[1]-1 or h >= img_src.shape[0]-1:
                continue
            cv2.drawContours(img_src, contours, i, color_shapes, thickness=thickness)
            # draw elipse if more than 5 points
            #if c.shape[0] > 5:
                #cv2.ellipse(img_src, minEllipse[i], color_shapes, thickness=thickness)

        return img_src

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

    