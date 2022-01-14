import os, io
import openpyxl
from openpyxl_image_loader import SheetImageLoader
import pandas as pd

import accupatt.config as cfg
from accupatt.helpers.dBBridge import DBBridge
from accupatt.models.seriesData import SeriesData
from accupatt.models.appInfo import AppInfo
from accupatt.models.passData import Pass
from accupatt.models.sprayCard import SprayCard

class DataFileImporter:
    
    def convert_xlsx_to_db(file):
        #Load in Series Data
        s = DataFileImporter.load_from_accupatt_1_file(file)
        #Write to DB (same dir as original xlsx)
        file_db = os.path.splitext(file)[0]+'.db'
        DBBridge(file_db, s).save_to_db()
        #Append Images
        wb = openpyxl.load_workbook(file)
        if not 'Card Data' in wb.sheetnames:
            return s
        sh = wb['Card Data']
        on_pass = int(sh['B2'].value)
        # Loop over declard cards and save images to db if has_image
        p: Pass = s.passes[on_pass-1]
        c: SprayCard
        for c in p.spray_cards:
            c.filepath = file_db
            if c.has_image:
                # Get the image from applicable sheet
                image_loader = SheetImageLoader(wb[c.name])
                image = image_loader.get('A1')
                # Conver to bytestream
                stream = io.BytesIO()
                image.save(stream, format="PNG")
                # Save it to the database
                c.save_image_to_file(stream.getvalue())
                # Reclaim resources
                stream.close()
                
        return s
    
    def load_from_accupatt_1_file(file):
        #indicator for metric
        isMetric = False

        #Load entire WB into dict of sheets
        df_map = pd.read_excel(file, sheet_name=None, header=None)
  
        #initialize SeriesData object to store all info
        s = SeriesData()

        #Pull data from Fly-In Tab
        df = df_map['Fly-In Data'].fillna('')
        for row in range(df.shape[0]):
            if row == 0: s.info.flyin_name = df.iat[row,0]
            if row == 1: s.info.flyin_location = df.iat[row,0]
            if row == 2: s.info.flyin_date = df.iat[row,0]
            if row == 3: s.info.flyin_analyst = df.iat[row,0]

        #Pull data from AppInfo Tab
        df = df_map['Aircraft Data'].fillna('')
        for row in range(df.shape[0]):
            #string value from col 1
            val = str(df.iat[row,1])
            #string value from col 2
            if df.shape[1] > 2: val2 = DataFileImporter.strip_num(df.iat[row,2])
            #asign as needed
            if row == 0: s.info.pilot = val
            if row == 1: s.info.business = val
            if row == 2: s.info.phone = val
            if row == 3: s.info.street = val
            if row == 4: s.info.city = val
            if row == 5: s.info.state = val
            if row == 5 and df.shape[1] > 2: s.info.zip = val2
            if row == 6: s.info.regnum = val
            if row == 7: s.info.series = val
            if row == 8: s.info.make = val
            if row == 9: s.info.model = val
            if row == 10: s.info.nozzle_type_1 = val
            if row == 11: s.info.set_nozzle_quantity_1(val)
            if row == 12: s.info.nozzle_size_1 = DataFileImporter.strip_num(val)
            if row == 13: s.info.nozzle_deflection_1 = DataFileImporter.strip_num(val)
            if row == 14: s.info.nozzle_type_2 = val
            if row == 15: s.info.set_nozzle_quantity_2(val)
            if row == 16: s.info.nozzle_size_2 = DataFileImporter.strip_num(val)
            if row == 17: s.info.nozzle_deflection_2 = DataFileImporter.strip_num(val)
            if row == 18: s.info.set_pressure(val)
            if row == 19: s.info.set_rate(val)
            if row == 20: s.info.set_swath(val)
            if row == 20 and df.shape[1] > 2: s.info.set_swath_adjusted(val2)
            if row == 26: s.info.time = val
            if row == 27: s.info.set_wingspan(val)
            if row == 28: s.info.set_boom_width(val)
            if row == 30: s.info.set_boom_drop(val)
            if row == 31: s.info.set_nozzle_spacing(val)
            if row == 32: s.info.winglets = val
            if row == 33: s.info.notes_setup = val
            if row == 35:
                isMetric = (val == 'True')
                if isMetric:
                    s.info.swath_units = 'm'
                    s.info.rate_units = 'l/ha'
                    s.info.pressure_units = 'bar'
                    s.info.wingspan_units = 'm'
                    s.info.boom_width_units = 'm'
                    s.info.boom_drop_units = 'cm'
                    s.info.nozzle_spacing_units = 'cm'
                else:
                    s.info.swath_units = 'ft'
                    s.info.rate_units = 'gpa'
                    s.info.pressure_units = 'psi'
                    s.info.wingspan_units = 'ft'
                    s.info.boom_width_units = 'ft'
                    s.info.boom_drop_units = 'in'
                    s.info.nozzle_spacing_units = 'in'

        #Pull data from Series Data tab
        df = df_map['Series Data'].fillna('')
        df.columns = df.iloc[0]
        #Clear any stored individual passes
        s.passes = []
        #Search for any active passes and create entries in seriesData.passes dict
        for column in df.columns[1:]:
            if not str(df.at[1,column]) == '':
                p = Pass(number = df.columns.get_loc(column))
                p.set_ground_speed(str(df.at[1,column]))
                p.set_spray_height(str(df.at[2,column]))
                p.set_pass_heading(str(df.at[3,column]))
                p.set_wind_direction(str(df.at[4,column]))
                p.set_wind_speed(str(df.at[5,column]))
                p.set_temperature(str(df.at[6,'Pass 1']))
                p.set_humidity(str(df.at[7,'Pass 1']))
                p.temperature_units = '°C' if isMetric else '°F'
                p.ground_speed_units = 'kph' if isMetric else 'mph'
                p.spray_height_units = 'm' if isMetric else 'ft'
                p.wind_speed_units = 'kph' if isMetric else 'mph'
                p.data_loc_units = 'm' if isMetric else 'ft'
                s.passes.append(p)

        #Pull data from Pattern Data tab
        df = df_map['Pattern Data'].fillna('')
        if df.shape[1] < 13: df['nan'] = ''
        #Make new empty dataframe for info
        df_info = pd.DataFrame({'Pass 1':[], 'Pass 2':[], 'Pass 3':[], 'Pass 4':[], 'Pass 5':[], 'Pass 6':[]})
        #Append trims
        dd = df.iloc[0:3,[2, 4, 6, 8, 10, 12]]
        dd.columns = ['Pass 1', 'Pass 2', 'Pass 3', 'Pass 4', 'Pass 5', 'Pass 6']
        df_info = df_info.append(dd, ignore_index=True)
        #Append string length and sample length
        dd = df.iloc[1:2,[1, 3, 5, 7, 9, 11]]
        dd.columns = ['Pass 1', 'Pass 2', 'Pass 3', 'Pass 4', 'Pass 5', 'Pass 6']
        df_info = df_info.append(dd, ignore_index=True)
        #Make a dataframe for emission data points
        df_emission = pd.DataFrame({'loc':[], 'Pass 1':[], 'Pass 2':[], 'Pass 3':[], 'Pass 4':[], 'Pass 5':[], 'Pass 6':[]})
        dd = df.iloc[5:,[0,2,4,6,8,10,12]]
        dd.columns = ['loc', 'Pass 1', 'Pass 2', 'Pass 3', 'Pass 4', 'Pass 5', 'Pass 6']
        df_emission = df_emission.append(dd, ignore_index=True)

        #Make a dataframe for excitation data points
        df_excitation = pd.DataFrame({'loc':[], 'Pass 1':[], 'Pass 2':[], 'Pass 3':[], 'Pass 4':[], 'Pass 5':[], 'Pass 6':[]})
        dd = df.iloc[5:,[0,1,3,5,7,9,11]]
        dd.columns = ['loc', 'Pass 1', 'Pass 2', 'Pass 3', 'Pass 4', 'Pass 5', 'Pass 6']
        df_excitation = df_excitation.append(dd, ignore_index=True)

        #Pull patterns and place them into seriesData.passes dicts by name (created above)
        p: Pass
        for p in s.passes:
            p.trim_l = 0 if df_info.at[0,p.name] == '' else int(df_info.at[0,p.name])
            p.trim_r = 0 if df_info.at[1,p.name] == '' else int(df_info.at[1,p.name])
            p.trim_v = 0 if df_info.at[2,p.name] == '' else df_info.at[2,p.name]
            p.data = df_emission[['loc',p.name]]
            p.data_ex = df_excitation[['loc',p.name]]                

        #Create SprayCards if applicable
        wb = openpyxl.load_workbook(file, read_only=True)
        if not 'Card Data' in wb.sheetnames:
            return s
        sh = wb['Card Data']
        spacing = sh['B1'].value
        on_pass = int(sh['B2'].value)
        spread_method_text = sh['B3'].value
        spread_method = cfg.SPREAD_METHOD_ADAPTIVE
        if spread_method_text == cfg.SPREAD_METHOD_DIRECT_STRING:
            spread_method = cfg.SPREAD_METHOD_DIRECT
        if spread_method_text == cfg.SPREAD_METHOD_NONE_STRING:
            spread_method = cfg.SPREAD_METHOD_NONE
        spread_a = sh['B4'].value
        spread_b = sh['B5'].value
        spread_c = sh['B6'].value
        #Card Pass
        p: Pass = s.passes[on_pass-1]
        for col in range(5,14):
            if not sh.cell(row=1,column=col).value:
                continue
            c = SprayCard(name=sh.cell(row=1,column=col).value)
            c.location = (col-9)*spacing
            c.has_image = 1 if sh.cell(row=2,column=col).value else 0
            c.include_in_composite = 1 if sh.cell(row=3,column=col).value else 0
            if c.has_image:
                c.threshold_grayscale = sh.cell(row=4,column=col).value
            c.threshold_type = cfg.THRESHOLD_TYPE_GRAYSCALE
            c.spread_method = spread_method
            c.spread_factor_a = spread_a
            c.spread_factor_b = spread_b
            c.spread_factor_c = spread_c
            p.spray_cards.append(c)
                
        return s
    
    def strip_num(x, noneIsZero = False) -> str:
        if type(x) is str:
            if x == '':
                if noneIsZero:
                    x = 0
                else:
                    return ''
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return str(float(x))
    