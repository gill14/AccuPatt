from dataclasses import dataclass
import math
import uuid

import accupatt.config as cfg
import cv2
from skimage.draw import ellipse_perimeter
from skimage.feature import peak_local_max
from skimage.measure import find_contours, label as sklabel, regionprops
from skimage.segmentation import watershed
from scipy import ndimage
import numpy as np
from accupatt.helpers.atomizationModel import AtomizationModel


class SprayCard:
    def __init__(self, id_="", name="", filepath=None):
        # Use id if passed, else create one
        self.id = id_
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
        self.flag_max_stain_limit_reached = False
        self.area_px2 = 0.0
        self.stains = []
        self.stats = SprayCardStats(sprayCard=self)
        # Flag for currency
        self.current = False
        # Temporary working variable
        self.threshold_grayscale_calculated = cfg.get_threshold_grayscale()

    def image_original(self):
        return sprayCardImageFileHandler.read_image_from_file(self)

    def process_image(self, overlay=False, mask=False):
        self.current = True
        scip = SprayCardImageProcessor(sprayCard=self)
        self.threshold_grayscale_calculated = scip.threshold_grayscale_calculated
        scip.process_stains()
        if overlay and mask:
            return scip.get_overlay_image(), scip.get_mask_image()
        elif overlay:
            return scip.get_overlay_image()
        elif mask:
            return scip.get_mask_image()

    def save_image_to_file(self, image):
        return sprayCardImageFileHandler.save_image_to_file(self, image)

    def set_filepath(self, filepath):
        self.filepath = filepath

    def set_threshold_type(self, type_=cfg.THRESHOLD_TYPE__DEFAULT):
        self.threshold_type = type_

    def set_threshold_method_grayscale(
        self, method=cfg.THRESHOLD_GRAYSCALE_METHOD__DEFAULT
    ):
        self.threshold_method_grayscale = method

    def set_threshold_grayscale(self, threshold: int):
        self.threshold_grayscale = threshold

    def set_threshold_color_hue(self, min_=None, max_=None, bandpass=None):
        if min_:
            self.threshold_color_hue_min = min_
        if max_:
            self.threshold_color_hue_max = max_
        if bandpass is not None:
            self.threshold_color_hue_pass = bandpass

    def set_threshold_color_saturation(self, min_=None, max_=None, bandpass=None):
        if min_:
            self.threshold_color_saturation_min = min_
        if max_:
            self.threshold_color_saturation_max = max_
        if bandpass is not None:
            self.threshold_color_saturation_pass = bandpass

    def set_threshold_color_brightness(self, min_=None, max_=None, bandpass=None):
        if min_:
            self.threshold_color_brightness_min = min_
        if max_:
            self.threshold_color_brightness_max = max_
        if bandpass is not None:
            self.threshold_color_brightness_pass = bandpass


@dataclass
class SprayCardStats:

    sprayCard: SprayCard

    dv01: int = 0
    dv05: int = 0
    dv09: int = 0
    gpa: float = 0.0
    lpha: float = 0.0

    # Flag for currency
    current = False

    # Public value/text getters

    def get_dv01(self, text=False):
        if text:
            return str(self.dv01) + " \u03BC" + "m" if self.dv01 > 0 else ""
        else:
            return self.dv01

    def get_dv01_color(self) -> str:
        return AtomizationModel().dsc_color_dv01(dv01=self.dv01)

    def get_dv05(self, text=False):
        if text:
            return str(self.dv05) + " \u03BC" + "m" if self.dv05 > 0 else ""
        else:
            return self.dv05

    def get_dv05_color(self) -> str:
        return AtomizationModel().dsc_color_dv05(dv05=self.dv05)

    def get_dv09(self, text=False):
        if text:
            return str(self.dv09) + " \u03BC" + "m" if self.dv01 > 0 else ""
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

    def get_deposition(self, text=False):
        if cfg.get_unit_rate() == cfg.UNIT_LPHA:
            return self._get_lpha(text)
        else:
            return self._get_gpa(text)

    def _get_gpa(self, text=False):
        if text:
            return f"{self.gpa:.2f}"
        else:
            return self.gpa

    def _get_lpha(self, text=False):
        if text:
            return f"{self.lpha:.2f}"
        else:
            return self.lpha

    def get_percent_coverage(self, text=False):
        stains = [s for s in self.sprayCard.stains if s["is_include"] or s["is_edge"]]
        # Protect from div/0 error or empty stain array
        if self.sprayCard.area_px2 == 0 or len(stains) == 0:
            return 0
        # Calculate coverage as percent of pixel area
        cov = (
            sum([stain["area"] for stain in stains]) / self.sprayCard.area_px2
        ) * 100.0
        if text:
            return f"{cov:.2f}%"
        else:
            return cov

    def get_number_of_stains(self, text=False):
        l = len([s for s in self.sprayCard.stains if s["is_include"]])
        if text:
            return str(l)
        else:
            return l

    def get_card_area_in2(self, text=False):
        area_in2 = self._px2_to_in2(self.sprayCard.area_px2)
        if text:
            return f"{area_in2:.2f} in\u00B2"
        else:
            return area_in2

    def get_stains_per_in2(self, text=False):
        if self.sprayCard.area_px2 == 0:
            return 0
        spsi = round(self.get_number_of_stains() / self.get_card_area_in2())
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
        if not any([s["is_include"] for s in self.sprayCard.stains]):
            self.dv01 = np.nan
            self.dv05 = np.nan
            self.dv09 = np.nan
            self.gpa = np.nan
            self.lpha = np.nan
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
        # Use the vol sum here to set GPA and L/HA
        um3_per_um2 = drop_vol_um3_sum / self._px2_to_um2(self.sprayCard.area_px2)
        self.gpa = um3_per_um2 / cfg.UM3_UM2_PER_GAL_ACRE
        self.lpha = um3_per_um2 / cfg.UM3_UM2_PER_L_HA
        # Reset currency flag
        self.current = True

    # Publicly accessible getter for dd and dv lists, only public so can be used in Composite Card calculations

    def get_droplet_diameters_and_volumes(self) -> tuple[list[float], list[float]]:
        stains = [s for s in self.sprayCard.stains if s["is_include"]]
        # Protect agains empty array
        if not stains:
            return [], []
        drop_dia_um = []
        drop_vol_um3 = []
        # Sort areas into ascending order of size
        stains.sort(key=lambda s: s["area"])
        for stain in stains:
            # Convert px2 to um2
            area_um2 = self._px2_to_um2(stain["area"])
            # Calculate stain diameter assuming circular stain
            dia_um = math.sqrt((4.0 * area_um2) / math.pi)
            # Apply Spread Factors to get originating drop diameter
            drop_dia_um.append(self._stain_dia_to_drop_dia(dia_um))
            # Use drop diameter to calculate drop volume
            vol_um3 = (math.pi * drop_dia_um[-1] ** 3) / 6.0
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
        if sprayCard.filepath is None or not sprayCard.has_image:
            return
        if sprayCard.filepath[-1] == "x":
            return sprayCardImageFileHandler._read_image_from_xlsx(sprayCard=sprayCard)
        elif sprayCard.filepath[-1] == "b":
            return sprayCardImageFileHandler._read_image_from_db(sprayCard=sprayCard)
        return

    def save_image_to_file(sprayCard: SprayCard, image):
        if sprayCard.filepath is None or sprayCard.filepath == "":
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
        self.sprayCard.area_px2 = self.img_src.shape[0] * self.img_src.shape[1]
        # Clear stain lists
        self.sprayCard.stains = []

    def process_stains(self):
        sc = self.sprayCard
        image_t = self.img_thresh
        if self.sprayCard.watershed:
            # Generate markers as local maxima of distance to background
            distance = cv2.distanceTransform(
                image_t, cv2.DIST_L2, cv2.DIST_MASK_PRECISE
            )
            coords = peak_local_max(
                distance,
                min_distance=4,
                threshold_abs=0,
                threshold_rel=0,
                labels=image_t,
            )
            mask = np.zeros(distance.shape, dtype=bool)
            mask[tuple(coords.T)] = True
            markers, _ = ndimage.label(mask)
            labels = watershed(-distance, markers, mask=image_t, watershed_line=True)
        else:
            labels = sklabel(image_t)
        # Iterate over each generated label
        for r in regionprops(labels):
            # Skip background
            if r.label == 0:
                continue
            # Check for mimimum area
            is_too_small = r.area < sc.min_stain_area_px
            # Get bbox vals for offsetting local region
            x1, y1, x2, y2 = r.bbox
            # Check if touching edge
            is_edge = (
                True
                if x1 <= 0
                or y1 <= 0
                or x2 >= image_t.shape[0] - 1
                or y2 >= image_t.shape[1] - 1
                else False
            )
            # Valid unless otherwise declared
            is_include = not is_too_small and not is_edge
            c, area = self._approximate_stain(r, image_t.shape)
            # Convert to cv2 image array, applying offsets (-1 for padding above)
            c_ = []
            for pt in c:
                c_.append([int(pt[1]), int(pt[0])])
            c = np.array(c_).astype(int)

            # Add it to the stains list for later use
            sc.stains.append(
                {
                    "index": r.label,
                    "contour": c,
                    "area": area,
                    "is_too_small": is_too_small,
                    "is_edge": is_edge,
                    "is_include": is_include,
                }
            )

    def get_overlay_image(self):
        sc = self.sprayCard
        img = self.img_src
        cv2.drawContours(
            img,
            [stain["contour"] for stain in sc.stains if stain["is_include"]],
            -1,
            cfg.COLOR_STAIN_OUTLINE[::-1],
            1,
        )
        return img

    def get_mask_image(self):
        sc = self.sprayCard
        img = np.zeros((self.img_src.shape[0], self.img_src.shape[1], 3), np.uint8)
        img[:] = (255, 255, 255)
        cv2.drawContours(
            img,
            [stain["contour"] for stain in sc.stains if stain["is_too_small"]],
            -1,
            cfg.COLOR_STAIN_FILL_ALL[::-1],
            -1,
        )
        cv2.drawContours(
            img,
            [stain["contour"] for stain in sc.stains if stain["is_edge"]],
            -1,
            cfg.COLOR_STAIN_FILL_EDGE[::-1],
            -1,
        )
        cv2.drawContours(
            img,
            [stain["contour"] for stain in sc.stains if stain["is_include"]],
            -1,
            cfg.COLOR_STAIN_FILL_VALID[::-1],
            -1,
        )
        cv2.drawContours(
            img,
            [stain["contour"] for stain in sc.stains if stain["is_include"]],
            -1,
            (255, 255, 255),
            1,
        )
        return img

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

    def _approximate_stain(self, regionprop, image_shape):
        x, y = regionprop.centroid
        x = int(x)
        y = int(y)
        method = self.sprayCard.stain_approximation_method
        if method in [
            cfg.STAIN_APPROXIMATION_ELLIPSE,
            cfg.STAIN_APPROXIMATION_MIN_CIRCLE,
        ]:
            r_radius = int(regionprop.minor_axis_length / 2)
            c_radius = int(regionprop.major_axis_length / 2)
            if method == cfg.STAIN_APPROXIMATION_MIN_CIRCLE:
                radius_max = max(r_radius, c_radius)
                r_radius = radius_max
                c_radius = radius_max
            angle = (
                2 * np.pi
            ) - regionprop.orientation  # To account for regionprops(ccw) to ellipse_perimeter(cw)
            if x < 1 or y < 1 or r_radius < 1 or c_radius < 1:
                return self._get_raw_stain(regionprop)
            rr, cc = ellipse_perimeter(
                x, y, c_radius, r_radius, shape=image_shape, orientation=angle
            )
            sorted_by_angle_to_centroid = np.argsort(
                np.arctan2(rr - np.mean(rr), cc - np.mean(cc))
            )
            rr = rr[sorted_by_angle_to_centroid]
            cc = cc[sorted_by_angle_to_centroid]
            return np.array((rr, cc)).T, np.pi * r_radius * c_radius
        else:
            # No approximation or convex hull
            return self._get_raw_stain(regionprop)

    def _get_raw_stain(self, regionprop):
        x1, y1, x2, y2 = regionprop.bbox
        if (
            self.sprayCard.stain_approximation_method
            == cfg.STAIN_APPROXIMATION_CONVEX_HULL
        ):
            image = regionprop.image_convex
            area = regionprop.area_convex
        else:
            image = regionprop.image
            area = regionprop.area
        # Take local region (bbox) binary image and get the contour of current label
        img_binary_padded = np.pad(image, 1, mode="constant", constant_values=False)
        c = find_contours(
            img_binary_padded, fully_connected="high", positive_orientation="high"
        )[0]
        c[:, 0] += x1 - 1
        c[:, 1] += y1 - 1
        return c, area
