import numpy as np
import cv2
import json

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

    def image_threshold_grayscale(self):
        # Otsu's thresholding after Gaussian filtering
        #gray = cv2.cvtColor(result,cv2.COLOR_BGR2GRAY)
        #blur = cv2.GaussianBlur(gray,(5,5),0)
        #ret,th = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        return

    def image_threshold_color(self):
        img = cv2.imread(self.filepath)
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        if self.threshold_color_hue is None or self.threshold_color_saturation is None or self.threshold_color_brightness is None:
            return None
        minHSV = np.array([self.threshold_color_hue[0], self.threshold_color_saturation[0], self.threshold_color_brightness[0]])
        maxHSV = np.array([self.threshold_color_hue[1], self.threshold_color_saturation[1], self.threshold_color_brightness[1]])
        mask = cv2.inRange(img_hsv, minHSV, maxHSV)
        if self.threshold_method_color == self.THRESHOLD_METHOD_INCLUDE:
            mask = cv2.bitwise_not(mask)
            #print('exclude')
        #cv2.imshow('test',result)
        return mask

    def set_threshold_type(self, type=THRESHOLD_TYPE_GRAYSCALE):
        self.threshold_type = type

    def set_threshold_method_grayscale(self, method=THRESHOLD_METHOD_AUTOMATIC):
        self.threshold_method_grayscale = method

    def set_threshold_grayscale(self, threshold: int):
        self.threshold_grayscale = threshold

    def set_threshold_method_color(self, method=THRESHOLD_METHOD_INCLUDE):
        self.threshold_method_color = method

    def set_threshold_color_hue(self, min: 0, max: 255):
        self.threshold_color_hue = np.array([min,max])

    def set_threshold_color_saturation(self, min: 0, max: 255):
        self.threshold_color_saturation = np.array([min,max])

    def set_threshold_color_brightness(self, min: 0, max: 255):
        self.threshold_color_brightness = np.array([min,max])

    def to_json(self):
        '''
        convert the instance of this class to json
        '''
        return json.dumps(self, indent = 4, default=lambda o: o.__dict__)

    def load_from_json(json_dict):
        sc = SprayCard()
        sc.filepath = json_dict['filepath']
        sc.name = json_dict['name']
        #ToDo
        return sc

    