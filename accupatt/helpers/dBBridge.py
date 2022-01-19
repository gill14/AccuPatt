import pandas as pd
import os

import sqlite3

from accupatt.models.seriesData import SeriesData
from accupatt.models.appInfo import AppInfo
from accupatt.models.passData import Pass
from accupatt.models.sprayCard import SprayCard

class DBBridge:
    
    schema_filename = os.path.join(os.getcwd(), 'accupatt', 'helpers', 'schema.sql')
    
    def __init__(self, file: str, series: SeriesData):
        self.file = file
        self.s = series

    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Loading
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

    def load_from_db(self, load_only_info=False):
        # Opens a file connection to the db
        with sqlite3.connect(self.file) as conn:
            # Get a cursor object
            c = conn.cursor()
            if load_only_info:
                # Need a handle on the series id to load
                s_ = SeriesData()
                self._load_table_series(c,s_)
                # Load in only needed data
                self._load_table_applicator(c,self.s,s_.id)
                self._load_table_aircraft(c,self.s,s_.id)
                self._load_table_spray_system(c,self.s,s_.id)
            else:
                self._load_table_series(c,self.s)
                self._load_table_series_string(c,self.s)
                self._load_table_flyin(c,self.s)
                self._load_table_applicator(c,self.s)
                self._load_table_aircraft(c,self.s)
                self._load_table_spray_system(c,self.s)
                self._load_table_passes(c,self.s)

    def _load_table_series(self, c: sqlite3.Cursor, s: SeriesData):
        i = s.info
        # Series Table
        c.execute('''SELECT id, series, date, time, notes_setup, notes_analyst FROM series''')
        s.id, i.series, i.date, i.time, i.notes_setup, i.notes_analyst = c.fetchone()

    def _load_table_series_string(self, c: sqlite3.Cursor, s: SeriesData):
        i = s.info
        # Series String Table
        c.execute('''SELECT smooth_individual, smooth_average, equalize_integrals, center, simulated_adjascent_passes FROM series_string WHERE series_id = ?''', (s.id,))
        s.string_smooth_individual, s.string_smooth_average, s.string_equalize_integrals, s.string_center, s.string_simulated_adjascent_passes = c.fetchone()

    def _load_table_flyin(self, c: sqlite3.Cursor, s: SeriesData):
        i = s.info
        #Flyin Table
        c.execute('''SELECT flyin_name, flyin_location, flyin_date, flyin_analyst FROM flyin WHERE series_id = ?''', (s.id,))
        i.flyin_name, i.flyin_location, i.flyin_date, i.flyin_analyst = c.fetchone()
        
    def _load_table_applicator(self, c: sqlite3.Cursor, s: SeriesData, alt_id: str = ''):
        if alt_id == '':
            id = s.id
        else:
            id = alt_id
        i = s.info
        #Applicator Table
        c.execute('''SELECT pilot, business, street, city, state, zip, phone, email FROM applicator WHERE series_id = ?''',(id,))
        i.pilot, i.business, i.street, i.city, i.state, i.zip, i.phone, i.email = c.fetchone()
    
    def _load_table_aircraft(self, c: sqlite3.Cursor, s: SeriesData, alt_id: str = ''):
        if alt_id == '':
            id = s.id
        else:
            id = alt_id
        i = s.info
        #Aircraft Table
        c.execute('''SELECT regnum, make, model, wingspan, wingspan_units, winglets FROM aircraft WHERE series_id = ?''', (id,))
        i.regnum, i.make, i.model, i.wingspan, i.wingspan_units, i.winglets = c.fetchone()
      
    def _load_table_spray_system(self, c: sqlite3.Cursor, s: SeriesData, alt_id: str = ''):
        if alt_id == '':
            id = s.id
        else:
            id = alt_id
        i = s.info
        #Spray System Table
        c.execute('''SELECT swath, swath_adjusted, swath_units, rate, rate_units, pressure, pressure_units, nozzle_type_1, nozzle_size_1, nozzle_deflection_1, nozzle_quantity_1, nozzle_type_2, nozzle_size_2, nozzle_deflection_2, nozzle_quantity_2, boom_width, boom_width_units, boom_drop, boom_drop_units, nozzle_spacing, nozzle_spacing_units FROM spray_system WHERE series_id = ?''',(id,))
        i.swath, i.swath_adjusted, i.swath_units, i.rate, i.rate_units, i.pressure, i.pressure_units, i.nozzle_type_1, i.nozzle_size_1, i.nozzle_deflection_1, i.nozzle_quantity_1, i.nozzle_type_2, i.nozzle_size_2, i.nozzle_deflection_2, i.nozzle_quantity_2, i.boom_width, i.boom_width_units, i.boom_drop, i.boom_drop_units, i.nozzle_spacing, i.nozzle_spacing_units = c.fetchone()

    def _load_table_passes(self, c: sqlite3.Cursor, s: SeriesData):
        #Passes Table
        c.execute('''SELECT id, pass_name, pass_number, ground_speed, ground_speed_units, spray_height, spray_height_units, pass_heading, wind_direction, wind_speed, wind_speed_units, temperature, temperature_units, humidity, include_in_composite, excitation_wav, emission_wav, trim_left, trim_right, trim_vertical, excitation_data, emission_data, data_loc_units FROM passes WHERE series_id = ?''',(s.id,))
        data = c.fetchall()
        for row in data:
            p = Pass(id=row[0], number=row[2])
            _, p.name, _, p.ground_speed, p.ground_speed_units, p.spray_height, p.spray_height_units, p.pass_heading, p.wind_direction, p.wind_speed, p.wind_speed_units, p.temperature, p.temperature_units, p.humidity, p.include_in_composite, p.excitation_wav, p.emission_wav, p.trim_l, p.trim_r, p.trim_v, d_ex, d_em, p.data_loc_units = row
            p.data_ex = pd.read_json(d_ex)
            p.data = pd.read_json(d_em)
            
            self._load_table_spray_cards(c,p)
            
            s.passes.append(p)

    def _load_table_spray_cards(self, c: sqlite3.Cursor, p: Pass):
        #Spray Cards Table
        c.execute('''SELECT id, name, location, location_units, include_in_composite, threshold_type, threshold_method_grayscale, threshold_grayscale, threshold_method_color, threshold_color_hue_min, threshold_color_hue_max, threshold_color_saturation_min, threshold_color_saturation_max, threshold_color_brightness_min, threshold_color_brightness_max, dpi, spread_method, spread_factor_a, spread_factor_b, spread_factor_c, has_image FROM spray_cards WHERE pass_id = ?''',(p.id,))
        cards = c.fetchall()
        for row in cards:
            sc = SprayCard(id=row[0], name=row[1], filepath=str(self.file))
            _, _, sc.location, sc.location_units, sc.include_in_composite, sc.threshold_type, sc.threshold_method_grayscale, sc.threshold_grayscale, sc.threshold_method_color, hmin, hmax, smin, smax, bmin, bmax,sc.dpi,sc.spread_method,sc.spread_factor_a,sc.spread_factor_b,sc.spread_factor_c,sc.has_image = row
            sc.set_threshold_color_hue(hmin, hmax)
            sc.set_threshold_color_saturation(smin, smax)
            sc.set_threshold_color_brightness(bmin, bmax)
            p.spray_cards.append(sc)
            
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Saving
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''        
    
    def save_to_db(self):
        # Opens a file connection to the db
        with sqlite3.connect(self.file) as conn:
            # Create db from schema if no tables exist
            with open(self.schema_filename, 'rt') as f:
                    schema = f.read()
            conn.executescript(schema)
            # Get a cursor object
            c = conn.cursor()
            # Update all tables
            self._update_table_series(c, self.s)
            self._update_table_series_string(c, self.s)
            self._update_table_flyin(c, self.s)
            self._update_table_aircraft(c, self.s)
            self._update_table_applicator(c, self.s)
            self._update_table_spray_system(c, self.s)
            self._update_table_passes(c, self.s)
         
    def _update_table_series(self, c: sqlite3.Cursor, s: SeriesData):
        i = s.info    
        c.execute('''INSERT INTO series (id, series, date, time, notes_setup, notes_analyst) VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                        series = excluded.series, date = excluded.date, time = excluded.time, notes_setup = excluded.notes_setup, notes_analyst = excluded.notes_analyst''',
                        (s.id, i.series, i.date, i.time, i.notes_setup, i.notes_analyst))
            
    def _update_table_series_string(self, c: sqlite3.Cursor, s: SeriesData):
        c.execute('''INSERT INTO series_string (series_id, smooth_individual, smooth_average, equalize_integrals, center, simulated_adjascent_passes) VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(series_id) DO UPDATE SET
                        smooth_individual = excluded.smooth_individual, smooth_average = excluded.smooth_average, equalize_integrals = excluded.equalize_integrals, center = excluded.center, simulated_adjascent_passes = excluded.simulated_adjascent_passes''',
                        (s.id, s.string_smooth_individual, s.string_smooth_average, s.string_equalize_integrals, s.string_center, s.string_simulated_adjascent_passes))
    
    def _update_table_flyin(self, c: sqlite3.Cursor, s: SeriesData):
        i = s.info
        c.execute('''INSERT INTO flyin (series_id, flyin_name, flyin_location, flyin_date, flyin_analyst) VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(series_id) DO UPDATE SET
                            flyin_name = excluded.flyin_name, flyin_location = excluded.flyin_location, flyin_date = excluded.flyin_date, flyin_analyst = excluded.flyin_analyst''',
                            (s.id, i.flyin_name, i.flyin_location, i.flyin_date, i.flyin_analyst))
    
    def _update_table_applicator(self, c: sqlite3.Cursor, s: SeriesData):
        i = s.info
        c.execute('''INSERT INTO applicator (series_id, pilot, business, street, city, state, zip, phone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                         ON CONFLICT(series_id) DO UPDATE SET
                         pilot = excluded.pilot, business = excluded.business, street = excluded.street, city = excluded.city, state = excluded.state, zip = excluded.zip, phone = excluded.phone, email = excluded.email''',
                         (s.id, i.pilot, i.business, i.street, i.city, i.state, i.zip, i.phone, i.email))
    
    def _update_table_aircraft(self, c: sqlite3.Cursor, s: SeriesData):
        i = s.info
        c.execute('''INSERT INTO aircraft (series_id, regnum, make, model, wingspan, wingspan_units, winglets) VALUES (?, ?, ?, ?, ?, ?, ?)
                         ON CONFLICT(series_id) DO UPDATE SET
                         regnum = excluded.regnum, make = excluded.make, model = excluded.model, wingspan = excluded.wingspan, wingspan_units = excluded.wingspan_units, winglets = excluded.winglets''',
                         (s.id, i.regnum, i.make, i.model, i.wingspan, i.wingspan_units, i.winglets))
    
    def _update_table_spray_system(self, c: sqlite3.Cursor, s: SeriesData):
        i = s.info
        c.execute('''INSERT INTO spray_system (series_id, swath, swath_adjusted, swath_units, rate, rate_units, pressure, pressure_units, nozzle_type_1, nozzle_size_1, nozzle_deflection_1, nozzle_quantity_1, nozzle_type_2, nozzle_size_2, nozzle_deflection_2, nozzle_quantity_2, boom_width, boom_width_units, boom_drop, boom_drop_units, nozzle_spacing, nozzle_spacing_units) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                         ON CONFLICT(series_id) DO UPDATE SET
                         swath = excluded.swath, swath_adjusted = excluded.swath_adjusted, swath_units = excluded.swath_units, rate = excluded.rate, rate_units = excluded.rate_units, pressure = excluded.pressure, pressure_units = excluded.pressure_units, nozzle_type_1 = excluded.nozzle_type_1, nozzle_size_1 = excluded.nozzle_size_1, nozzle_deflection_1 = excluded.nozzle_deflection_1, nozzle_quantity_1 = excluded.nozzle_quantity_1, nozzle_type_2 = excluded.nozzle_type_2, nozzle_size_2 = excluded.nozzle_size_2, nozzle_deflection_2 = excluded.nozzle_deflection_2, nozzle_quantity_2 = excluded.nozzle_quantity_2, boom_width = excluded.boom_width, boom_width_units = excluded.boom_width_units, boom_drop = excluded.boom_drop, boom_drop_units = excluded.boom_drop_units, nozzle_spacing = excluded.nozzle_spacing, nozzle_spacing_units = excluded.nozzle_spacing_units''',
                         (s.id, i.swath, i.swath_adjusted, i.swath_units, i.rate, i.rate_units, i.pressure, i.pressure_units, i.nozzle_type_1, i.nozzle_size_1, i.nozzle_deflection_1, i.nozzle_quantity_1, i.nozzle_type_2, i.nozzle_size_2, i.nozzle_deflection_2, i.nozzle_quantity_2, i.boom_width, i.boom_width_units, i.boom_drop, i.boom_drop_units, i.nozzle_spacing, i.nozzle_spacing_units))
    
    def _update_table_passes(self, c: sqlite3.Cursor, s: SeriesData):
        p: Pass
        for p in s.passes:
            c.execute('''INSERT INTO passes (id, series_id, pass_name, pass_number, ground_speed, ground_speed_units, spray_height, spray_height_units, pass_heading, wind_direction, wind_speed, wind_speed_units, temperature, temperature_units, humidity, include_in_composite, excitation_wav, emission_wav, trim_left, trim_right, trim_vertical, excitation_data, emission_data, data_loc_units) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                        pass_name = excluded.pass_name, pass_number = excluded.pass_number, ground_speed = excluded.ground_speed, ground_speed_units = excluded.ground_speed_units, spray_height = excluded.spray_height, spray_height_units = excluded.spray_height_units, pass_heading = excluded.pass_heading, wind_direction = excluded.wind_direction, wind_speed = excluded.wind_speed, wind_speed_units = excluded.wind_speed_units, temperature = excluded.temperature, temperature_units = excluded.temperature_units, humidity = excluded.humidity, include_in_composite = excluded.include_in_composite, excitation_wav = excluded.excitation_wav, emission_wav = excluded.emission_wav, trim_left = excluded.trim_left, trim_right = excluded.trim_right, trim_vertical = excluded.trim_vertical, excitation_data = excluded.excitation_data, emission_data = excluded.emission_data, data_loc_units = excluded.data_loc_units''',
                        (p.id, s.id, p.name, p.number, p.ground_speed, p.ground_speed_units, p.spray_height, p.spray_height_units, p.pass_heading, p.wind_direction, p.wind_speed, p.wind_speed_units, p.temperature, p.temperature_units, p.humidity, p.include_in_composite, p.excitation_wav, p.emission_wav, p.trim_l, p.trim_r, p.trim_v, p.data_ex.to_json(), p.data.to_json(), p.data_loc_units))
            self._update_table_spray_cards(c, p)
        # Loop through passes on db, delete any not in series object
        current_ids = [p.id for p in s.passes]
        if len(current_ids) == 0:
            c.execute('''DELETE FROM passes WHERE pass_id = ?''',(p.id,))
        else:
            in_query = '('
            for i, id in enumerate(current_ids):
                if i == 0:
                    in_query += f"'{id}'"
                else:
                    in_query += f", '{id}'"
            in_query += ')'
            c.execute(f'DELETE FROM passes WHERE id NOT IN {in_query}')
            c.execute(f'DELETE FROM spray_cards WHERE pass_id NOT IN {in_query}')
    
    def _update_table_spray_cards(self, c: sqlite3.Cursor, p: Pass):
        card: SprayCard
        for card in p.spray_cards:
            c.execute('''INSERT INTO spray_cards (id, pass_id, name, location, location_units, include_in_composite, threshold_type, threshold_method_grayscale, threshold_grayscale, threshold_method_color, threshold_color_hue_min, threshold_color_hue_max, threshold_color_saturation_min, threshold_color_saturation_max, threshold_color_brightness_min, threshold_color_brightness_max, dpi, spread_method, spread_factor_a, spread_factor_b, spread_factor_c, has_image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(id) DO UPDATE SET
                            name = excluded.name, location = excluded.location, location_units = excluded.location_units, include_in_composite = excluded.include_in_composite, threshold_type = excluded.threshold_type, threshold_method_grayscale = excluded.threshold_method_grayscale, threshold_grayscale = excluded.threshold_grayscale, threshold_method_color = excluded.threshold_method_color, threshold_color_hue_min = excluded.threshold_color_hue_min, threshold_color_hue_max = excluded.threshold_color_hue_max, threshold_color_saturation_min = excluded.threshold_color_saturation_min, threshold_color_saturation_max = excluded.threshold_color_saturation_max, threshold_color_brightness_min = excluded.threshold_color_brightness_min, threshold_color_brightness_max = excluded.threshold_color_brightness_max, dpi = excluded.dpi, spread_method = excluded.spread_method, spread_factor_a = excluded.spread_factor_a, spread_factor_B = excluded.spread_factor_b, spread_factor_c = excluded.spread_factor_c, has_image = excluded.has_image''',
                            (card.id, p.id, card.name, card.location, card.location_units, card.include_in_composite, card.threshold_type, card.threshold_method_grayscale, card.threshold_grayscale, card.threshold_method_color, card.threshold_color_hue[0], card.threshold_color_hue[1], card.threshold_color_saturation[0], card.threshold_color_saturation[1], card.threshold_color_brightness[0], card.threshold_color_brightness[1], card.dpi, card.spread_method, card.spread_factor_a, card.spread_factor_b, card.spread_factor_c, card.has_image))
        # Loop through cards on db, delete any not in pass object
        current_ids = [sc.id for sc in p.spray_cards]
        if len(current_ids) == 0:
            c.execute('''DELETE FROM spray_cards WHERE pass_id = ?''',(p.id,))
        else:
            in_query = '('
            for i, id in enumerate(current_ids):
                if i == 0:
                    in_query += f"'{id}'"
                else:
                    in_query += f", '{id}'"
            in_query += ')'
            c.execute(f'DELETE FROM spray_cards WHERE pass_id = "{p.id}" AND id NOT IN {in_query}')
            