-- Schema for AccuPatt Data File (SeriesData)

CREATE TABLE IF NOT EXISTS series (
    id              TEXT PRIMARY KEY,
    series          INTEGER,
    created         INTEGER,
    modified        INTEGER,
    notes_setup     TEXT,
    notes_analyst   TEXT,
    version_major   INTEGER,
    version_minor   INTEGER,
    version_release INTEGER
);
CREATE TABLE IF NOT EXISTS series_string (
    series_id                   TEXT PRIMARY KEY REFERENCES series(id),
    average_center              INTEGER,
    average_center_method       TEXT,
    average_smooth              INTEGER,
    average_smooth_window       REAL,
    average_smooth_order        INTEGER,
    equalize_integrals          INTEGER,
    swath_adjusted              INTEGER,
    simulated_adjascent_passes  INTEGER
);
CREATE TABLE IF NOT EXISTS series_spray_card (
    series_id                   TEXT PRIMARY KEY REFERENCES series(id),
    average_center              INTEGER,
    average_center_method       TEXT,
    swath_adjusted              INTEGER,
    simulated_adjascent_passes  INTEGER
);
CREATE TABLE IF NOT EXISTS flyin (
    series_id       TEXT PRIMARY KEY REFERENCES series(id),
    flyin_name      TEXT,
    flyin_location  TEXT,
    flyin_date      TEXT,
    flyin_analyst   TEXT
);
CREATE TABLE IF NOT EXISTS applicator (
    series_id       TEXT PRIMARY KEY REFERENCES series(id),
    pilot           TEXT,
    business        TEXT,
    street          TEXT,
    city            TEXT,
    state           TEXT,
    zip             TEXT,
    phone           TEXT,
    email           TEXT
);
CREATE TABLE IF NOT EXISTS aircraft (
    series_id       TEXT PRIMARY KEY REFERENCES series(id),
    regnum          TEXT,
    make            TEXT,
    model           TEXT,
    wingspan        REAL,
    wingspan_units  TEXT,
    winglets        TEXT
);
CREATE TABLE IF NOT EXISTS spray_system (
    series_id               TEXT PRIMARY KEY REFERENCES series(id),
    swath                   INTEGER,
    swath_units             TEXT,
    rate                    REAL,
    rate_units              TEXT,
    pressure                REAL,
    pressure_units          TEXT,
    boom_width              REAL,
    boom_width_units        TEXT,
    boom_drop               REAL,
    boom_drop_units         TEXT,
    nozzle_spacing          REAL,
    nozzle_spacing_units    TEXT
);
CREATE TABLE IF NOT EXISTS nozzles (
    id              TEXT PRIMARY KEY,
    series_id       TEXT REFERENCES series(id),
    type            TEXT,
    size            TEXT,
    deflection      TEXT,
    quantity        INTEGER
);
CREATE TABLE IF NOT EXISTS passes (
    id                          TEXT PRIMARY KEY,
    series_id                   TEXT REFERENCES series(id),
    pass_name                   TEXT,
    pass_number                 INTEGER,
    ground_speed                REAL,
    ground_speed_units          TEXT,
    spray_height                REAL,
    spray_height_units          TEXT,
    pass_heading                INTEGER,
    wind_direction              INTEGER,
    wind_speed                  REAL,
    wind_speed_units            TEXT,
    temperature                 REAL,
    temperature_units           TEXT,
    humidity                    REAL
);
CREATE TABLE IF NOT EXISTS pass_string (
    pass_id                 TEXT PRIMARY KEY REFERENCES passes(id),
    dye                     TEXT,
    excitation_wav          INTEGER,
    emission_wav            INTEGER,
    integration_time_ms     INTEGER,
    boxcar_width            INTEGER,
    trim_left               INTEGER,
    trim_right              INTEGER,
    trim_vertical           REAL,
    rebase                  INTEGER,
    center                  INTEGER,
    center_method           TEXT,
    smooth                  INTEGER,
    smooth_window           REAL,
    smooth_order            INTEGER,
    data_loc_units          TEXT,
    excitation_data         TEXT,
    emission_data           TEXT,
    include_in_composite    INTEGER
);
CREATE TABLE IF NOT EXISTS pass_spray_card (
    pass_id                 TEXT PRIMARY KEY REFERENCES passes(id),
    center                  INTEGER,
    center_method           TEXT,
    include_in_composite    INTEGER
);
CREATE TABLE IF NOT EXISTS spray_cards (
    id                              TEXT PRIMARY KEY,
    pass_id                         TEXT REFERENCES passes(id),
    name                            TEXT,
    location                        REAL,
    location_units                  TEXT,
    include_in_composite            INTEGER,
    threshold_type                  INTEGER,
    threshold_method_grayscale      INTEGER,
    threshold_grayscale             INTEGER,
    threshold_color_hue_min         INTEGER,
    threshold_color_hue_max         INTEGER,
    threshold_color_hue_pass        INTEGER,
    threshold_color_saturation_min  INTEGER,
    threshold_color_saturation_max  INTEGER,
    threshold_color_saturation_pass INTEGER,
    threshold_color_brightness_min  INTEGER,
    threshold_color_brightness_max  INTEGER,
    threshold_color_brightness_pass INTEGER,
    watershed                       INTEGER,
    min_stain_area_px               INTEGER,
    stain_approximation_method      TEXT,
    dpi                             INTEGER,
    spread_method                   INTEGER,
    spread_factor_a                 REAL,
    spread_factor_b                 REAL,
    spread_factor_c                 REAL,
    has_image                       INTEGER,
    image                           BLOB
);