import numpy as np
import cv2

import accupatt.config as cfg

class SprayCardImageProcessor:

    def __init__(self, sprayCard):
        self.sprayCard = sprayCard

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
        img_src = self.sprayCard.image_original()
        img_thresh = self._image_threshold(img=img_src)
        #Apply Watershed
        #markers = self._image_watershed(img_src, img_thresh)
        #Re-thresh
        #_, img_thresh = cv2.threshold(markers.astype(np.uint8), 0, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)
        #If fillshapes, use blank white image as src
        if fillShapes:
            img_src = np.zeros((img_src.shape[0], img_src.shape[1], 3), np.uint8)
            img_src[:] = (255, 255, 255)
        return self._image_contour(img_src, img_thresh, fillShapes)

    def _image_contour(self, img_src, img_thresh, fillShapes=False):
        # Card Size
        self.sprayCard.area_px2 = img_src.shape[0] * img_src.shape[1]
        # Clear stain lists
        self.sprayCard.stain_areas_all_px2 = []
        self.sprayCard.stain_areas_valid_px2 = []
        # Use img_thresh to find contours
        contours, _ = cv2.findContours(img_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # When !fillShapes(default), set thickness will outline contours on img_src using these colors
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
        for i, c in enumerate(contours):  
            # If contour is below the min pixel size, don't count it anywhere
            if cv2.contourArea(c) < 4:
                continue
            # If contour above min area size, count it for coverage only
            self.sprayCard.stain_areas_all_px2.append(self._calc_contour_area(c))
            # If contour touches edge, count it for coverage only
            x, y, w, h = cv2.boundingRect(c)
            if x <= 0 or y <= 0 or (x+w) >= img_src.shape[1]-1 or (y+h) >= img_src.shape[0]-1:
                continue
            # Passes all checks, include in droplet analysis
            contours_include.append(c)
            self.sprayCard.stain_areas_valid_px2.append(self._calc_contour_area(c))
            # If fillShapes, draw white borders on contours to show watershed seperation
            #if fillShapes:
            #    cv2.drawContours(img_src, contours, i, (255,255,255), thickness=1)
        # Draw all contours
        cv2.drawContours(img_src, contours, -1, color_stain_not_counted, thickness=thickness)
        # Draw record-worthy contour (over previously drawn contour, just new color)
        cv2.drawContours(img_src, contours_include, -1, color_stain_counted, thickness=thickness)
        
        return img_src

    def _calc_contour_area(self, contour):
        # Default to simple Area
        return cv2.contourArea(contour)
        # ToDo include more area calculation options (mean feret, etc.)
