#Unit Labels
UNIT_MPH = 'mph'
UNIT_KPH = 'kph'
UNIT_FT = 'ft'
UNIT_M = 'm'
UNIT_IN = 'in'
UNIT_CM = 'cm'
UNIT_DEG = '°'
UNIT_DEG_F = '°F'
UNIT_DEG_C = '°C'
UNIT_GPA = 'gal/a'
UNIT_LPHA = 'l/ha'
UNIT_PSI = 'psi'
UNIT_BAR = 'bar'
UNIT_KPA = 'kpa'

#Unit Option Lists
UNITS_LENGTH_LARGE = [UNIT_FT, UNIT_M]
UNITS_LENGTH_SMALL = [UNIT_IN, UNIT_CM]

UNITS_RATE = [UNIT_GPA, UNIT_LPHA]
UNITS_PRESSURE = [UNIT_PSI, UNIT_BAR, UNIT_KPA]

# Math Conversion Constants
UM_PER_IN = 25400.0
FT_PER_M = 3.28084
MPH_PER_KPH = 0.621371
MPH_PER_KN = 1.15078

# Pass Data
UNITS_GROUND_SPEED = [UNIT_MPH, UNIT_KPH]
_UNIT_GROUND_SPEED = 'unit_ground_speed'
UNIT_GROUND_SPEED__DEFAULT = UNITS_GROUND_SPEED[0]
UNITS_SPRAY_HEIGHT = UNITS_LENGTH_LARGE
_UNIT_SPRAY_HEIGHT = 'unit_spray_height'
UNIT_SPRAY_HEIGHT__DEFAULT = UNITS_SPRAY_HEIGHT[0]
UNITS_WIND_SPEED = [UNIT_MPH, UNIT_KPH]
_UNIT_WIND_SPEED = 'unit_wind_speed'
UNIT_WIND_SPEED__DEFAULT = UNITS_WIND_SPEED[0]
UNITS_TEMPERATURE = [UNIT_DEG_F, UNIT_DEG_C]
_UNIT_TEMPERATURE = 'unit_temperature'
UNIT_TEMPERATURE__DEFAULT = UNITS_TEMPERATURE[0]
_UNIT_DATA_LOCATION = 'unit_data_location'
UNIT_DATA_LOCATION__DEFAULT = UNIT_FT

# Pattern Centering
_CENTER_METHOD = 'center_method'
CENTER_METHOD_NONE = 'None'
CENTER_METHOD_CENTROID = 'Centroid'
CENTER_METHOD_COD = 'Center of Distribution'
CENTER_METHOD__DEFAULT = CENTER_METHOD_CENTROID

# String Drive
STRING_DRIVE_FWD_START = 'AD+\r'
STRING_DRIVE_FWD_STOP = 'AD\r'
STRING_DRIVE_REV_START = 'BD-\r'
STRING_DRIVE_REV_STOP = 'BD\r'
_STRING_DRIVE_PORT = 'string_drive_port'
STRING_DRIVE_PORT__DEFAULT = ''
_STRING_LENGTH = 'string_length'
STRING_LENGTH__DEFAULT = 150.0
_STRING_SPEED = 'string_speed'
STRING_SPEED__DEFAULT = 1.71

# Spectrometer
SPEC_WAV_EX_RHODAMINE = 525
SPEC_WAV_EM_RHODAMINE = 575
_SPEC_WAV_EX = 'spectrometer_wavelength_excitation_nm'
SPEC_WAV_EX__DEFAULT = SPEC_WAV_EX_RHODAMINE
_SPEC_WAV_EM = 'spectrometer_wavelength_emission_nm'
SPEC_WAV_EM__DEFAULT = SPEC_WAV_EM_RHODAMINE
_SPEC_INT_TIME_MS = 'spectrometer_integration_time_ms'
SPEC_INT_TIME_MS__DEFAULT = 100

# SprayCard Load
_ROI_ACQUISITION_ORIENTATION = 'roi_acquisition_orientation'
ROI_ACQUISITION_ORIENTATIONS = ['Horizontal', 'Vertical']
ROI_ACQUISITION_ORIENTATION__DEFAULT = ROI_ACQUISITION_ORIENTATIONS[0]
_ROI_ACQUISITION_ORDER = 'roi_acquisition_order'
ROI_ACQUISITION_ORDERS = ['Increasing', 'Decreasing']
ROI_ACQUISITION_ORDER__DEFAULT = ROI_ACQUISITION_ORDERS[0]
_ROI_SCALE = 'roi_scale'
ROI_SCALES = [10,20,30,40,50,60,70,80,90,100]
ROI_SCALE__DEFAULT = ROI_SCALES[6]

# SprayCard DPI
_DPI = 'dpi'
DPI__DEFAULT = 600
DPI_OPTIONS = [300, 600, 1200, 2400]

# SprayCard Thresholding Constants
_THRESHOLD_TYPE = 'threshold_type'
THRESHOLD_TYPE_GRAYSCALE = 'Grayscale'
THRESHOLD_TYPE_HSB = 'HSB'
THRESHOLD_TYPES = [THRESHOLD_TYPE_GRAYSCALE, THRESHOLD_TYPE_HSB]
THRESHOLD_TYPE__DEFAULT = THRESHOLD_TYPES[0]
# SprayCard Thresholding Constants (Grayscale)
_THRESHOLD_GRAYSCALE = 'threshold_grayscale'
THRESHOLD_GRAYSCALE__DEFAULT = 152
_THRESHOLD_GRAYSCALE_METHOD = 'threshold_grayscale_method'
THRESHOLD_GRAYSCALE_METHOD_AUTO = 'Auto'
THRESHOLD_GRAYSCALE_METHOD_MANUAL = 'Manual'
THRESHOLD_GRAYSCALE_METHODS = [THRESHOLD_GRAYSCALE_METHOD_AUTO,THRESHOLD_GRAYSCALE_METHOD_MANUAL]
THRESHOLD_GRAYSCALE_METHOD__DEFAULT = THRESHOLD_GRAYSCALE_METHODS[0]
# SprayCard Thresholding Constants (HSB)
_THRESHOLD_HSB_HUE = 'threshold_hsb_hue'
THRESHOLD_HSB_HUE__DEFAULT = (180,240)
_THRESHOLD_HSB_SATURATION = 'threshold_hsb_saturation'
THRESHOLD_HSB_SATURATION__DEFAULT = (6,255)
_THRESHOLD_HSB_BRIGHTNESS = 'threshold_hsb_brightness'
THRESHOLD_HSB_BRIGHTNESS__DEFAULT = (0,255)
_THRESHOLD_HSB_METHOD = 'threshold_hsb_method'
THRESHOLD_HSB_METHOD_INCLUDE = 'Include'
THRESHOLD_HSB_METHOD_EXCLUDE = 'Exclude'
THRESHOLD_HSB_METHODS = [THRESHOLD_HSB_METHOD_INCLUDE,THRESHOLD_HSB_METHOD_EXCLUDE]
THRESHOLD_HSB_METHOD__DEFAULT = THRESHOLD_HSB_METHODS[1]

# SprayCard Processing Options
_WATERSHED = 'watershed'
WATERSHED__DEFAULT = False
_MIN_STAIN_AREA_PX = 'min_stain_area_px'
MIN_STAIN_AREA_PX = 4

# SprayCard Processed Image Colors
COLOR_STAIN_OUTLINE = (138, 43, 226) #Red-Pink
COLOR_STAIN_FILL_ALL = (0, 0, 255) #Red
COLOR_STAIN_FILL_EDGE = (238, 130, 238) #Violet
COLOR_STAIN_FILL_VALID = (255, 0, 0) #Blue

# SprayCard Spread Factor Methods
_SPREAD_FACTOR_A = 'spread_factor_a'
SPREAD_FACTOR_A__DEFAULT = 0.0000
_SPREAD_FACTOR_B = 'spread_factor_b'
SPREAD_FACTOR_B__DEFAULT = 0.0009
_SPREAD_FACTOR_C = 'spread_factor_c'
SPREAD_FACTOR_C__DEFAULT = 1.6333
_SPREAD_METHOD = 'spread_factor_method'
SPREAD_METHOD_NONE = 'None'
SPREAD_METHOD_DIRECT = 'Direct'
SPREAD_METHOD_ADAPTIVE = 'Adaptive'
SPREAD_METHODS = [SPREAD_METHOD_NONE,SPREAD_METHOD_DIRECT,SPREAD_METHOD_ADAPTIVE]
SPREAD_METHOD__DEFAULT = SPREAD_METHODS[2]

    
