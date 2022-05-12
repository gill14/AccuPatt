from dataclasses import dataclass
import math
import uuid

import accupatt.config as cfg
import cv2
import numpy as np
from accupatt.helpers.atomizationModel import AtomizationModel


class SprayCard:
    def __init__(self, id="", name="", filepath=None):
        # Use id if passed, else create one
        self.id = id
        if self.id == "":
            self.id = str(uuid.uuid4())
        self.name = name
        # filepath (either .db or .xlsx) needed for image load/save
        self.filepath = filepath
        self.location = None
        self.location_units = None
        self.has_image = False
        self.include_in_composite = False
        # Init optionals using persistent values/defaults from config if available
        self.dpi = cfg.get_image_dpi()
        self.threshold_type = cfg.get_threshold_type()
        self.threshold_method_grayscale = cfg.get_threshold_grayscale_method()
        self.threshold_grayscale = cfg.get_threshold_grayscale()
        self.threshold_color_hue_min = cfg.get_threshold_hsb_hue_min()
        self.threshold_color_hue_max = cfg.get_threshold_hsb_hue_max()
        self.threshold_color_hue_pass = cfg.get_threshold_hsb_hue_pass()
        self.threshold_color_saturation_min = cfg.get_threshold_hsb_saturation_min()
        self.threshold_color_saturation_max = cfg.get_threshold_hsb_saturation_max()
        self.threshold_color_saturation_pass = cfg.get_threshold_hsb_saturation_pass()
        self.threshold_color_brightness_min = cfg.get_threshold_hsb_brightness_min()
        self.threshold_color_brightness_max = cfg.get_threshold_hsb_brightness_max()
        self.threshold_color_brightness_pass = cfg.get_threshold_hsb_brightness_pass()
        self.watershed = cfg.get_watershed()
        self.min_stain_area_px = cfg.get_min_stain_area_px()
        self.stain_approximation_method = cfg.get_stain_approximation_method()
        self.spread_method = cfg.get_spread_factor_equation()
        self.spread_factor_a = cfg.get_spread_factor_a()
        self.spread_factor_b = cfg.get_spread_factor_b()
        self.spread_factor_c = cfg.get_spread_factor_c()
        # Initialize stain stats
        self.area_px2 = 0.0
        self.stain_areas_all_px2 = []
        self.stain_areas_valid_px2 = []
        self.stats = SprayCardStats(sprayCard=self)
        # Flag for currency
        self.current = False
        # Temporary working variable
        self.threshold_grayscale_calculated = cfg.get_threshold_grayscale()

    def image_original(self):
        return sprayCardImageFileHandler.read_image_from_file(self)

    def images_processed(self):
        # Returns processed images as tuple (overlay on og, binary mask)
        # And Populates Stain Area Lists, card area
        self.current = True
        scip = SprayCardImageProcessor(sprayCard=self)
        self.threshold_grayscale_calculated = scip.threshold_grayscale_calculated
        return scip.draw_and_log_stains()

    def save_image_to_file(self, image):
        return sprayCardImageFileHandler.save_image_to_file(self, image)

    def set_filepath(self, filepath):
        self.filepath = filepath

    def set_threshold_type(self, type=cfg.THRESHOLD_TYPE__DEFAULT):
        self.threshold_type = type

    def set_threshold_method_grayscale(
        self, method=cfg.THRESHOLD_GRAYSCALE_METHOD__DEFAULT
    ):
        self.threshold_method_grayscale = method

    def set_threshold_grayscale(self, threshold: int):
        self.threshold_grayscale = threshold

    def set_threshold_color_hue(self, min=None, max=None, bandpass=None):
        if min:
            self.threshold_color_hue_min = min
        if max:
            self.threshold_color_hue_max = max
        if bandpass is not None:
            self.threshold_color_hue_pass = bandpass

    def set_threshold_color_saturation(self, min=None, max=None, bandpass=None):
        if min:
            self.threshold_color_saturation_min = min
        if max:
            self.threshold_color_saturation_max = max
        if bandpass is not None:
            self.threshold_color_saturation_pass = bandpass

    def set_threshold_color_brightness(self, min=None, max=None, bandpass=None):
        if min:
            self.threshold_color_brightness_min = min
        if max:
            self.threshold_color_brightness_max = max
        if bandpass is not None:
            self.threshold_color_brightness_pass = bandpass


@dataclass
class SprayCardStats:

    sprayCard: SprayCard

    dv01: int = 0
    dv05: int = 0
    dv09: int = 0

    # Flag for currency
    current = False

    # Public value/text getters

    def get_dv01(self, text=False):
        if text:
            return str(self.dv01) + " \u03BC" + "m" if self.dv01 > 0 else ''
        else:
            return self.dv01

    def get_dv01_color(self) -> str:
        return AtomizationModel().dsc_color_dv01(dv01=self.dv01)

    def get_dv05(self, text=False):
        if text:
            return str(self.dv05) + " \u03BC" + "m" if self.dv05 > 0 else ''
        else:
            return self.dv05

    def get_dv05_color(self) -> str:
        return AtomizationModel().dsc_color_dv05(dv05=self.dv09)

    def get_dv09(self, text=False):
        if text:
            return str(self.dv09) + " \u03BC" + "m" if self.dv01 > 0 else ''
        else:
            return self.dv09

    def get_dv09_color(self) -> str:
        return AtomizationModel().dsc_color_dv09(dv09=self.dv09)

    def get_dsc(self):
        return AtomizationModel().dsc(dv01=self.dv01, dv05=self.dv05)

    def get_dsc_color(self) -> str:
        return AtomizationModel().dsc_color(dv01=self.dv01, dv05=self.dv05)

    def get_relative_span(self, text=False):
        if self.dv05 == 0:
            rs = 0
        else:
            rs = (self.dv09 - self.dv01) / self.dv05
        if text:
            return f"{rs:.2f}"
        else:
            return rs

    def get_percent_coverage(self, text=False):
        # Protect from div/0 error or empty stain array
        if self.sprayCard.area_px2 == 0 or len(self.sprayCard.stain_areas_all_px2) == 0:
            return 0
        # Calculate coverage as percent of pixel area
        cov = (
            sum(self.sprayCard.stain_areas_all_px2) / self.sprayCard.area_px2
        ) * 100.0
        if text:
            return f"{cov:.2f}%"
        else:
            return cov

    def get_number_of_stains(self, text=False):
        if text:
            return str(len(self.sprayCard.stain_areas_valid_px2))
        else:
            return len(self.sprayCard.stain_areas_valid_px2)

    def get_stains_per_in2(self, text=False):
        if self.sprayCard.area_px2 == 0:
            return 0
        spsi = round(
            len(self.sprayCard.stain_areas_valid_px2)
            / self._px2_to_in2(self.sprayCard.area_px2)
        )
        if text:
            return str(spsi)
        else:
            return spsi

    def get_minimum_detectable_droplet_diameter(self):
        min_stain_area = self._px2_to_um2(self.sprayCard.min_stain_area_px)
        min_stain_dia = math.sqrt((4.0 * min_stain_area) / math.pi)
        return round(self._stain_dia_to_drop_dia(min_stain_dia))

    # Public setter for dv's

    def set_volumetric_stats(self, drop_dia_um=None, drop_vol_um3=None):
        # Protect agains empty array
        if len(self.sprayCard.stain_areas_valid_px2) == 0:
            self.dv01 = 0
            self.dv05 = 0
            self.dv09 = 0
            return
        # dd and dv lists normally none, but will have values already for composite card calcs
        if drop_dia_um is None or drop_vol_um3 is None:
            drop_dia_um, drop_vol_um3 = self.get_droplet_diameters_and_volumes()
        # Calculate volume sum
        drop_vol_um3_sum = sum(drop_vol_um3)
        # Calculate volume fractions
        dv01_vol = 0.10 * drop_vol_um3_sum
        dv05_vol = 0.50 * drop_vol_um3_sum
        dv09_vol = 0.90 * drop_vol_um3_sum
        # Convert lists to np arrays
        drop_dia_um = np.array(drop_dia_um, dtype=float, order="K")
        drop_vol_um3 = np.array(drop_vol_um3, dtype=float, order="K")
        # Create cumulative volume array
        drop_vol_um3_cum = np.cumsum(drop_vol_um3)
        # Interpolate drop diameters using volume fractions
        self.dv01 = round(np.interp(dv01_vol, drop_vol_um3_cum, drop_dia_um))
        self.dv05 = round(np.interp(dv05_vol, drop_vol_um3_cum, drop_dia_um))
        self.dv09 = round(np.interp(dv09_vol, drop_vol_um3_cum, drop_dia_um))
        # Reset currency flag
        self.current = True

    # Publicly accessible getter for dd and dv lists, only public so can be used in Composite Card calculations

    def get_droplet_diameters_and_volumes(self) -> tuple[list[float], list[float]]:
        # Protect agains empty array
        if len(self.sprayCard.stain_areas_valid_px2) == 0:
            return [], []
        drop_dia_um = []
        drop_vol_um3 = []
        # Sort areas into ascending order of size
        self.sprayCard.stain_areas_valid_px2.sort()
        for area in self.sprayCard.stain_areas_valid_px2:
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

    # Internal Functions

    def _px2_to_um2(self, area_px2):
        um_per_px = cfg.UM_PER_IN / self.sprayCard.dpi
        return area_px2 * um_per_px * um_per_px

    def _px2_to_in2(self, area_px2):
        return area_px2 / (self.sprayCard.dpi**2)

    def _stain_dia_to_drop_dia(self, stain_dia):
        if self.sprayCard.spread_method == cfg.SPREAD_METHOD_DIRECT:
            # D = A(S)^2 + B(S) + C
            return (
                self.sprayCard.spread_factor_a * stain_dia * stain_dia
                + self.sprayCard.spread_factor_b * stain_dia
                + self.sprayCard.spread_factor_c
            )
        elif self.sprayCard.spread_method == cfg.SPREAD_METHOD_ADAPTIVE:
            # D = S / ( A(S)^2 + B(S) + C )
            return stain_dia / (
                self.sprayCard.spread_factor_a * stain_dia * stain_dia
                + self.sprayCard.spread_factor_b * stain_dia
                + self.sprayCard.spread_factor_c
            )
        # DD = DS
        return stain_dia


class sprayCardImageFileHandler:
    def read_image_from_file(sprayCard: SprayCard):
        if sprayCard.filepath == None or not sprayCard.has_image:
            return
        if sprayCard.filepath[-1] == "x":
            return sprayCardImageFileHandler._read_image_from_xlsx(sprayCard=sprayCard)
        elif sprayCard.filepath[-1] == "b":
            return sprayCardImageFileHandler._read_image_from_db(sprayCard=sprayCard)
        return

    def save_image_to_file(sprayCard: SprayCard, image):
        if sprayCard.filepath == None or sprayCard.filepath == "":
            return
        if sprayCard.filepath[-1] == "b":
            return sprayCardImageFileHandler._write_image_to_db(
                sprayCard=sprayCard, image=image
            )

    def _read_image_from_xlsx(sprayCard: SprayCard):
        from accupatt.helpers.dataFileImporter import load_image_from_accupatt_1

        # Get Image from applicable sheet
        image_PIL = load_image_from_accupatt_1(sprayCard.filepath, sprayCard.name)
        # Convert to numpy array
        image_array = np.asarray(image_PIL)
        # Convert PIL Image to CVImage
        return cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

    def _read_image_from_db(sprayCard: SprayCard):
        from accupatt.helpers.dBBridge import load_image_from_db

        # Get byte array of image from db
        byte_array = load_image_from_db(sprayCard.filepath, sprayCard.id)
        # Convert to numpy array
        image_array = np.asarray(byte_array, dtype="uint8")
        # Decode the image to a cv2 image
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    def _write_image_to_db(sprayCard: SprayCard, image):
        from accupatt.helpers.dBBridge import save_image_to_db

        if success := save_image_to_db(sprayCard.filepath, sprayCard.id, image):
            sprayCard.has_image = True
            sprayCard.include_in_composite = True
        return success


class SprayCardImageProcessor:
    def __init__(self, sprayCard):
        self.sprayCard: SprayCard = sprayCard
        self.threshold_grayscale = self.sprayCard.threshold_grayscale
        self.img_src = self.sprayCard.image_original()
        self.threshold_grayscale_calculated, self.img_thresh = self._image_threshold(
            img=self.img_src
        )

    def draw_and_log_stains(self):
        # img_src = self.sprayCard.image_original()
        # self.img_thresh = self._image_threshold(img=img_src)
        # Find all contours (stains)
        contours, _ = cv2.findContours(
            self.img_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        # Watershed Segmentation
        if self.sprayCard.watershed:
            # Find all contours via watershed
            contours = self._image_watershed(
                self.img_src.copy(), self.img_thresh.copy(), contours
            )
        # Get src overlay image
        img_overlay = self._image_stains(
            img=self.img_src, contours=contours, fillShapes=False
        )
        # Get Binary image
        img = np.zeros((self.img_src.shape[0], self.img_src.shape[1], 3), np.uint8)
        img[:] = (255, 255, 255)
        img_binary = self._image_stains(img=img, contours=contours, fillShapes=True)

        return img_overlay, img_binary

    def _image_threshold(self, img):
        if self.sprayCard.threshold_type == cfg.THRESHOLD_TYPE_GRAYSCALE:
            return self._image_threshold_grayscale(img)
        else:
            return self._image_threshold_color(img)

    def _image_threshold_grayscale(self, img):
        # Convert to grayscale
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if (
            self.sprayCard.threshold_method_grayscale
            == cfg.THRESHOLD_GRAYSCALE_METHOD_AUTO
        ):
            # Run Otsu Threshold, if threshold value is within ui-specified range, return it
            thresh_val, _img_thresh = cv2.threshold(
                src=img_gray,
                thresh=0,  # This val isn't used when Otsu's method is employed
                maxval=255,
                type=cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU,
            )
            if thresh_val <= self.sprayCard.threshold_grayscale:
                return thresh_val, _img_thresh
        # If manually thresholding, or auto returned threshold value outside ui-specified range, run manual thresh and return it
        _, img_thresh = cv2.threshold(
            src=img_gray,
            thresh=self.sprayCard.threshold_grayscale,
            maxval=255,
            type=cv2.THRESH_BINARY_INV,
        )
        return self.sprayCard.threshold_grayscale, img_thresh

    def _image_threshold_color(self, img):
        # Readability
        hbl = 0
        hvl = self.sprayCard.threshold_color_hue_min
        hvh = self.sprayCard.threshold_color_hue_max
        hbh = 179
        sbl = 0
        svl = self.sprayCard.threshold_color_saturation_min
        svh = self.sprayCard.threshold_color_saturation_max
        sbh = 255
        bbl = 0
        bvl = self.sprayCard.threshold_color_brightness_min
        bvh = self.sprayCard.threshold_color_brightness_max
        bbh = 255
        # Use HSV colorspace
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Check Hue channel
        if self.sprayCard.threshold_color_hue_pass:
            # Band-Pass
            mask_hue = cv2.inRange(
                img_hsv, np.array([hvl, sbl, bbl]), np.array([hvh, sbh, bbh])
            )
        else:
            # Band-Reject
            mask_hue_low = cv2.inRange(
                img_hsv, np.array([hbl, sbl, bbl]), np.array([hvl, sbh, bbh])
            )
            mask_hue_high = cv2.inRange(
                img_hsv, np.array([hvh, sbl, bbl]), np.array([hbh, sbh, bbh])
            )
            mask_hue = cv2.bitwise_or(mask_hue_low, mask_hue_high)
        # Check Saturation channel
        if self.sprayCard.threshold_color_saturation_pass:
            # Band-Pass
            mask_sat = cv2.inRange(
                img_hsv, np.array([hbl, svl, bbl]), np.array([hbh, svh, bbh])
            )
        else:
            # Band-Reject
            mask_sat_low = cv2.inRange(
                img_hsv, np.array([hbl, sbl, bbl]), np.array([hbh, svl, bbh])
            )
            mask_sat_high = cv2.inRange(
                img_hsv, np.array([hbl, svh, bbl]), np.array([hbh, sbh, bbh])
            )
            mask_sat = cv2.bitwise_or(mask_sat_low, mask_sat_high)
        # Check Brightness channel
        if self.sprayCard.threshold_color_brightness_pass:
            # Band-Pass
            mask_bri = cv2.inRange(
                img_hsv, np.array([hbl, sbl, bvl]), np.array([hbh, sbh, bvh])
            )
        else:
            # Band-Reject
            mask_bri_low = cv2.inRange(
                img_hsv, np.array([hbl, sbl, bbl]), np.array([hbh, sbh, bvl])
            )
            mask_bri_high = cv2.inRange(
                img_hsv, np.array([hbl, sbl, bvh]), np.array([hbh, sbh, bbh])
            )
            mask_bri = cv2.bitwise_or(mask_bri_low, mask_bri_high)
        # Merge layers and return
        return 0, cv2.bitwise_and(cv2.bitwise_and(mask_hue, mask_sat), mask_bri)

    def _image_watershed(self, img_src, img_thresh, contours_original):
        thresh = img_thresh
        # noise removal
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        # sure background area
        sure_bg = cv2.dilate(opening, kernel, iterations=3)
        # Finding sure foreground area
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, 0.2 * dist_transform.max(), 255, 0)
        # Finding unknown region
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)
        # Marker labelling
        _, markers = cv2.connectedComponents(sure_fg)
        # Add one to all labels so that sure background is not 0, but 1
        markers = markers + 1
        # Now, mark the region of unknown with zero
        markers[unknown == 255] = 0
        # Do watershed segmentation, then find the resultant contours
        img_thresh_ws = cv2.watershed(img_src, markers).astype(np.uint8)
        _, img_thresh_ws = cv2.threshold(
            img_thresh_ws, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
        )
        contours, hierarchy = cv2.findContours(
            img_thresh_ws, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
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
            for _x in range(x, x + w):
                for _y in range(y, y + h):
                    if (
                        cv2.pointPolygonTest(c, [_x, _y], False) >= 0
                        and img_thresh_ws[_y, _x] == 255
                    ):
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
        # When fillshapes, netagive thickness will fill contours on white image using these new colors
        thickness = -1 if fillShapes else 1
        color_stain_counted = (
            cfg.COLOR_STAIN_FILL_VALID if fillShapes else cfg.COLOR_STAIN_OUTLINE
        )
        color_stain_edge = (
            cfg.COLOR_STAIN_FILL_EDGE if fillShapes else cfg.COLOR_STAIN_OUTLINE
        )
        color_stain_not_counted = (
            cfg.COLOR_STAIN_FILL_ALL if fillShapes else cfg.COLOR_STAIN_OUTLINE
        )

        # Image dims calc'd once to compare against:
        max_stain_size = 0.90 * img.shape[0] * img.shape[1]
        # Iterate thorugh each contour to find includables
        contours_edge = []
        contours_include = []
        for c in contours:
            # Determine if touching edge before morphing
            x, y, w, h = cv2.boundingRect(c)
            is_edge = (
                True
                if x <= 0
                or y <= 0
                or (x + w) >= img.shape[1] - 1
                or (y + h) >= img.shape[0] - 1
                else False
            )

            area = cv2.contourArea(c)
            # If contour is below the min pixel size, don't count it anywhere
            if area < self.sprayCard.min_stain_area_px:
                continue
            # If contour is whole card, don't count it anywhere
            if area >= max_stain_size:
                continue

            # Ammend area based on chosen approximation option
            if (
                self.sprayCard.stain_approximation_method
                == cfg.STAIN_APPROXIMATION_METHODS[0]
            ):
                area = cv2.contourArea(c)
            elif (
                self.sprayCard.stain_approximation_method
                == cfg.STAIN_APPROXIMATION_METHODS[1]
            ):
                c = cv2.minEnclosingCircle(c)
                (x, y), radius = c
                center = (int(x), int(y))
                area = np.pi * (radius**2)
            elif (
                self.sprayCard.stain_approximation_method
                == cfg.STAIN_APPROXIMATION_METHODS[2]
            ):
                if len(c) >= 5:
                    c = cv2.fitEllipse(c)
                    (x, y), (MA, ma), angle = c
                    area = np.pi * MA * ma / 4
                else:
                    area = cv2.contourArea(c)
            elif (
                self.sprayCard.stain_approximation_method
                == cfg.STAIN_APPROXIMATION_METHODS[3]
            ):
                c = cv2.convexHull(c)
                area = cv2.contourArea(c)
            # add stain to layer 1, count for coverage
            contours_edge.append(c)
            self.sprayCard.stain_areas_all_px2.append(area)

            # If contour touches edge, count it for coverage only
            if is_edge:
                continue

            # add stain to layer 2, count for coverage and dd stats
            contours_include.append(c)
            self.sprayCard.stain_areas_valid_px2.append(area)

        if len(contours_include) > 0:
            # Draw edge (layer 1) and include (layer 2) based on type
            if (
                self.sprayCard.stain_approximation_method
                == cfg.STAIN_APPROXIMATION_METHODS[1]
            ):
                for c in contours_edge:
                    (x, y), radius = c
                    center = (int(x), int(y))
                    cv2.circle(img, center, int(radius), color_stain_edge, thickness)
                for c in contours_include:
                    (x, y), radius = c
                    center = (int(x), int(y))
                    cv2.circle(img, center, int(radius), color_stain_counted, thickness)
            elif (
                self.sprayCard.stain_approximation_method
                == cfg.STAIN_APPROXIMATION_METHODS[2]
            ):
                for i, c in enumerate(contours_edge):
                    if type(c) is tuple:
                        cv2.ellipse(img, c, color_stain_edge, thickness)
                    else:
                        cv2.drawContours(
                            img, contours_edge, i, color_stain_edge, thickness
                        )
                for i, c in enumerate(contours_include):
                    if type(c) is tuple:
                        cv2.ellipse(img, c, color_stain_counted, thickness)
                    else:
                        cv2.drawContours(
                            img, contours_include, i, color_stain_counted, thickness
                        )
            else:
                # Draw all contours
                cv2.drawContours(
                    img, contours, -1, color_stain_not_counted, thickness=thickness
                )
                # Draw edge contours overlay (for cov only)
                cv2.drawContours(
                    img, contours_edge, -1, color_stain_edge, thickness=thickness
                )
                # Draw record-worthy contour overlay (for cov and ds calcs)
                cv2.drawContours(
                    img, contours_include, -1, color_stain_counted, thickness=thickness
                )
                if fillShapes:
                    cv2.drawContours(
                        img, contours_include, -1, (255, 255, 255), thickness=1
                    )

        return img
