import json
from pathlib import Path
from PyQt6.QtCore import QSettings

VERSION_MAJOR = 2
VERSION_MINOR = 0
VERSION_RELEASE = 15

# For clearning all QSettings
def clear_all_settings():
    QSettings().clear()


# Unit Labels
UNIT_MPH = "mph"
UNIT_KPH = "kph"
UNIT_KN = "kn"
UNIT_FT = "ft"
UNIT_M = "m"
UNIT_IN = "in"
UNIT_CM = "cm"
UNIT_DEG = "°"
UNIT_DEG_F = "°F"
UNIT_DEG_C = "°C"
UNIT_GPA = "gal/a"
UNIT_LPHA = "l/ha"
UNIT_PSI = "psi"
UNIT_BAR = "bar"
UNIT_KPA = "kpa"

# Unit Option Lists
UNITS_LENGTH_LARGE = [UNIT_FT, UNIT_M]
UNITS_LENGTH_SMALL = [UNIT_IN, UNIT_CM]

UNITS_RATE = [UNIT_GPA, UNIT_LPHA]
UNITS_PRESSURE = [UNIT_PSI, UNIT_BAR, UNIT_KPA]

# Math Conversion Constants
UM_PER_IN = 25400.0
FT_PER_M = 3.28084
MPH_PER_KPH = 0.621371
MPH_PER_KN = 1.15078
PSI_PER_BAR = 14.5038
KPA_PER_PSI = 6.89476
UM3_PER_L = 1e15
L_PER_GAL = 3.78541
ACRE_PER_HA = 2.47105
IN_PER_FT = 12.00000
FT2_PER_ACRE = 43560.0
UM3_UM2_PER_GAL_ACRE = 1.06907
UM3_UM2_PER_L_HA = 10.0
AU_PER_PERCENT_16_BIT = 655.35

# Data File

_DATA_FILE_DIR = "data_file_dir"
DATA_FILE_DIR__DEFAULT = str(Path.home())


def get_datafile_dir() -> str:
    return QSettings().value(
        _DATA_FILE_DIR, defaultValue=DATA_FILE_DIR__DEFAULT, type=str
    )


def set_datafile_dir(value: str):
    QSettings().setValue(_DATA_FILE_DIR, value)


# Logo Stuff

_LOGO_INCLUDE_IN_REPORT = "logo_include_in_report"
LOGO_INCLUDE_IN_REPORT__DEFAULT = False


def get_logo_include_in_report() -> bool:
    return QSettings().value(
        _LOGO_INCLUDE_IN_REPORT, defaultValue=LOGO_INCLUDE_IN_REPORT__DEFAULT, type=bool
    )


def set_logo_include_in_report(value: bool):
    QSettings().setValue(_LOGO_INCLUDE_IN_REPORT, value)


_LOGO_PATH = "logo_path"
LOGO_PATH__DEFAULT = ""


def get_logo_path() -> str:
    return QSettings().value(_LOGO_PATH, defaultValue=LOGO_PATH__DEFAULT, type=str)


def set_logo_path(value: str):
    QSettings().setValue(_LOGO_PATH, value)


# Flyin Headers

_FLYIN_NAME = "flyin_name"


def get_flyin_name() -> str:
    return QSettings().value(_FLYIN_NAME, defaultValue="", type=str)


def set_flyin_name(value: str):
    QSettings().setValue(_FLYIN_NAME, value)


_FLYIN_LOCATION = "flyin_location"


def get_flyin_location() -> str:
    return QSettings().value(_FLYIN_LOCATION, defaultValue="", type=str)


def set_flyin_location(value: str):
    QSettings().setValue(_FLYIN_LOCATION, value)


_FLYIN_DATE = "flyin_date"


def get_flyin_date() -> str:
    return QSettings().value(_FLYIN_DATE, defaultValue="", type=str)


def set_flyin_date(value: str):
    QSettings().setValue(_FLYIN_DATE, value)


_FLYIN_ANALYST = "flyin_analyst"


def get_flyin_analyst() -> str:
    return QSettings().value(_FLYIN_ANALYST, defaultValue="", type=str)


def set_flyin_analyst(value: str):
    QSettings().setValue(_FLYIN_ANALYST, value)


# Series Info

_UNIT_WINGSPAN = "unit_wingspan"
UNIT_WINGSPAN__DEFAULT = UNIT_FT


def get_unit_wingspan() -> str:
    return QSettings().value(
        _UNIT_WINGSPAN, defaultValue=UNIT_WINGSPAN__DEFAULT, type=str
    )


def set_unit_wingspan(value: str):
    QSettings().setValue(_UNIT_WINGSPAN, value)


_UNIT_SWATH = "unit_swath"
UNIT_SWATH__DEFAULT = UNIT_FT


def get_unit_swath() -> str:
    return QSettings().value(_UNIT_SWATH, defaultValue=UNIT_SWATH__DEFAULT, type=str)


def set_unit_swath(value: str):
    QSettings().setValue(_UNIT_SWATH, value)


_UNIT_RATE = "unit_rate"
UNIT_RATE__DEFAULT = UNIT_GPA


def get_unit_rate() -> str:
    return QSettings().value(_UNIT_RATE, defaultValue=UNIT_RATE__DEFAULT, type=str)


def set_unit_rate(value: str):
    QSettings().setValue(_UNIT_RATE, value)


_UNIT_PRESSURE = "unit_pressure"
UNIT_PRESSURE__DEFAULT = UNIT_PSI


def get_unit_pressure() -> str:
    return QSettings().value(
        _UNIT_PRESSURE, defaultValue=UNIT_PRESSURE__DEFAULT, type=str
    )


def set_unit_pressure(value: str):
    QSettings().setValue(_UNIT_PRESSURE, value)


_UNIT_BOOM_WIDTH = "unit_boom_width"
UNIT_BOOM_WIDTH__DEFAULT = UNIT_FT


def get_unit_boom_width() -> str:
    return QSettings().value(
        _UNIT_BOOM_WIDTH, defaultValue=UNIT_BOOM_WIDTH__DEFAULT, type=str
    )


def set_unit_boom_width(value: str):
    QSettings().setValue(_UNIT_BOOM_WIDTH, value)


_UNIT_BOOM_DROP = "unit_boom_drop"
UNIT_BOOM_DROP__DEFAULT = UNIT_IN


def get_unit_boom_drop() -> str:
    return QSettings().value(
        _UNIT_BOOM_DROP, defaultValue=UNIT_BOOM_DROP__DEFAULT, type=str
    )


def set_unit_boom_drop(value: str):
    QSettings().setValue(_UNIT_BOOM_DROP, value)


_UNIT_NOZZLE_SPACING = "unit_nozzle_spacing"
UNIT_NOZZLE_SPACING__DEFAULT = UNIT_IN


def get_unit_nozzle_spacing() -> str:
    return QSettings().value(
        _UNIT_NOZZLE_SPACING, defaultValue=UNIT_NOZZLE_SPACING__DEFAULT, type=str
    )


def set_unit_nozzle_spacing(value: str):
    QSettings().setValue(_UNIT_NOZZLE_SPACING, value)


# Pass Observable Data

_NUMBER_OF_PASSES = "number_of_passes"
NUMBER_OF_PASSES__DEFAULT = 3


def get_number_of_passes() -> int:
    return QSettings().value(
        _NUMBER_OF_PASSES, defaultValue=NUMBER_OF_PASSES__DEFAULT, type=int
    )


def set_number_of_passes(value: int):
    QSettings().setValue(_NUMBER_OF_PASSES, value)


_UNIT_GROUND_SPEED = "unit_ground_speed"
UNITS_GROUND_SPEED = [UNIT_MPH, UNIT_KPH, UNIT_KN]
UNIT_GROUND_SPEED__DEFAULT = UNITS_GROUND_SPEED[0]


def get_unit_ground_speed() -> str:
    return QSettings().value(
        _UNIT_GROUND_SPEED, defaultValue=UNIT_GROUND_SPEED__DEFAULT, type=str
    )


def set_unit_ground_speed(value: str):
    QSettings().setValue(_UNIT_GROUND_SPEED, value)


_UNIT_SPRAY_HEIGHT = "unit_spray_height"
UNITS_SPRAY_HEIGHT = UNITS_LENGTH_LARGE
UNIT_SPRAY_HEIGHT__DEFAULT = UNITS_SPRAY_HEIGHT[0]


def get_unit_spray_height() -> str:
    return QSettings().value(
        _UNIT_SPRAY_HEIGHT, defaultValue=UNIT_SPRAY_HEIGHT__DEFAULT, type=str
    )


def set_unit_spray_height(value: str):
    QSettings().setValue(_UNIT_SPRAY_HEIGHT, value)


_UNIT_WIND_SPEED = "unit_wind_speed"
UNITS_WIND_SPEED = [UNIT_MPH, UNIT_KPH]
UNIT_WIND_SPEED__DEFAULT = UNITS_WIND_SPEED[0]


def get_unit_wind_speed() -> str:
    return QSettings().value(
        _UNIT_WIND_SPEED, defaultValue=UNIT_WIND_SPEED__DEFAULT, type=str
    )


def set_unit_wind_speed(value: str):
    QSettings().setValue(_UNIT_WIND_SPEED, value)


_UNIT_TEMPERATURE = "unit_temperature"
UNITS_TEMPERATURE = [UNIT_DEG_F, UNIT_DEG_C]
UNIT_TEMPERATURE__DEFAULT = UNITS_TEMPERATURE[0]


def get_unit_temperature() -> str:
    return QSettings().value(
        _UNIT_TEMPERATURE, defaultValue=UNIT_TEMPERATURE__DEFAULT, type=str
    )


def set_unit_temperature(value: str):
    QSettings().setValue(_UNIT_TEMPERATURE, value)


_UNIT_DATA_LOCATION = "unit_data_location"
UNIT_DATA_LOCATION__DEFAULT = UNIT_FT


def get_unit_data_location() -> str:
    return QSettings().value(
        _UNIT_DATA_LOCATION, defaultValue=UNIT_DATA_LOCATION__DEFAULT, type=str
    )


def set_unit_data_location(value: str):
    QSettings().setValue(_UNIT_DATA_LOCATION, value)


_SIMULATED_ADJASCENT_PASSES = "simulated_adjascent_passes"
SIMULATED_ADJASCENT_PASSES__DEFAULT = 2

def get_simulated_adjascent_passes() -> int:
    return QSettings().value(
        _SIMULATED_ADJASCENT_PASSES,
        defaultValue=SIMULATED_ADJASCENT_PASSES__DEFAULT,
        type=int
    )
    
def set_simulated_adjascent_passes(value: int):
    QSettings().setValue(_SIMULATED_ADJASCENT_PASSES, value)

# String Pattern Manipulation

_CENTER_METHOD = "center_method"
CENTER_METHOD_CENTROID = "Centroid"
CENTER_METHOD_COD = "Center of Distribution"
CENTER_METHOD__DEFAULT = CENTER_METHOD_CENTROID


def get_center_method() -> str:
    return QSettings().value(
        _CENTER_METHOD, defaultValue=CENTER_METHOD__DEFAULT, type=str
    )


def set_center_method(value: str):
    QSettings().setValue(_CENTER_METHOD, value)


_SMOOTH_WINDOW = "smooth_window"


def get_smooth_window() -> float:
    return QSettings().value(_SMOOTH_WINDOW, defaultValue=4, type=float)


def set_smooth_window(value: float):
    QSettings().setValue(_SMOOTH_WINDOW, value)


_SMOOTH_ORDER = "smooth_order"


def get_smooth_order() -> int:
    return QSettings().value(_SMOOTH_ORDER, defaultValue=3, type=int)


def set_smooth_order(value: int):
    QSettings().setValue(_SMOOTH_ORDER, value)


# String Plot Options

_STRING_PLOT_AVERAGE_DASH_OVERLAY = "string_plot_average_dash_overlay"
STRING_PLOT_AVERAGE_DASH_OVERLAY__DEFUALT = True


def get_string_plot_average_dash_overlay() -> bool:
    return QSettings().value(
        _STRING_PLOT_AVERAGE_DASH_OVERLAY,
        defaultValue=STRING_PLOT_AVERAGE_DASH_OVERLAY__DEFUALT,
        type=bool,
    )


def set_string_plot_average_dash_overlay(value: bool):
    QSettings().setValue(_STRING_PLOT_AVERAGE_DASH_OVERLAY, value)


_STRING_PLOT_AVERAGE_DASH_OVERLAY_METHOD = "string_plot_average_dash_overlay_method"
DASH_OVERLAY_METHOD_ISHA = "ISHA"
DASH_OVERLAY_METHOD_AVERAGE = "Average"
STRING_PLOT_AVERAGE_DASH_OVERLAY_METHOD__DEFAULT = DASH_OVERLAY_METHOD_ISHA


def get_string_plot_average_dash_overlay_method() -> str:
    return QSettings().value(
        _STRING_PLOT_AVERAGE_DASH_OVERLAY_METHOD,
        defaultValue=STRING_PLOT_AVERAGE_DASH_OVERLAY_METHOD__DEFAULT,
        type=str,
    )


def set_string_plot_average_dash_overlay_method(value: str):
    QSettings().setValue(_STRING_PLOT_AVERAGE_DASH_OVERLAY_METHOD, value)

_STRING_SIMULATION_VIEW_WINDOW = "string_simulation_view_window"
STRING_SIMULATION_VIEW_WINDOW_ONE = "one"
STRING_SIMULATION_VIEW_WINDOW_ALL = "all"


def get_string_simulation_view_window() -> str:
    return QSettings().value(
        _STRING_SIMULATION_VIEW_WINDOW,
        defaultValue=STRING_SIMULATION_VIEW_WINDOW_ONE,
        type=str,
    )


def set_string_simulation_view_window(value=str):
    QSettings().setValue(_STRING_SIMULATION_VIEW_WINDOW, value)


# String Drive

STRING_DRIVE_FWD_START = "AD+\r"
STRING_DRIVE_FWD_STOP = "AD\r"
STRING_DRIVE_REV_START = "BD-\r"
STRING_DRIVE_REV_STOP = "BD\r"

_STRING_DRIVE_PORT = "string_drive_port"
STRING_DRIVE_PORT__DEFAULT = ""


def get_string_drive_port() -> str:
    return QSettings().value(
        _STRING_DRIVE_PORT, defaultValue=STRING_DRIVE_PORT__DEFAULT, type=str
    )


def set_string_drive_port(value: str):
    QSettings().setValue(_STRING_DRIVE_PORT, value)


_STRING_LENGTH = "string_length"
STRING_LENGTH__DEFAULT = 150.0


def get_string_length() -> float:
    return QSettings().value(
        _STRING_LENGTH, defaultValue=STRING_LENGTH__DEFAULT, type=float
    )


def set_string_length(value: float):
    QSettings().setValue(_STRING_LENGTH, value)


_STRING_SPEED = "string_speed"
STRING_SPEED__DEFAULT = 1.71


def get_string_speed() -> float:
    return QSettings().value(
        _STRING_SPEED, defaultValue=STRING_SPEED__DEFAULT, type=float
    )


def set_string_speed(value: float):
    QSettings().setValue(_STRING_SPEED, value)


# Spectrometer

_DEFINED_DYES = "defined_dyes"


def gen_dye_dict(name, w_ex, w_em, it, bx) -> dict:
    dye = dict()
    dye["name"] = name
    dye["wavelength_excitation"] = w_ex
    dye["wavelength_emission"] = w_em
    dye["integration_time_milliseconds"] = it
    dye["boxcar_width"] = bx
    return dye


DEFINED_DYES__DEFAULT = [
    gen_dye_dict("Rhodamine WT", 525, 575, 100, 0),
    gen_dye_dict("Pyranine", 425, 495, 100, 0),
    gen_dye_dict("Topline", 425, 502, 100, 0),
    gen_dye_dict("PTSA", 365, 410, 100, 0),
]


def get_defined_dyes() -> list[dict]:
    # set_defined_dyes(json.dumps(DEFINED_DYES__DEFAULT))
    dyes = QSettings().value(
        _DEFINED_DYES,
        defaultValue=json.dumps(DEFINED_DYES__DEFAULT),
        type=str,
    )
    dyes_list: list[dict] = json.loads(dyes)
    return dyes_list


def set_defined_dyes(value: str):
    QSettings().setValue(_DEFINED_DYES, value)


_DEFINED_DYE = "defined_dye"
DEFINED_DYE__DEFAULT = DEFINED_DYES__DEFAULT[0]["name"]


def get_defined_dye() -> str:
    return QSettings().value(_DEFINED_DYE, defaultValue=DEFINED_DYE__DEFAULT, type=str)


def set_defined_dye(value: str):
    QSettings().setValue(_DEFINED_DYE, value)

_SPECTROMETER_DISPLAY_UNIT = "spectrometer_display_units"
SPECTROMETER_DISPLAY_UNIT_RELATIVE = "Relative (%)"
SPECTROMETER_DISPLAY_UNIT_ABSOLUTE = "Absolute"
SPECTROMETER_DISPLAY_UNITS = [
    SPECTROMETER_DISPLAY_UNIT_RELATIVE,
    SPECTROMETER_DISPLAY_UNIT_ABSOLUTE
]
SPECTROMETER_DISPLAY_UNIT__DEFAULT = SPECTROMETER_DISPLAY_UNITS[0]

def get_spectrometer_display_unit() -> str:
    return QSettings().value(
        _SPECTROMETER_DISPLAY_UNIT, defaultValue=SPECTROMETER_DISPLAY_UNIT__DEFAULT, type=str
    )
    
def set_spectrometer_display_unit(value: str):
    QSettings().setValue(_SPECTROMETER_DISPLAY_UNIT, value)


# SprayCard Image Loading Operations / Attributes

_IMAGE_LOAD_DIR = "image_load_dir"
IMAGE_LOAD_DIR__DEFAULT = str(Path.home())


def get_image_load_dir() -> str:
    return QSettings().value(
        _IMAGE_LOAD_DIR, defaultValue=IMAGE_LOAD_DIR__DEFAULT, type=str
    )


def set_image_load_dir(value: str):
    QSettings().setValue(_IMAGE_LOAD_DIR, value)


_IMAGE_LOAD_METHOD = "image_load_method"
IMAGE_LOAD_METHODS = ["One File Per Card", "One File, Multiple Cards"]
IMAGE_LOAD_METHOD__DEFAULT = IMAGE_LOAD_METHODS[1]


def get_image_load_method() -> str:
    return QSettings().value(
        _IMAGE_LOAD_METHOD, defaultValue=IMAGE_LOAD_METHOD__DEFAULT, type=str
    )


def set_image_load_method(value: str):
    QSettings().setValue(_IMAGE_LOAD_METHOD, value)


_IMAGE_FLIP_X = "image_flip_x"
IMAGE_FLIP_X__DEFAULT = False


def get_image_flip_x() -> bool:
    return QSettings().value(
        _IMAGE_FLIP_X, defaultValue=IMAGE_FLIP_X__DEFAULT, type=bool
    )


def set_image_flip_x(value: bool):
    QSettings().setValue(_IMAGE_FLIP_X, value)


_IMAGE_FLIP_Y = "image_flip_y"
IMAGE_FLIP_Y__DEFAULT = False


def get_image_flip_y() -> bool:
    return QSettings().value(
        _IMAGE_FLIP_Y, defaultValue=IMAGE_FLIP_Y__DEFAULT, type=bool
    )


def set_image_flip_y(value: bool):
    QSettings().setValue(_IMAGE_FLIP_Y, value)


_ROI_ACQUISITION_ORIENTATION = "roi_acquisition_orientation"
ROI_ACQUISITION_ORIENTATIONS = ["Horizontal", "Vertical"]
ROI_ACQUISITION_ORIENTATION__DEFAULT = ROI_ACQUISITION_ORIENTATIONS[0]


def get_image_roi_acquisition_orientation() -> str:
    return QSettings().value(
        _ROI_ACQUISITION_ORIENTATION,
        defaultValue=ROI_ACQUISITION_ORIENTATION__DEFAULT,
        type=str,
    )


def set_image_roi_acquisition_orientation(value: str):
    QSettings().setValue(_ROI_ACQUISITION_ORIENTATION, value)


_ROI_ACQUISITION_ORDER = "roi_acquisition_order"
ROI_ACQUISITION_ORDERS = ["Increasing", "Decreasing"]
ROI_ACQUISITION_ORDER__DEFAULT = ROI_ACQUISITION_ORDERS[0]


def get_image_roi_acquisition_order() -> str:
    return QSettings().value(
        _ROI_ACQUISITION_ORDER, defaultValue=ROI_ACQUISITION_ORDER__DEFAULT, type=str
    )


def set_image_roi_acquisition_order(value: str):
    QSettings().setValue(_ROI_ACQUISITION_ORDER, value)


_ROI_SCALE = "roi_scale"
ROI_SCALES = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
ROI_SCALE__DEFAULT = ROI_SCALES[6]


def get_image_roi_scale() -> int:
    return QSettings().value(_ROI_SCALE, defaultValue=ROI_SCALE__DEFAULT, type=int)


def set_image_roi_scale(value: int):
    QSettings().setValue(_ROI_SCALE, value)


_IMAGE_DPI = "image_dpi"
IMAGE_DPI_OPTIONS = [300, 600, 1200, 2400]
IMAGE_DPI__DEFAULT = 600


def get_image_dpi() -> int:
    return QSettings().value(_IMAGE_DPI, defaultValue=IMAGE_DPI__DEFAULT, type=int)


def set_image_dpi(value: int):
    QSettings().setValue(_IMAGE_DPI, value)


# SprayCard Image Processing - Thresholding

_THRESHOLD_TYPE = "threshold_type"
THRESHOLD_TYPE_GRAYSCALE = "Grayscale"
THRESHOLD_TYPE_HSB = "HSB"
THRESHOLD_TYPES = [THRESHOLD_TYPE_GRAYSCALE, THRESHOLD_TYPE_HSB]
THRESHOLD_TYPE__DEFAULT = THRESHOLD_TYPES[0]


def get_threshold_type() -> str:
    return QSettings().value(
        _THRESHOLD_TYPE, defaultValue=THRESHOLD_TYPE__DEFAULT, type=str
    )


def set_threshold_type(value: str):
    QSettings().setValue(_THRESHOLD_TYPE, value)


_THRESHOLD_GRAYSCALE = "threshold_grayscale"
THRESHOLD_GRAYSCALE__DEFAULT = 152


def get_threshold_grayscale() -> int:
    return QSettings().value(
        _THRESHOLD_GRAYSCALE, defaultValue=THRESHOLD_GRAYSCALE__DEFAULT, type=int
    )


def set_threshold_grayscale(value: int):
    QSettings().setValue(_THRESHOLD_GRAYSCALE, value)


_THRESHOLD_GRAYSCALE_METHOD = "threshold_grayscale_method"
THRESHOLD_GRAYSCALE_METHOD_AUTO = "Auto"
THRESHOLD_GRAYSCALE_METHOD_MANUAL = "Manual"
THRESHOLD_GRAYSCALE_METHODS = [
    THRESHOLD_GRAYSCALE_METHOD_AUTO,
    THRESHOLD_GRAYSCALE_METHOD_MANUAL,
]
THRESHOLD_GRAYSCALE_METHOD__DEFAULT = THRESHOLD_GRAYSCALE_METHODS[0]


def get_threshold_grayscale_method() -> str:
    return QSettings().value(
        _THRESHOLD_GRAYSCALE_METHOD,
        defaultValue=THRESHOLD_GRAYSCALE_METHOD__DEFAULT,
        type=str,
    )


def set_threshold_grayscale_method(value: str):
    QSettings().setValue(_THRESHOLD_GRAYSCALE_METHOD, value)


_THRESHOLD_HSB_HUE_MIN = "threshold_hsb_hue_min"
THRESHOLD_HSB_HUE_MIN__DEFAULT = 140


def get_threshold_hsb_hue_min() -> int:
    return QSettings().value(
        _THRESHOLD_HSB_HUE_MIN, defaultValue=THRESHOLD_HSB_HUE_MIN__DEFAULT, type=int
    )


def set_threshold_hsb_hue_min(value: int):
    QSettings().setValue(_THRESHOLD_HSB_HUE_MIN, value)


_THRESHOLD_HSB_HUE_MAX = "threshold_hsb_hue_max"
THRESHOLD_HSB_HUE_MAX__DEFAULT = 170


def get_threshold_hsb_hue_max() -> int:
    return QSettings().value(
        _THRESHOLD_HSB_HUE_MAX, defaultValue=THRESHOLD_HSB_HUE_MAX__DEFAULT, type=int
    )


def set_threshold_hsb_hue_max(value: int):
    QSettings().setValue(_THRESHOLD_HSB_HUE_MAX, value)


_THRESHOLD_HSB_HUE_PASS = "threshold_hsb_hue_pass"
THRESHOLD_HSB_HUE_PASS__DEFAULT = True


def get_threshold_hsb_hue_pass() -> bool:
    return QSettings().value(
        _THRESHOLD_HSB_HUE_PASS, defaultValue=THRESHOLD_HSB_HUE_PASS__DEFAULT, type=bool
    )


def set_threshold_hsb_hue_pass(value: bool):
    QSettings().setValue(_THRESHOLD_HSB_HUE_PASS, value)


_THRESHOLD_HSB_SATURATION_MIN = "threshold_hsb_saturation_min"
THRESHOLD_HSB_SATURATION_MIN__DEFAULT = 30


def get_threshold_hsb_saturation_min() -> int:
    return QSettings().value(
        _THRESHOLD_HSB_SATURATION_MIN,
        defaultValue=THRESHOLD_HSB_SATURATION_MIN__DEFAULT,
        type=int,
    )


def set_threshold_hsb_saturation_min(value: int):
    QSettings().setValue(_THRESHOLD_HSB_SATURATION_MIN, value)


_THRESHOLD_HSB_SATURATION_MAX = "threshold_hsb_saturation_max"
THRESHOLD_HSB_SATURATION_MAX__DEFAULT = 255


def get_threshold_hsb_saturation_max() -> int:
    return QSettings().value(
        _THRESHOLD_HSB_SATURATION_MAX,
        defaultValue=THRESHOLD_HSB_SATURATION_MAX__DEFAULT,
        type=int,
    )


def set_threshold_hsb_saturation_max(value: int):
    QSettings().setValue(_THRESHOLD_HSB_SATURATION_MAX, value)


_THRESHOLD_HSB_SATURATION_PASS = "threshold_hsb_saturation_pass"
THRESHOLD_HSB_SATURATION_PASS__DEFAULT = True


def get_threshold_hsb_saturation_pass() -> bool:
    return QSettings().value(
        _THRESHOLD_HSB_SATURATION_PASS,
        defaultValue=THRESHOLD_HSB_SATURATION_PASS__DEFAULT,
        type=bool,
    )


def set_threshold_hsb_saturation_pass(value: bool):
    QSettings().setValue(_THRESHOLD_HSB_SATURATION_PASS, value)


_THRESHOLD_HSB_BRIGHTNESS_MIN = "threshold_hsb_brightness_min"
THRESHOLD_HSB_BRIGHTNESS_MIN__DEFAULT = 0


def get_threshold_hsb_brightness_min() -> int:
    return QSettings().value(
        _THRESHOLD_HSB_BRIGHTNESS_MIN,
        defaultValue=THRESHOLD_HSB_BRIGHTNESS_MIN__DEFAULT,
        type=int,
    )


def set_threshold_hsb_brightness_min(value: int):
    QSettings().setValue(_THRESHOLD_HSB_BRIGHTNESS_MIN, value)


_THRESHOLD_HSB_BRIGHTNESS_MAX = "threshold_hsb_brightness_max"
THRESHOLD_HSB_BRIGHTNESS_MAX__DEFAULT = 255


def get_threshold_hsb_brightness_max() -> int:
    return QSettings().value(
        _THRESHOLD_HSB_BRIGHTNESS_MAX,
        defaultValue=THRESHOLD_HSB_BRIGHTNESS_MAX__DEFAULT,
        type=int,
    )


def set_threshold_hsb_brightness_max(value: int):
    QSettings().setValue(_THRESHOLD_HSB_BRIGHTNESS_MAX, value)


_THRESHOLD_HSB_BRIGHTNESS_PASS = "threshold_hsb_brightness_pass"
THRESHOLD_HSB_BRIGHTNESS_PASS__DEFAULT = True


def get_threshold_hsb_brightness_pass() -> bool:
    return QSettings().value(
        _THRESHOLD_HSB_BRIGHTNESS_PASS,
        defaultValue=THRESHOLD_HSB_BRIGHTNESS_PASS__DEFAULT,
        type=bool,
    )


def set_threshold_hsb_brightness_pass(value: bool):
    QSettings().setValue(_THRESHOLD_HSB_BRIGHTNESS_PASS, value)


# SprayCard Image Processing - Options

_WATERSHED = "watershed"
WATERSHED__DEFAULT = True


def get_watershed() -> bool:
    return QSettings().value(_WATERSHED, defaultValue=WATERSHED__DEFAULT, type=bool)


def set_watershed(value: bool):
    QSettings().setValue(_WATERSHED, value)


_MIN_STAIN_AREA_PX = "min_stain_area_px"
MIN_STAIN_AREA_PX = 4


def get_min_stain_area_px() -> int:
    return QSettings().value(
        _MIN_STAIN_AREA_PX, defaultValue=MIN_STAIN_AREA_PX, type=int
    )


def set_min_stain_area_px(value: int):
    QSettings().setValue(_MIN_STAIN_AREA_PX, value)


_STAIN_APPROXIMATION_METHOD = "stain_approximation_method"
STAIN_APPROXIMATION_NONE = "None"
STAIN_APPROXIMATION_MIN_CIRCLE = "Minimum Enclosing Circle"
STAIN_APPROXIMATION_ELLIPSE = "Fit Ellipse"
STAIN_APPROXIMATION_CONVEX_HULL = "Convex Hull"
STAIN_APPROXIMATION_METHODS = [
    STAIN_APPROXIMATION_NONE,
    STAIN_APPROXIMATION_MIN_CIRCLE,
    STAIN_APPROXIMATION_ELLIPSE,
    STAIN_APPROXIMATION_CONVEX_HULL,
]
STAIN_APPROXIMATION_METHOD__DEFAULT = STAIN_APPROXIMATION_NONE


def get_stain_approximation_method() -> str:
    return QSettings().value(
        _STAIN_APPROXIMATION_METHOD,
        defaultValue=STAIN_APPROXIMATION_METHOD__DEFAULT,
        type=str,
    )


def set_stain_approximation_method(value: str):
    QSettings().setValue(_STAIN_APPROXIMATION_METHOD, value)


_MAX_STAIN_COUNT = "max_stain_count"
MAX_STAIN_COUNT = 3000


def get_max_stain_count() -> int:
    return QSettings().value(_MAX_STAIN_COUNT, defaultValue=MAX_STAIN_COUNT, type=int)


def set_max_stain_count(value: int):
    QSettings().setValue(_MAX_STAIN_COUNT, value)


# SprayCard Processed Image Colors

COLOR_STAIN_OUTLINE = (226, 43, 138)  # Red-Pink
COLOR_STAIN_FILL_ALL = (255, 0, 0)  # Red
COLOR_STAIN_FILL_EDGE = (238, 130, 238)  # Violet
COLOR_STAIN_FILL_VALID = (0, 0, 255)  # Blue

# SprayCard Spread Factors

_SPREAD_FACTOR_A = "spread_factor_a"
SPREAD_FACTOR_A__DEFAULT = 0.0000


def get_spread_factor_a() -> float:
    return QSettings().value(
        _SPREAD_FACTOR_A, defaultValue=SPREAD_FACTOR_A__DEFAULT, type=float
    )


def set_spread_factor_a(value: float):
    QSettings().setValue(_SPREAD_FACTOR_A, value)


_SPREAD_FACTOR_B = "spread_factor_b"
SPREAD_FACTOR_B__DEFAULT = 0.0009


def get_spread_factor_b() -> float:
    return QSettings().value(
        _SPREAD_FACTOR_B, defaultValue=SPREAD_FACTOR_B__DEFAULT, type=float
    )


def set_spread_factor_b(value: float):
    QSettings().setValue(_SPREAD_FACTOR_B, value)


_SPREAD_FACTOR_C = "spread_factor_c"
SPREAD_FACTOR_C__DEFAULT = 1.6333


def get_spread_factor_c() -> float:
    return QSettings().value(
        _SPREAD_FACTOR_C, defaultValue=SPREAD_FACTOR_C__DEFAULT, type=float
    )


def set_spread_factor_c(value: float):
    QSettings().setValue(_SPREAD_FACTOR_C, value)


_SPREAD_METHOD = "spread_factor_equation"
SPREAD_METHOD_NONE = "None"
SPREAD_METHOD_DIRECT = "Direct"
SPREAD_METHOD_ADAPTIVE = "Adaptive"
SPREAD_METHODS = [SPREAD_METHOD_NONE, SPREAD_METHOD_DIRECT, SPREAD_METHOD_ADAPTIVE]
SPREAD_METHOD__DEFAULT = SPREAD_METHODS[2]


def get_spread_factor_equation() -> str:
    return QSettings().value(
        _SPREAD_METHOD, defaultValue=SPREAD_METHOD__DEFAULT, type=str
    )


def set_spread_factor_equation(value: str):
    QSettings().setValue(_SPREAD_METHOD, value)


# SprayCard Plot Options

_CARD_PLOT_Y_AXIS = "card_plot_y_axis"
CARD_PLOT_Y_AXIS_COVERAGE = "coverage"
CARD_PLOT_Y_AXIS_DEPOSITION = "deposition"
CARD_PLOT_Y_AXIS__DEFAULT = CARD_PLOT_Y_AXIS_COVERAGE


def get_card_plot_y_axis() -> str:
    return QSettings().value(
        _CARD_PLOT_Y_AXIS, defaultValue=CARD_PLOT_Y_AXIS__DEFAULT, type=str
    )


def set_card_plot_y_axis(value: str):
    QSettings().setValue(_CARD_PLOT_Y_AXIS, value)


_CARD_PLOT_SHADING = "card_plot_shading"
CARD_PLOT_SHADING__DEFAULT = True


def get_card_plot_shading() -> bool:
    return QSettings().value(
        _CARD_PLOT_SHADING, defaultValue=CARD_PLOT_SHADING__DEFAULT, type=bool
    )


def set_card_plot_shading(value: bool):
    QSettings().setValue(_CARD_PLOT_SHADING, value)


_CARD_PLOT_SHADING_METHOD = "card_plot_shading_method"
CARD_PLOT_SHADING_METHOD_DSC = "DSC"
CARD_PLOT_SHADING_METHOD_DEPOSITION_AVERAGE = "Average Deposition"
CARD_PLOT_SHADING_METHOD_DEPOSITION_TARGET = "Target Deposition"
CARD_PLOT_SHADING_METHOD__DEFAULT = CARD_PLOT_SHADING_METHOD_DSC


def get_card_plot_shading_method() -> str:
    return QSettings().value(
        _CARD_PLOT_SHADING_METHOD,
        defaultValue=CARD_PLOT_SHADING_METHOD__DEFAULT,
        type=str,
    )


def set_card_plot_shading_method(value: str):
    QSettings().setValue(_CARD_PLOT_SHADING_METHOD, value)


_CARD_PLOT_SHADING_INTERPOLATE = "card_plot_shading_interpolate"
CARD_PLOT_SHADING_INTERPOLATE__DEFAULT = True


def get_card_plot_shading_interpolate() -> bool:
    return QSettings().value(
        _CARD_PLOT_SHADING_INTERPOLATE,
        defaultValue=CARD_PLOT_SHADING_INTERPOLATE__DEFAULT,
        type=bool,
    )


def set_card_plot_shading_interpolate(value: bool):
    QSettings().setValue(_CARD_PLOT_SHADING_INTERPOLATE, value)


_CARD_PLOT_AVERAGE_DASH_OVERLAY = "card_plot_average_dash_overlay"
CARD_PLOT_AVERAGE_DASH_OVERLAY__DEFUALT = True


def get_card_plot_average_dash_overlay() -> bool:
    return QSettings().value(
        _CARD_PLOT_AVERAGE_DASH_OVERLAY,
        defaultValue=CARD_PLOT_AVERAGE_DASH_OVERLAY__DEFUALT,
        type=bool,
    )


def set_card_plot_average_dash_overlay(value: bool):
    QSettings().setValue(_CARD_PLOT_AVERAGE_DASH_OVERLAY, value)


_CARD_PLOT_AVERAGE_DASH_OVERLAY_METHOD = "card_plot_average_dash_overlay_method"
DASH_OVERLAY_METHOD_ISHA = "ISHA"
DASH_OVERLAY_METHOD_AVERAGE = "Average"
CARD_PLOT_AVERAGE_DASH_OVERLAY_METHOD__DEFAULT = DASH_OVERLAY_METHOD_ISHA


def get_card_plot_average_dash_overlay_method() -> str:
    return QSettings().value(
        _CARD_PLOT_AVERAGE_DASH_OVERLAY_METHOD,
        defaultValue=CARD_PLOT_AVERAGE_DASH_OVERLAY_METHOD__DEFAULT,
        type=str,
    )


def set_card_plot_average_dash_overlay_method(value: str):
    QSettings().setValue(_CARD_PLOT_AVERAGE_DASH_OVERLAY_METHOD, value)


_CARD_SIMULATION_VIEW_WINDOW = "card_simulation_view_window"
CARD_SIMULATION_VIEW_WINDOW_ONE = "one"
CARD_SIMULATION_VIEW_WINDOW_ALL = "all"


def get_card_simulation_view_window() -> str:
    return QSettings().value(
        _CARD_SIMULATION_VIEW_WINDOW,
        defaultValue=CARD_SIMULATION_VIEW_WINDOW_ONE,
        type=str,
    )


def set_card_simulation_view_window(value=str):
    QSettings().setValue(_CARD_SIMULATION_VIEW_WINDOW, value)


# SprayCard Prefab Sets

_CARD_DEFINED_SETS = "card_defined_sets"


def get_card_set_base(set_name: str, card_names: list[str]) -> dict:
    base = dict()
    base["set_name"] = set_name
    base["card_name"] = card_names
    q = len(card_names)
    base[_THRESHOLD_TYPE] = [THRESHOLD_TYPE_HSB] * q
    base[_THRESHOLD_GRAYSCALE_METHOD] = [get_threshold_grayscale_method()] * q
    base[_THRESHOLD_GRAYSCALE] = [get_threshold_grayscale()] * q
    base[_THRESHOLD_HSB_HUE_MIN] = [get_threshold_hsb_hue_min()] * q
    base[_THRESHOLD_HSB_HUE_MAX] = [get_threshold_hsb_hue_max()] * q
    base[_THRESHOLD_HSB_HUE_PASS] = [get_threshold_hsb_hue_pass()] * q
    base[_THRESHOLD_HSB_SATURATION_MIN] = [get_threshold_hsb_saturation_min()] * q
    base[_THRESHOLD_HSB_SATURATION_MAX] = [get_threshold_hsb_saturation_max()] * q
    base[_THRESHOLD_HSB_SATURATION_PASS] = [get_threshold_hsb_saturation_pass()] * q
    base[_THRESHOLD_HSB_BRIGHTNESS_MIN] = [get_threshold_hsb_brightness_min()] * q
    base[_THRESHOLD_HSB_BRIGHTNESS_MAX] = [get_threshold_hsb_brightness_max()] * q
    base[_THRESHOLD_HSB_BRIGHTNESS_PASS] = [get_threshold_hsb_brightness_pass()] * q
    base[_WATERSHED] = [get_watershed()] * q
    base[_MIN_STAIN_AREA_PX] = [get_min_stain_area_px()] * q
    base[_STAIN_APPROXIMATION_METHOD] = [get_stain_approximation_method()] * q
    base[_SPREAD_METHOD] = [get_spread_factor_equation()] * q
    base[_SPREAD_FACTOR_A] = [get_spread_factor_a()] * q
    base[_SPREAD_FACTOR_B] = [get_spread_factor_b()] * q
    base[_SPREAD_FACTOR_C] = [get_spread_factor_c()] * q
    return base


def get_card_set_safe_white():
    set_name = "SAFE Fly-In (White Cards)"
    card_names = [
        "L-32",
        "L-24",
        "L-16",
        "L-8",
        "Center",
        "R-8",
        "R-16",
        "R-24",
        "R-32",
    ]
    base = get_card_set_base(set_name, card_names)
    base["location"] = [-32, -24, -16, -8, 0, 8, 16, 24, 32]
    base["location_unit"] = [UNIT_FT] * len(base["location"])
    base[_THRESHOLD_TYPE] = [THRESHOLD_TYPE_HSB] * len(base["location"])
    return base


def get_card_set_safe_wsp():
    set_name = "SAFE Fly-In (WSP)"
    card_names = [
        "L-32",
        "L-24",
        "L-16",
        "L-8",
        "Center",
        "R-8",
        "R-16",
        "R-24",
        "R-32",
    ]
    base = get_card_set_base(set_name, card_names)
    base["location"] = [-32, -24, -16, -8, 0, 8, 16, 24, 32]
    base["location_unit"] = [UNIT_FT] * len(base["location"])
    base[_THRESHOLD_TYPE] = [THRESHOLD_TYPE_GRAYSCALE] * len(base["location"])
    return base


CARD_DEFINED_SETS__DEFAULT = [get_card_set_safe_wsp(), get_card_set_safe_white()]


def get_card_defined_sets() -> str:
    sets = QSettings().value(
        _CARD_DEFINED_SETS,
        defaultValue=json.dumps(CARD_DEFINED_SETS__DEFAULT),
        type=str,
    )
    sets_list: list[dict] = json.loads(sets)
    if any([_THRESHOLD_GRAYSCALE not in s.keys() for s in sets_list]):
        temporary_converter()
        sets = QSettings().value(
            _CARD_DEFINED_SETS,
            defaultValue=json.dumps(CARD_DEFINED_SETS__DEFAULT),
            type=str,
        )
    return sets


def temporary_converter():
    print("Converting...")
    old_sets = QSettings().value(
        _CARD_DEFINED_SETS,
        defaultValue=json.dumps(CARD_DEFINED_SETS__DEFAULT),
        type=str,
    )
    old_sets_list: list[dict] = json.loads(old_sets)
    new_sets_list = []
    for set in old_sets_list:
        set_name = set["set_name"]
        card_names = set["card_name"]
        base = get_card_set_base(set_name, card_names)
        base["location"] = set["location"]
        base["location_unit"] = set["location_unit"]
        base["threshold_type"] = set["threshold_type"]
        new_sets_list.append(base)
    new_sets = json.dumps(new_sets_list)
    set_card_defined_sets(new_sets)


def set_card_defined_sets(value: str):
    QSettings().setValue(_CARD_DEFINED_SETS, value)


_CARD_DEFINED_SET = "card_defined_set"
CARD_DEFINED_SET__DEFAULT = get_card_set_safe_white()["set_name"]


def get_card_defined_set() -> str:
    return QSettings().value(
        _CARD_DEFINED_SET, defaultValue=CARD_DEFINED_SET__DEFAULT, type=str
    )


def set_card_defined_set(value: str):
    QSettings().setValue(_CARD_DEFINED_SET, value)


# Report - SprayCard Params

_REPORT_CARD_INCLUDE_IMAGES = "report_card_include_images"
REPORT_CARD_INCLUDE_IMAGES__DEFAULT = True


def get_report_card_include_images() -> bool:
    return QSettings().value(
        _REPORT_CARD_INCLUDE_IMAGES,
        defaultValue=REPORT_CARD_INCLUDE_IMAGES__DEFAULT,
        type=bool,
    )


def set_report_card_include_images(value: bool):
    QSettings().setValue(_REPORT_CARD_INCLUDE_IMAGES, value)


_REPORT_CARD_IMAGE_TYPE = "report_card_image_type"
REPORT_CARD_IMAGE_TYPE_ORIGINAL = "original"
REPORT_CARD_IMAGE_TYPE_OUTLINE = "outline"
REPORT_CARD_IMAGE_TYPE_MASK = "mask"
REPORT_CARD_IMAGE_TYPES = [
    REPORT_CARD_IMAGE_TYPE_ORIGINAL,
    REPORT_CARD_IMAGE_TYPE_OUTLINE,
    REPORT_CARD_IMAGE_TYPE_MASK,
]
REPORT_CARD_IMAGE_TYPE__DEFAULT = REPORT_CARD_IMAGE_TYPE_ORIGINAL


def get_report_card_image_type() -> str:
    return QSettings().value(
        _REPORT_CARD_IMAGE_TYPE, defaultValue=REPORT_CARD_IMAGE_TYPE__DEFAULT, type=str
    )


def set_report_card_image_type(value: str):
    QSettings().setValue(_REPORT_CARD_IMAGE_TYPE, value)


_REPORT_CARD_IMAGE_PER_PAGE = "report_card_image_per_page"
REPORT_CARD_IMAGE_PER_PAGE__DEFAULT = 9


def get_report_card_image_per_page() -> int:
    return QSettings().value(
        _REPORT_CARD_IMAGE_PER_PAGE,
        defaultValue=REPORT_CARD_IMAGE_PER_PAGE__DEFAULT,
        type=int,
    )


def set_report_card_image_per_page(value: int):
    QSettings().setValue(_REPORT_CARD_IMAGE_PER_PAGE, value)
