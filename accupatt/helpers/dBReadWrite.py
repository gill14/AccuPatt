from PyQt5.QtWidgets import QFileDialog
import pandas as pd
import os

import sqlite3

import accupatt.config as cfg
from accupatt.models.seriesData import SeriesData
from accupatt.models.appInfo import AppInfo
from accupatt.models.passData import Pass
from accupatt.models.sprayCard import SprayCard

class DBReadWrite:

    def read_from_db(parent_window, last_directory):
        #file, _ = QFileDialog.getOpenFileName(parent_window, 'Open file', last_directory, "AccuPatt files (*.db)")
        file = '/Users/gill14/OneDrive - University of Illinois - Urbana/AccuProjects/Python Projects/AccuPatt/testing/N802ET 03.db'
        
        try:
            # Opens a file called mydb with a SQLite3 DB
            conn = sqlite3.connect(file)
            # Get a cursor object
            c = conn.cursor()
            # Series Table
            c.execute('''SELECT id, series, date, time, notes FROM series''')
            data = c.fetchone()
            s = SeriesData(id=data[0])
            s.info.series = data[1]
            s.info.date = data[2]
            s.info.time = data[3]
            s.info.notes = data[4]
            # Series String Table
            c.execute('''SELECT smooth_individual, smooth_average, equalize_integrals, center, simulated_adjascent_passes FROM series_string WHERE series_id = ?''', (s.id,))
            s.string_smooth_individual = data[0]
            s.string_smooth_average = data[1]
            s.string_equalize_integrals = data[2]
            s.string_center = data[3]
            s.string_simulated_adjascent_passes = data[4]
            #Flyin Table
            c.execute('''SELECT flyin_name, flyin_location, flyin_date, flyin_analyst FROM flyin WHERE series_id = ?''', (s.id,))
            data = c.fetchone()
            s.info.flyin_name = data[0]
            s.info.flyin_location = data[1]
            s.info.flyin_date = data[2]
            s.info.flyin_analyst = data[3]
            #Applicator Table
            c.execute('''SELECT pilot, business, street, city, state, zip, phone, email FROM applicator WHERE series_id = ?''',(s.id,))
            data = c.fetchone()
            s.info.pilot = data[0]
            s.info.business = data[1]
            s.info.street = data[2]
            s.info.city = data[3]
            s.info.state = data[4]
            s.info.zip = data[5]
            s.info.phone = data[6]
            s.info.email = data[7]
            #Aircraft Table
            c.execute('''SELECT regnum, make, model, wingspan, wingspan_units, winglets FROM aircraft WHERE series_id = ?''', (s.id,))
            data = c.fetchone()
            s.info.regnum = data[0]
            s.info.make = data[1]
            s.info.model = data[2]
            s.info.wingspan = data[3]
            s.info.wingspan_units = data[4]
            s.info.winglets = data[5]
            #Spray System Table
            c.execute('''SELECT swath, swath_adjusted, swath_units, rate, rate_units, pressure, pressure_units, nozzle_type_1, nozzle_size_1, nozzle_deflection_1, nozzle_quantity_1, nozzle_type_2, nozzle_size_2, nozzle_deflection_2, nozzle_quantity_2, boom_width, boom_width_units, boom_drop, boom_drop_units, nozzle_spacing, nozzle_spacing_units FROM spray_system WHERE series_id = ?''',(s.id,))
            data = c.fetchone()
            s.info.swath = data[0]
            s.info.swath_adjusted = data[1]
            s.info.swath_units = data[2]
            s.info.rate = data[3]
            s.info.rate_units = data[4]
            s.info.pressure = data[5]
            s.info.pressure_units = data[6]
            s.info.nozzle_type_1 = data[7]
            s.info.nozzle_size_1 = data[8]
            s.info.nozzle_deflection_1 = data[9]
            s.info.nozzle_quantity_1 = data[10]
            s.info.nozzle_type_2 = data[11]
            s.info.nozzle_size_2 = data[12]
            s.info.nozzle_deflection_2 = data[13]
            s.info.nozzle_quantity_2 = data[14]
            s.info.boom_width = data[15]
            s.info.boom_width_units = data[16]
            s.info.boom_drop = data[17]
            s.info.boom_drop_units = data[18]
            s.info.nozzle_spacing = data[19]
            s.info.nozzle_spacing_units = data[20]
            #Passes Table
            c.execute('''SELECT id, pass_number, ground_speed, ground_speed_units, spray_height, spray_height_units, pass_heading, wind_direction, wind_speed, wind_speed_units, temperature, temperature_units, humidity, include_in_composite, excitation_wav, emission_wav, trim_left, trim_right, trim_vertical, excitation_data, emission_data, data_loc_units FROM passes WHERE series_id = ?''',(s.id,))
            data = c.fetchall()
            for row in data:
                p = Pass(id=row[0], number=row[1])
                p.ground_speed = row[2]
                p.ground_speed_units = row[3]
                p.spray_height = row[4]
                p.spray_height_units = row[5]
                p.pass_heading = row[6]
                p.wind_direction = row[7]
                p.wind_speed = row[8]
                p.wind_speed_units = row[9]
                p.temperature = row[10]
                p.temperature_units = row[11]
                p.humidity = row[12]
                p.include_in_composite = row[13]
                p.excitation_wav = row[14]
                p.emission_wav = row[15]
                p.trim_l = row[16]
                p.trim_r = row[17]
                p.trim_v = row[18]
                p.data_ex = pd.read_json(row[19])
                p.data = pd.read_json(row[20])
                p.data_loc_units = row[21]
                #Spray Cards Table
                c.execute('''SELECT id, name, location, include_in_composite, threshold_type, threshold_method_color, threshold_method_grayscale, threshold_grayscale, threshold_color_hue_min, threshold_color_hue_max, threshold_color_saturation_min, threshold_color_saturation_max, threshold_color_brightness_min, threshold_color_brightness_max, dpi, spread_method, spread_factor_a, spread_factor_b, spread_factor_c, has_image FROM spray_cards WHERE pass_id = ?''',(p.id,))
                cards = c.fetchall()
                for row in cards:
                    c = SprayCard(id=row[0], name=row[1], filepath=str(file))
                    c.location = row[2]
                    c.include_in_composite = row[3]
                    c.threshold_type = row[4]
                    c.threshold_method_color = row[5]
                    c.threshold_method_grayscale = row[6]
                    c.threshold_grayscale = row[7]
                    c.threshold_color_hue = [row[8],row[9]]
                    c.threshold_color_saturation = [row[10],row[11]]
                    c.threshold_color_brightness = [row[12],row[13]]
                    c.dpi = row[14]
                    c.spread_method = row[15]
                    c.spread_factor_a = row[16]
                    c.spread_factor_b = row[17]
                    c.spread_factor_c = row[18]
                    c.has_image = row[19]
                    p.spray_cards.append(c)
                s.passes.append(p)
        # Catch the exception
        except Exception as e:
            # Roll back any change if something goes wrong
            conn.rollback()
            raise e
        finally:
            # Close the db connection
            conn.close()
        
        
        return file, s

    def write_to_db(filePath, seriesData):
        #db_filename = os.path.splitext(filePath)[0]+'.db'
        schema_filename = os.path.join(os.getcwd(), 'accupatt', 'helpers', 'schema.sql')
        with sqlite3.connect(filePath) as conn:
            with open(schema_filename, 'rt') as f:
                    schema = f.read()
            conn.executescript(schema)
            #if not os.path.exists(filePath):
                
            #Update From AppInfo Object
            info = seriesData.info
            assert isinstance(info, AppInfo)
            #Series    
            conn.execute('''INSERT INTO series (id, series, date, time, notes) VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(id) DO UPDATE SET
                            series = excluded.series, date = excluded.date, time = excluded.time, notes = excluded.notes''',
                            (seriesData.id, info.series, info.date, info.time, info.notes))
            #Series String
            conn.execute('''INSERT INTO series_string (series_id, smooth_individual, smooth_average, equalize_integrals, center, simulated_adjascent_passes) VALUES (?, ?, ?, ?, ?, ?)
                         ON CONFLICT(series_id) DO UPDATE SET
                         smooth_individual = excluded.smooth_individual, smooth_average = excluded.smooth_average, equalize_integrals = excluded.equalize_integrals, center = excluded.center, simulated_adjascent_passes = excluded.simulated_adjascent_passes''',
                         (seriesData.id, seriesData.string_smooth_individual, seriesData.string_smooth_average, seriesData.string_equalize_integrals, seriesData.string_center, seriesData.string_simulated_adjascent_passes))
            #Flyin    
            conn.execute('''INSERT INTO flyin (series_id, flyin_name, flyin_location, flyin_date, flyin_analyst) VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(series_id) DO UPDATE SET
                            flyin_name = excluded.flyin_name, flyin_location = excluded.flyin_location, flyin_date = excluded.flyin_date, flyin_analyst = excluded.flyin_analyst''',
                            (seriesData.id, info.flyin_name, info.flyin_location, info.flyin_date, info.flyin_analyst))
            #Applicator
            conn.execute('''INSERT INTO applicator (series_id, pilot, business, street, city, state, zip, phone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                         ON CONFLICT(series_id) DO UPDATE SET
                         pilot = excluded.pilot, business = excluded.business, street = excluded.street, city = excluded.city, state = excluded.state, zip = excluded.zip, phone = excluded.phone, email = excluded.email''',
                         (seriesData.id, info.pilot, info.business, info.street, info.city, info.state, info.zip, info.phone, info.email))
            #Aircraft
            conn.execute('''INSERT INTO aircraft (series_id, regnum, make, model, wingspan, wingspan_units, winglets) VALUES (?, ?, ?, ?, ?, ?, ?)
                         ON CONFLICT(series_id) DO UPDATE SET
                         regnum = excluded.regnum, make = excluded.make, model = excluded.model, wingspan = excluded.wingspan, wingspan_units = excluded.wingspan_units, winglets = excluded.winglets''',
                         (seriesData.id, info.regnum, info.make, info.model, info.wingspan, info.wingspan_units, info.winglets))
            #Spray System
            conn.execute('''INSERT INTO spray_system (series_id, swath, swath_adjusted, swath_units, rate, rate_units, pressure, pressure_units, nozzle_type_1, nozzle_size_1, nozzle_deflection_1, nozzle_quantity_1, nozzle_type_2, nozzle_size_2, nozzle_deflection_2, nozzle_quantity_2, boom_width, boom_width_units, boom_drop, boom_drop_units, nozzle_spacing, nozzle_spacing_units) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                         ON CONFLICT(series_id) DO UPDATE SET
                         swath = excluded.swath, swath_adjusted = excluded.swath_adjusted, swath_units = excluded.swath_units, rate = excluded.rate, rate_units = excluded.rate_units, pressure = excluded.pressure, pressure_units = excluded.pressure_units, nozzle_type_1 = excluded.nozzle_type_1, nozzle_size_1 = excluded.nozzle_size_1, nozzle_deflection_1 = excluded.nozzle_deflection_1, nozzle_quantity_1 = excluded.nozzle_quantity_1, nozzle_type_2 = excluded.nozzle_type_2, nozzle_size_2 = excluded.nozzle_size_2, nozzle_deflection_2 = excluded.nozzle_deflection_2, nozzle_quantity_2 = excluded.nozzle_quantity_2, boom_width = excluded.boom_width, boom_width_units = excluded.boom_width_units, boom_drop = excluded.boom_drop, boom_drop_units = excluded.boom_drop_units, nozzle_spacing = excluded.nozzle_spacing, nozzle_spacing_units = excluded.nozzle_spacing_units''',
                         (seriesData.id, info.swath, info.swath_adjusted, info.swath_units, info.rate, info.rate_units, info.pressure, info.pressure_units, info.nozzle_type_1, info.nozzle_size_1, info.nozzle_deflection_1, info.nozzle_quantity_1, info.nozzle_type_2, info.nozzle_size_2, info.nozzle_deflection_2, info.nozzle_quantity_2, info.boom_width, info.boom_width_units, info.boom_drop, info.boom_drop_units, info.nozzle_spacing, info.nozzle_spacing_units))

            for p in seriesData.passes:
                assert isinstance(p, Pass)
                conn.execute('''INSERT INTO passes (id, series_id, pass_number, ground_speed, ground_speed_units, spray_height, spray_height_units, pass_heading, wind_direction, wind_speed, wind_speed_units, temperature, temperature_units, humidity, include_in_composite, excitation_wav, emission_wav, trim_left, trim_right, trim_vertical, excitation_data, emission_data, data_loc_units) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(id) DO UPDATE SET
                            ground_speed = excluded.ground_speed, ground_speed_units = excluded.ground_speed_units, spray_height = excluded.spray_height, spray_height_units = excluded.spray_height_units, pass_heading = excluded.pass_heading, wind_direction = excluded.wind_direction, wind_speed = excluded.wind_speed, wind_speed_units = excluded.wind_speed_units, temperature = excluded.temperature, temperature_units = excluded.temperature_units, humidity = excluded.humidity, include_in_composite = excluded.include_in_composite, excitation_wav = excluded.excitation_wav, emission_wav = excluded.emission_wav, trim_left = excluded.trim_left, trim_right = excluded.trim_right, trim_vertical = excluded.trim_vertical, excitation_data = excluded.excitation_data, emission_data = excluded.emission_data, data_loc_units = excluded.data_loc_units''',
                            (p.id, seriesData.id, p.number, p.ground_speed, p.ground_speed_units, p.spray_height, p.spray_height_units, p.pass_heading, p.wind_direction, p.wind_speed, p.wind_speed_units, p.temperature, p.temperature_units, p.humidity, p.include_in_composite, p.excitation_wav, p.emission_wav, p.trim_l, p.trim_r, p.trim_v, p.data_ex.to_json(), p.data.to_json(), p.data_loc_units))
                if isinstance(p.spray_cards, type(None)):
                    continue
                for card in p.spray_cards:
                    assert isinstance(card, SprayCard)
                    img = None
                    #Fix after done with intermediate file type (folders)
                    if not isinstance(card.filepath, type(None)):
                        img = open(card.filepath, 'rb').read()
                        img = sqlite3.Binary(img)
                    conn.execute('''INSERT INTO spray_cards (id, pass_id, name, location, include_in_composite, threshold_type, threshold_method_color, threshold_method_grayscale, threshold_grayscale, threshold_color_hue_min, threshold_color_hue_max, threshold_color_saturation_min, threshold_color_saturation_max, threshold_color_brightness_min, threshold_color_brightness_max, dpi, spread_method, spread_factor_a, spread_factor_b, spread_factor_c, has_image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                 ON CONFLICT(id) DO UPDATE SET
                                 name = excluded.name, location = excluded.location, include_in_composite = excluded.include_in_composite, threshold_type = excluded.threshold_type, threshold_method_color = excluded.threshold_method_color, threshold_method_grayscale = excluded.threshold_method_grayscale, threshold_grayscale = excluded.threshold_grayscale, threshold_color_hue_min = excluded.threshold_color_hue_min, threshold_color_hue_max = excluded.threshold_color_hue_max, threshold_color_saturation_min = excluded.threshold_color_saturation_min, threshold_color_saturation_max = excluded.threshold_color_saturation_max, threshold_color_brightness_min = excluded.threshold_color_brightness_min, threshold_color_brightness_max = excluded.threshold_color_brightness_max, dpi = excluded.dpi, spread_method = excluded.spread_method, spread_factor_a = excluded.spread_factor_a, spread_factor_B = excluded.spread_factor_b, spread_factor_c = excluded.spread_factor_c, has_image = excluded.has_image''',
                                 (card.id, p.id, card.name, card.location, card.include_in_composite, card.threshold_type, card.threshold_method_color, card.threshold_method_grayscale, card.threshold_grayscale, card.threshold_color_hue[0], card.threshold_color_hue[1], card.threshold_color_saturation[0], card.threshold_color_saturation[1], card.threshold_color_brightness[0], card.threshold_color_brightness[1], card.dpi, card.spread_method, card.spread_factor_a, card.spread_factor_b, card.spread_factor_c, card.has_image))
