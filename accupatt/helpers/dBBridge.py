import os
import sqlite3
import alembic.config
import alembic.command
from datetime import datetime

import pandas as pd
import accupatt.config as cfg
from accupatt.models.appInfo import Nozzle
from accupatt.models.passDataCard import PassDataCard
from accupatt.models.passData import Pass
from accupatt.models.passDataString import PassDataString
from accupatt.models.seriesDataCard import SeriesDataCard
from accupatt.models.seriesData import SeriesData
from accupatt.models.seriesDataString import SeriesDataString
from accupatt.models.sprayCard import SprayCard

schema_filename = os.path.join(os.getcwd(), "resources", "schema.sql")
alembic_ini = os.path.join(os.getcwd(), "resources", "alembic.ini")


"""""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
Loading
""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""


def load_from_db(file: str, s: SeriesData, load_only_info=False):
    # Use Alembic to convert db to most current
    alembic_args = [
        "--raiseerr",
        f"-c{alembic_ini}",
        f"-xdbPath=sqlite:///{file}",
        "upgrade",
        "head",
    ]
    alembic.config.main(argv=alembic_args)
    # Opens a file connection to the db
    with sqlite3.connect(file) as conn:
        # Get a cursor object
        c = conn.cursor()
        if load_only_info:
            # Need a handle on the series id to load
            s_ = SeriesData()
            _load_table_series(c, s_)
            s.info.series = s_.info.series
            # Load in only needed data
            _load_table_applicator(c, s, s_.id)
            _load_table_aircraft(c, s, s_.id)
            _load_table_spray_system(c, s, s_.id)
            _load_table_nozzles(c, s, s_.id)
        else:
            _load_table_series(c, s)
            _load_table_series_string(c, s)
            _load_table_series_spray_card(c, s)
            _load_table_flyin(c, s)
            _load_table_applicator(c, s)
            _load_table_aircraft(c, s)
            _load_table_spray_system(c, s)
            _load_table_nozzles(c, s)
            _load_table_passes(c, s, file)


def _load_table_series(c: sqlite3.Cursor, s: SeriesData):
    i = s.info
    c.execute(
        """SELECT id, series, created, modified, notes_setup, notes_analyst, version_major, version_minor, version_release FROM series"""
    )
    (
        s.id,
        i.series,
        i.created,
        i.modified,
        i.notes_setup,
        i.notes_analyst,
        version_major,
        version_minor,
        version_release,
    ) = c.fetchone()


def _load_table_series_string(c: sqlite3.Cursor, s: SeriesData):
    ss: SeriesDataString = s.string
    c.execute(
        """SELECT average_center, average_center_method, average_smooth, average_smooth_window, average_smooth_order, equalize_integrals, swath_adjusted, simulated_adjascent_passes FROM series_string WHERE series_id = ?""",
        (s.id,),
    )
    (
        ss.center,
        ss.center_method,
        ss.smooth,
        ss.smooth_window,
        ss.smooth_order,
        ss.equalize_integrals,
        ss.swath_adjusted,
        ss.simulated_adjascent_passes,
    ) = c.fetchone()


def _load_table_series_spray_card(c: sqlite3.Cursor, s: SeriesData):
    scd: SeriesDataCard = s.cards
    c.execute(
        """SELECT average_center, average_center_method, swath_adjusted, simulated_adjascent_passes FROM series_spray_card WHERE series_id = ?""",
        (s.id,),
    )
    (
        scd.center,
        scd.center_method,
        scd.swath_adjusted,
        scd.simulated_adjascent_passes,
    ) = c.fetchone()


def _load_table_flyin(c: sqlite3.Cursor, s: SeriesData):
    i = s.info
    c.execute(
        """SELECT flyin_name, flyin_location, flyin_date, flyin_analyst FROM flyin WHERE series_id = ?""",
        (s.id,),
    )
    i.flyin_name, i.flyin_location, i.flyin_date, i.flyin_analyst = c.fetchone()


def _load_table_applicator(c: sqlite3.Cursor, s: SeriesData, alt_id: str = ""):
    if alt_id == "":
        id_ = s.id
    else:
        id_ = alt_id
    i = s.info
    c.execute(
        """SELECT pilot, business, street, city, state, zip, phone, email FROM applicator WHERE series_id = ?""",
        (id_,),
    )
    (
        i.pilot,
        i.business,
        i.street,
        i.city,
        i.state,
        i.zip,
        i.phone,
        i.email,
    ) = c.fetchone()


def _load_table_aircraft(c: sqlite3.Cursor, s: SeriesData, alt_id: str = ""):
    if alt_id == "":
        id_ = s.id
    else:
        id_ = alt_id
    i = s.info
    c.execute(
        """SELECT regnum, make, model, wingspan, wingspan_units, winglets FROM aircraft WHERE series_id = ?""",
        (id_,),
    )
    i.regnum, i.make, i.model, i.wingspan, i.wingspan_units, i.winglets = c.fetchone()


def _load_table_spray_system(c: sqlite3.Cursor, s: SeriesData, alt_id: str = ""):
    if alt_id == "":
        id = s.id
    else:
        id = alt_id
    i = s.info
    c.execute(
        """SELECT swath, swath_units, rate, rate_units, pressure, pressure_units, boom_width, boom_width_units, boom_drop, boom_drop_units, nozzle_spacing, nozzle_spacing_units FROM spray_system WHERE series_id = ?""",
        (id,),
    )
    (
        i.swath,
        i.swath_units,
        i.rate,
        i.rate_units,
        i.pressure,
        i.pressure_units,
        i.boom_width,
        i.boom_width_units,
        i.boom_drop,
        i.boom_drop_units,
        i.nozzle_spacing,
        i.nozzle_spacing_units,
    ) = c.fetchone()


def _load_table_nozzles(c: sqlite3.Cursor, s: SeriesData, alt_id: str = ""):
    if alt_id == "":
        id = s.id
    else:
        id = alt_id
    i = s.info
    c.execute(
        """SELECT id, type, size, deflection, quantity FROM nozzles WHERE series_id = ?""",
        (id,),
    )
    data = c.fetchall()
    for row in data:
        i.nozzles.append(
            Nozzle(
                id=row[0], type=row[1], size=row[2], deflection=row[3], quantity=row[4]
            )
        )


def _load_table_passes(c: sqlite3.Cursor, s: SeriesData, file: str):
    c.execute(
        """SELECT id, pass_name, pass_number, ground_speed, ground_speed_units, spray_height, spray_height_units, pass_heading, wind_direction, wind_speed, wind_speed_units, temperature, temperature_units, humidity FROM passes WHERE series_id = ?""",
        (s.id,),
    )
    data = c.fetchall()
    for row in data:
        p = Pass(id_=row[0], number=row[2])
        (
            _,
            p.name,
            _,
            p.ground_speed,
            p.ground_speed_units,
            p.spray_height,
            p.spray_height_units,
            p.pass_heading,
            p.wind_direction,
            p.wind_speed,
            p.wind_speed_units,
            p.temperature,
            p.temperature_units,
            p.humidity,
        ) = row

        _load_table_pass_string(c, p)
        _load_table_pass_spray_card(c, p)
        _load_table_spray_cards(c, p, file)

        s.passes.append(p)


def _load_table_pass_string(c: sqlite3.Cursor, p: Pass):
    c.execute(
        """SELECT dye, excitation_wav, emission_wav, integration_time_ms, boxcar_width, trim_left, trim_right, trim_vertical, rebase, center, center_method, smooth, smooth_window, smooth_order, data_loc_units, excitation_data, emission_data, include_in_composite FROM pass_string WHERE pass_id = ?""",
        (p.id,),
    )
    ps: PassDataString = p.string
    (
        ps.dye.name,
        ps.dye.wavelength_excitation,
        ps.dye.wavelength_emission,
        ps.dye.integration_time_milliseconds,
        ps.dye.boxcar_width,
        ps.trim_l,
        ps.trim_r,
        ps.trim_v,
        ps.rebase,
        ps.center,
        ps.center_method,
        ps.smooth,
        ps.smooth_window,
        ps.smooth_order,
        ps.data_loc_units,
        d_ex,
        d_em,
        ps.include_in_composite,
    ) = c.fetchone()
    ps.data_ex = pd.read_json(d_ex)
    ps.data = pd.read_json(d_em)


def _load_table_pass_spray_card(c: sqlite3.Cursor, p: Pass):
    c.execute(
        """SELECT center, center_method, include_in_composite FROM pass_spray_card WHERE pass_id = ?""",
        (p.id,),
    )
    pcd: PassDataCard = p.cards
    (
        pcd.center,
        pcd.center_method,
        pcd.include_in_composite,
    ) = c.fetchone()


def _load_table_spray_cards(c: sqlite3.Cursor, p: Pass, file: str):
    # Spray Cards Table
    c.execute(
        """SELECT id, name, location, location_units, include_in_composite, threshold_type, threshold_method_grayscale, threshold_grayscale, threshold_color_hue_min, threshold_color_hue_max, threshold_color_hue_pass, threshold_color_saturation_min, threshold_color_saturation_max, threshold_color_saturation_pass, threshold_color_brightness_min, threshold_color_brightness_max, threshold_color_brightness_pass, watershed, min_stain_area_px, stain_approximation_method, dpi, spread_method, spread_factor_a, spread_factor_b, spread_factor_c, has_image FROM spray_cards WHERE pass_id = ?""",
        (p.id,),
    )
    cards = c.fetchall()
    for row in cards:
        sc = SprayCard(id_=row[0], name=row[1], filepath=str(file))
        (
            _,
            _,
            sc.location,
            sc.location_units,
            sc.include_in_composite,
            sc.threshold_type,
            sc.threshold_method_grayscale,
            sc.threshold_grayscale,
            hmin,
            hmax,
            hpass,
            smin,
            smax,
            spass,
            bmin,
            bmax,
            bpass,
            sc.watershed,
            sc.min_stain_area_px,
            sc.stain_approximation_method,
            sc.dpi,
            sc.spread_method,
            sc.spread_factor_a,
            sc.spread_factor_b,
            sc.spread_factor_c,
            sc.has_image,
        ) = row
        sc.set_threshold_color_hue(min_=hmin, max_=hmax, bandpass=hpass)
        sc.set_threshold_color_saturation(min_=smin, max_=smax, bandpass=spass)
        sc.set_threshold_color_brightness(min_=bmin, max_=bmax, bandpass=bpass)
        p.cards.card_list.append(sc)


def load_image_from_db(file: str, spray_card_id: str) -> bytearray:
    byte_array = None
    with sqlite3.connect(file) as conn:
        # Get a cursor object
        c = conn.cursor()
        # SprayCard Table entry matching supplied card id
        c.execute("""SELECT image FROM spray_cards WHERE id = ?""", (spray_card_id,))
        # blob to byte array
        byte_array = bytearray(c.fetchone()[0])
    return byte_array


"""""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
Saving
""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""


def save_to_db(file: str, s: SeriesData):
    # If db not yet created need create timestamp
    if not os.path.isfile(file):
        s.info.created = int(datetime.now().timestamp())
    s.info.modified = int(datetime.now().timestamp())
    # Use Alembic to convert db to most current
    alembic_args = [
        "--raiseerr",
        f"-c{alembic_ini}",
        f"-xdbPath=sqlite:///{file}",
        "stamp",
        "head",
    ]
    alembic.config.main(argv=alembic_args)
    # Opens a file connection to the db
    with sqlite3.connect(file) as conn:
        # Create db from schema if no tables exist
        with open(schema_filename, "rt") as f:
            schema = f.read()
        conn.executescript(schema)
        # Get a cursor object
        c = conn.cursor()
        # Ensure we don't get multiple series per db file
        if _is_new_or_sole_series(c, s):
            # Update all tables
            _update_table_series(c, s)
            _update_table_series_string(c, s)
            _update_table_series_spray_card(c, s)
            _update_table_flyin(c, s)
            _update_table_aircraft(c, s)
            _update_table_applicator(c, s)
            _update_table_spray_system(c, s)
            _update_table_nozzles(c, s)
            _update_table_passes(c, s)
            return True
    return False


def _is_new_or_sole_series(c: sqlite3.Cursor, s: SeriesData):
    c.execute("""SELECT id FROM series""")
    ids = c.fetchall()
    if len(ids) == 0:
        return True
    elif len(ids) == 1:
        return ids[0][0] == s.id
    return False


def _update_table_series(c: sqlite3.Cursor, s: SeriesData):
    i = s.info
    c.execute(
        """INSERT INTO series (id, series, created, modified, notes_setup, notes_analyst, version_major, version_minor, version_release) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                    series = excluded.series, created = excluded.created, modified = excluded.modified, notes_setup = excluded.notes_setup, notes_analyst = excluded.notes_analyst""",
        (
            s.id,
            i.series,
            i.created,
            i.modified,
            i.notes_setup,
            i.notes_analyst,
            cfg.VERSION_MAJOR,
            cfg.VERSION_MINOR,
            cfg.VERSION_RELEASE,
        ),
    )


def _update_table_series_string(c: sqlite3.Cursor, s: SeriesData):
    ss: SeriesDataString = s.string
    c.execute(
        """INSERT INTO series_string (series_id, average_center, average_center_method, average_smooth, average_smooth_window, average_smooth_order, equalize_integrals, swath_adjusted, simulated_adjascent_passes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(series_id) DO UPDATE SET
                    average_center = excluded.average_center, average_center_method = excluded.average_center_method, average_smooth = excluded.average_smooth, average_smooth_window = excluded.average_smooth_window, average_smooth_order = excluded.average_smooth_window, equalize_integrals = excluded.equalize_integrals, swath_adjusted = excluded.swath_adjusted, simulated_adjascent_passes = excluded.simulated_adjascent_passes""",
        (
            s.id,
            ss.center,
            ss.center_method,
            ss.smooth,
            ss.smooth_window,
            ss.smooth_order,
            ss.equalize_integrals,
            ss.swath_adjusted,
            ss.simulated_adjascent_passes,
        ),
    )


def _update_table_series_spray_card(c: sqlite3.Cursor, s: SeriesData):
    scd: SeriesDataCard = s.cards
    c.execute(
        """INSERT INTO series_spray_card (series_id, average_center, average_center_method, swath_adjusted, simulated_adjascent_passes) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(series_id) DO UPDATE SET
                    average_center = excluded.average_center, average_center_method = excluded.average_center_method, swath_adjusted = excluded.swath_adjusted, simulated_adjascent_passes = excluded.simulated_adjascent_passes""",
        (
            s.id,
            scd.center,
            scd.center_method,
            scd.swath_adjusted,
            scd.simulated_adjascent_passes,
        ),
    )


def _update_table_flyin(c: sqlite3.Cursor, s: SeriesData):
    i = s.info
    c.execute(
        """INSERT INTO flyin (series_id, flyin_name, flyin_location, flyin_date, flyin_analyst) VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(series_id) DO UPDATE SET
                        flyin_name = excluded.flyin_name, flyin_location = excluded.flyin_location, flyin_date = excluded.flyin_date, flyin_analyst = excluded.flyin_analyst""",
        (s.id, i.flyin_name, i.flyin_location, i.flyin_date, i.flyin_analyst),
    )


def _update_table_applicator(c: sqlite3.Cursor, s: SeriesData):
    i = s.info
    c.execute(
        """INSERT INTO applicator (series_id, pilot, business, street, city, state, zip, phone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(series_id) DO UPDATE SET
                        pilot = excluded.pilot, business = excluded.business, street = excluded.street, city = excluded.city, state = excluded.state, zip = excluded.zip, phone = excluded.phone, email = excluded.email""",
        (s.id, i.pilot, i.business, i.street, i.city, i.state, i.zip, i.phone, i.email),
    )


def _update_table_aircraft(c: sqlite3.Cursor, s: SeriesData):
    i = s.info
    c.execute(
        """INSERT INTO aircraft (series_id, regnum, make, model, wingspan, wingspan_units, winglets) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(series_id) DO UPDATE SET
                        regnum = excluded.regnum, make = excluded.make, model = excluded.model, wingspan = excluded.wingspan, wingspan_units = excluded.wingspan_units, winglets = excluded.winglets""",
        (s.id, i.regnum, i.make, i.model, i.wingspan, i.wingspan_units, i.winglets),
    )


def _update_table_spray_system(c: sqlite3.Cursor, s: SeriesData):
    i = s.info
    c.execute(
        """INSERT INTO spray_system (series_id, swath, swath_units, rate, rate_units, pressure, pressure_units, boom_width, boom_width_units, boom_drop, boom_drop_units, nozzle_spacing, nozzle_spacing_units) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(series_id) DO UPDATE SET
                        swath = excluded.swath, swath_units = excluded.swath_units, rate = excluded.rate, rate_units = excluded.rate_units, pressure = excluded.pressure, pressure_units = excluded.pressure_units,  boom_width = excluded.boom_width, boom_width_units = excluded.boom_width_units, boom_drop = excluded.boom_drop, boom_drop_units = excluded.boom_drop_units, nozzle_spacing = excluded.nozzle_spacing, nozzle_spacing_units = excluded.nozzle_spacing_units""",
        (
            s.id,
            i.swath,
            i.swath_units,
            i.rate,
            i.rate_units,
            i.pressure,
            i.pressure_units,
            i.boom_width,
            i.boom_width_units,
            i.boom_drop,
            i.boom_drop_units,
            i.nozzle_spacing,
            i.nozzle_spacing_units,
        ),
    )


def _update_table_nozzles(c: sqlite3.Cursor, s: SeriesData):
    i = s.info
    n: Nozzle
    for n in i.nozzles:
        c.execute(
            """INSERT INTO nozzles (id, series_id, type, size, deflection, quantity) VALUES (?, ?, ?, ?, ?, ?)
                  ON CONFLICT(id) DO UPDATE SET
                  type = excluded.type, size = excluded.size, deflection = excluded.deflection, quantity = excluded.quantity""",
            (n.id, s.id, n.type, n.size, n.deflection, n.quantity),
        )
    # Loop through nozzles on db, delete any not in series object
    current_ids = [n.id for n in i.nozzles]
    if len(current_ids) == 0:
        c.execute("""DELETE FROM nozzles WHERE id = ?""", (n.id,))
    else:
        in_query = "("
        for i, id_ in enumerate(current_ids):
            if i == 0:
                in_query += f"'{id_}'"
            else:
                in_query += f", '{id_}'"
        in_query += ")"
        c.execute(f"DELETE FROM nozzles WHERE id NOT IN {in_query}")


def _update_table_passes(c: sqlite3.Cursor, s: SeriesData):
    p: Pass
    for p in s.passes:
        c.execute(
            """INSERT INTO passes (id, series_id, pass_name, pass_number, ground_speed, ground_speed_units, spray_height, spray_height_units, pass_heading, wind_direction, wind_speed, wind_speed_units, temperature, temperature_units, humidity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                    pass_name = excluded.pass_name, pass_number = excluded.pass_number, ground_speed = excluded.ground_speed, ground_speed_units = excluded.ground_speed_units, spray_height = excluded.spray_height, spray_height_units = excluded.spray_height_units, pass_heading = excluded.pass_heading, wind_direction = excluded.wind_direction, wind_speed = excluded.wind_speed, wind_speed_units = excluded.wind_speed_units, temperature = excluded.temperature, temperature_units = excluded.temperature_units, humidity = excluded.humidity""",
            (
                p.id,
                s.id,
                p.name,
                p.number,
                p.ground_speed,
                p.ground_speed_units,
                p.spray_height,
                p.spray_height_units,
                p.pass_heading,
                p.wind_direction,
                p.wind_speed,
                p.wind_speed_units,
                p.temperature,
                p.temperature_units,
                p.humidity,
            ),
        )
        _update_table_pass_string(c, p)
        _update_table_pass_spray_card(c, p)
        _update_table_spray_cards(c, p)
    # Loop through passes on db, delete any not in series object
    current_ids = [p.id for p in s.passes]
    if len(current_ids) == 0:
        c.execute("""DELETE FROM passes WHERE pass_id = ?""", (p.id,))
    else:
        in_query = "("
        for i, id in enumerate(current_ids):
            if i == 0:
                in_query += f"'{id}'"
            else:
                in_query += f", '{id}'"
        in_query += ")"
        c.execute(f"DELETE FROM passes WHERE id NOT IN {in_query}")
        c.execute(f"DELETE FROM pass_string WHERE pass_id NOT IN {in_query}")
        c.execute(f"DELETE FROM spray_cards WHERE pass_id NOT IN {in_query}")


def _update_table_pass_string(c: sqlite3.Cursor, p: Pass):
    ps: PassDataString = p.string
    c.execute(
        """INSERT INTO pass_string (pass_id, dye, excitation_wav, emission_wav, integration_time_ms, boxcar_width, trim_left, trim_right, trim_vertical, rebase, center, center_method, smooth, smooth_window, smooth_order, data_loc_units, excitation_data, emission_data, include_in_composite) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(pass_id) DO UPDATE SET
                    dye = excluded.dye, excitation_wav = excluded.excitation_wav, emission_wav = excluded.emission_wav, integration_time_ms = excluded.integration_time_ms, boxcar_width = excluded.boxcar_width, trim_left = excluded.trim_left, trim_right = excluded.trim_right, trim_vertical = excluded.trim_vertical, rebase = excluded.rebase, center = excluded.center, center_method = excluded.center_method, smooth = excluded.smooth, smooth_window = excluded.smooth_window, smooth_order = excluded.smooth_order, data_loc_units = excluded.data_loc_units, excitation_data = excluded.excitation_data, emission_data = excluded.emission_data, include_in_composite = excluded.include_in_composite""",
        (
            p.id,
            ps.dye.name,
            ps.dye.wavelength_excitation,
            ps.dye.wavelength_emission,
            ps.dye.integration_time_milliseconds,
            ps.dye.boxcar_width,
            ps.trim_l,
            ps.trim_r,
            ps.trim_v,
            ps.rebase,
            ps.center,
            ps.center_method,
            ps.smooth,
            ps.smooth_window,
            ps.smooth_order,
            ps.data_loc_units,
            ps.data_ex.to_json(),
            ps.data.to_json(),
            ps.include_in_composite,
        ),
    )


def _update_table_pass_spray_card(c: sqlite3.Cursor, p: Pass):
    pcd: PassDataCard = p.cards
    c.execute(
        """INSERT INTO pass_spray_card (pass_id, center, center_method, include_in_composite) VALUES (?, ?, ?, ?)
                    ON CONFLICT(pass_id) DO UPDATE SET
                    center = excluded.center, center_method = excluded.center_method, include_in_composite = excluded.include_in_composite""",
        (
            p.id,
            pcd.center,
            pcd.center_method,
            pcd.include_in_composite,
        ),
    )


def _update_table_spray_cards(c: sqlite3.Cursor, p: Pass):
    card: SprayCard
    for card in p.cards.card_list:
        c.execute(
            """INSERT INTO spray_cards (id, pass_id, name, location, location_units, include_in_composite, threshold_type, threshold_method_grayscale, threshold_grayscale, threshold_color_hue_min, threshold_color_hue_max, threshold_color_hue_pass, threshold_color_saturation_min, threshold_color_saturation_max, threshold_color_saturation_pass, threshold_color_brightness_min, threshold_color_brightness_max, threshold_color_brightness_pass, watershed, min_stain_area_px, stain_approximation_method, dpi, spread_method, spread_factor_a, spread_factor_b, spread_factor_c, has_image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name, location = excluded.location, location_units = excluded.location_units, include_in_composite = excluded.include_in_composite, threshold_type = excluded.threshold_type, threshold_method_grayscale = excluded.threshold_method_grayscale, threshold_grayscale = excluded.threshold_grayscale, threshold_color_hue_min = excluded.threshold_color_hue_min, threshold_color_hue_max = excluded.threshold_color_hue_max, threshold_color_hue_pass = excluded.threshold_color_hue_pass, threshold_color_saturation_min = excluded.threshold_color_saturation_min, threshold_color_saturation_max = excluded.threshold_color_saturation_max, threshold_color_saturation_pass = excluded.threshold_color_saturation_pass, threshold_color_brightness_min = excluded.threshold_color_brightness_min, threshold_color_brightness_max = excluded.threshold_color_brightness_max, threshold_color_brightness_pass = excluded.threshold_color_brightness_pass, watershed = excluded.watershed, min_stain_area_px = excluded.min_stain_area_px, stain_approximation_method = excluded.stain_approximation_method, dpi = excluded.dpi, spread_method = excluded.spread_method, spread_factor_a = excluded.spread_factor_a, spread_factor_B = excluded.spread_factor_b, spread_factor_c = excluded.spread_factor_c, has_image = excluded.has_image""",
            (
                card.id,
                p.id,
                card.name,
                card.location,
                card.location_units,
                card.include_in_composite,
                card.threshold_type,
                card.threshold_method_grayscale,
                card.threshold_grayscale,
                card.threshold_color_hue_min,
                card.threshold_color_hue_max,
                card.threshold_color_hue_pass,
                card.threshold_color_saturation_min,
                card.threshold_color_saturation_max,
                card.threshold_color_saturation_pass,
                card.threshold_color_brightness_min,
                card.threshold_color_brightness_max,
                card.threshold_color_brightness_pass,
                card.watershed,
                card.min_stain_area_px,
                card.stain_approximation_method,
                card.dpi,
                card.spread_method,
                card.spread_factor_a,
                card.spread_factor_b,
                card.spread_factor_c,
                card.has_image,
            ),
        )
    # Loop through cards on db, delete any not in pass object
    current_ids = [sc.id for sc in p.cards.card_list]
    if len(current_ids) == 0:
        c.execute("""DELETE FROM spray_cards WHERE pass_id = ?""", (p.id,))
    else:
        in_query = "("
        for i, id in enumerate(current_ids):
            if i == 0:
                in_query += f"'{id}'"
            else:
                in_query += f", '{id}'"
        in_query += ")"
        c.execute(
            f'DELETE FROM spray_cards WHERE pass_id = "{p.id}" AND id NOT IN {in_query}'
        )


def save_image_to_db(file: str, spray_card_id: str, image) -> bool:
    success = False
    with sqlite3.connect(file) as conn:
        # Get a cursor object
        c = conn.cursor()
        # Request update of card record in table spray_cards by sprayCard.id
        c.execute(
            """UPDATE spray_cards SET image = ? WHERE id = ?""",
            (sqlite3.Binary(image), spray_card_id),
        )
        success = True
    return success
