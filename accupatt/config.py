import json
from pathlib import Path
from PyQt6.QtCore import QSettings

VERSION_MAJOR = 2
VERSION_MINOR = 0
VERSION_RELEASE = 9

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

# Data File

_DATA_FILE_DIR = "data_file_dir"
DATA_FILE_DIR__DEFAULT = str(Path.home())


def get_datafile_dir() -> str:
    return QSettings().value(
        _DATA_FILE_DIR, defaultValue=DATA_FILE_DIR__DEFAULT, type=str
    )


def set_datafile_dir(value: str):
    QSettings().setValue(_DATA_FILE_DIR, value)


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


_STRING_SMOOTH_WINDOW = "string_smooth_window"


def get_string_smooth_window() -> float:
    return QSettings().value(_STRING_SMOOTH_WINDOW, defaultValue=4, type=float)


def set_string_smooth_window(value: float):
    QSettings().setValue(_STRING_SMOOTH_WINDOW, value)


_STRING_SMOOTH_ORDER = "string_smooth_order"


def get_string_smooth_order() -> int:
    return QSettings().value(_STRING_SMOOTH_ORDER, defaultValue=3, type=int)


def set_string_smooth_order(value: int):
    QSettings().setValue(_STRING_SMOOTH_ORDER, value)


_STRING_SIMULATION_VIEW_WINDOW = "string_simulation_view_window"
STRING_SIMULATION_VIEW_WINDOW_ONE = "one"
STRING_SIMULATINO_VIEW_WINDOW_ALL = "all"


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

SPEC_WAV_EX_RHODAMINE = 525
SPEC_WAV_EM_RHODAMINE = 575

_SPEC_WAV_EX = "spectrometer_wavelength_excitation_nm"
SPEC_WAV_EX__DEFAULT = SPEC_WAV_EX_RHODAMINE


def get_spec_wav_ex() -> int:
    return QSettings().value(_SPEC_WAV_EX, defaultValue=SPEC_WAV_EX__DEFAULT, type=int)


def set_spec_wav_ex(value: int):
    QSettings().setValue(_SPEC_WAV_EX, value)


_SPEC_WAV_EM = "spectrometer_wavelength_emission_nm"
SPEC_WAV_EM__DEFAULT = SPEC_WAV_EM_RHODAMINE


def get_spec_wav_em() -> int:
    return QSettings().value(_SPEC_WAV_EM, defaultValue=SPEC_WAV_EM__DEFAULT, type=int)


def set_spec_wav_em(value: int):
    QSettings().setValue(_SPEC_WAV_EM, value)


_SPEC_INT_TIME_MS = "spectrometer_integration_time_ms"
SPEC_INT_TIME_MS__DEFAULT = 100


def get_spec_int_time_millis() -> int:
    return QSettings().value(
        _SPEC_INT_TIME_MS, defaultValue=SPEC_INT_TIME_MS__DEFAULT, type=int
    )


def set_spec_int_time_millis(value: int):
    QSettings().setValue(_SPEC_INT_TIME_MS, value)


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
THRESHOLD_HSB_SATURATION_MIN__DEFAULT = 15


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
WATERSHED__DEFAULT = False


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
STAIN_APPROXIMATION_METHODS = [
    "None",
    "Minimum Enclosing Circle",
    "Fit Ellipse",
    "Convex Hull",
]
STAIN_APPROXIMATION_METHOD__DEFAULT = STAIN_APPROXIMATION_METHODS[0]


def get_stain_approximation_method() -> str:
    return QSettings().value(
        _STAIN_APPROXIMATION_METHOD,
        defaultValue=STAIN_APPROXIMATION_METHOD__DEFAULT,
        type=str,
    )


def set_stain_approximation_method(value: str):
    QSettings().setValue(_STAIN_APPROXIMATION_METHOD, value)


# SprayCard Processed Image Colors

COLOR_STAIN_OUTLINE = (138, 43, 226)  # Red-Pink
COLOR_STAIN_FILL_ALL = (0, 0, 255)  # Red
COLOR_STAIN_FILL_EDGE = (238, 130, 238)  # Violet
COLOR_STAIN_FILL_VALID = (255, 0, 0)  # Blue

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

_CARD_SIMULATION_VIEW_WINDOW = "card_simulation_view_window"
CARD_SIMULATION_VIEW_WINDOW_ONE = "one"
CARD_SIMULATINO_VIEW_WINDOW_ALL = "all"


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
CARD_SET_SAFE_WSP = {
    "set_name": "SAFE Fly-In (WSP)",
    "card_name": [
        "L-32",
        "L-24",
        "L-16",
        "L-8",
        "Center",
        "R-8",
        "R-16",
        "R-24",
        "R-32",
    ],
    "location": [-32, -24, -16, -8, 0, 8, 16, 24, 32],
    "location_unit": [UNIT_FT] * 9,
    "threshold_type": [THRESHOLD_TYPE_GRAYSCALE] * 9,
    "dpi": [1200] * 9,
}
CARD_SET_SAFE_WHITE = {
    "set_name": "SAFE Fly-In (White Cards)",
    "card_name": [
        "L-32",
        "L-24",
        "L-16",
        "L-8",
        "Center",
        "R-8",
        "R-16",
        "R-24",
        "R-32",
    ],
    "location": [-32, -24, -16, -8, 0, 8, 16, 24, 32],
    "location_unit": [UNIT_FT] * 9,
    "threshold_type": [THRESHOLD_TYPE_HSB] * 9,
    "dpi": [1200] * 9,
}
CARD_DEFINED_SETS__DEFAULT = [CARD_SET_SAFE_WSP, CARD_SET_SAFE_WHITE]


def get_card_defined_sets() -> str:
    return QSettings().value(
        _CARD_DEFINED_SETS,
        defaultValue=json.dumps(CARD_DEFINED_SETS__DEFAULT),
        type=str,
    )


def set_card_defined_sets(value: str):
    QSettings().setValue(_CARD_DEFINED_SETS, value)


_CARD_DEFINED_SET = "card_defined_set"
CARD_DEFINED_SET__DEFAULT = CARD_SET_SAFE_WHITE["set_name"]


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
