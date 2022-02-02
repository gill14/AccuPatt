from typing import List

import pandas as pd
from accupatt.helpers.dBBridge import load_from_db
from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.models.sprayCard import SprayCard
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows


def safe_report(filesToInclude: List[str], saveFile: str):
    wb = Workbook()
    # Sheet created by default
    ws = wb.active
    # Static labels
    ws.title = 'S.A.F.E. Report'
    ws['B1'] = 'Event:'
    ws['B2'] = 'Location:'
    ws['B3'] = 'Date:'
    ws['B4'] = 'Analyst:'
    ws['B5'] = '# Passes:'
    header = ['Pilot Last','Pilot First','Business Name','Operator Name','Opr Fname',
              'A/C Reg','Aircraft Model','# Passes','Business Address','City',
              'St','Zip Code','Phone*','E-mail*']
    for i, head in enumerate(header):
        ws.cell(6,i+1,head)
    sum_passes = 0
    next_row_avail = 7
    for i, file in enumerate(filesToInclude):
        s = SeriesData()
        load_from_db(file=file, s=s)
        # Flyin - Will overwrite each time
        ws['C1'] = s.info.flyin_name
        ws['C2'] = s.info.flyin_location
        ws['C3'] = s.info.flyin_date
        ws['C4'] = s.info.flyin_analyst
        row = next_row_avail
        # Check if row with Regnum already exists
        for cell in ws['F']:
            if cell.value == s.info.regnum:
                row = cell.row
        
        # Line Entry for each file
        ws.cell(row, 1, s.info.pilot.split(' ',1)[1])
        ws.cell(row, 2, s.info.pilot.split(' ',1)[0])
        ws.cell(row, 3, s.info.business)
        ws.cell(row, 6, s.info.regnum)
        ws.cell(row, 7, s.info.make + ' ' + s.info.model)
        ws.cell(row, 9, s.info.street)
        ws.cell(row, 10, s.info.city)
        ws.cell(row, 11, s.info.state)
        ws.cell(row, 12, s.info.zip)
        ws.cell(row, 13, s.info.phone)
        ws.cell(row, 14, s.info.email)
        # Increment next_row_avail if a new regnum
        if row == next_row_avail:
            next_row_avail += 1
            ws.cell(row, 8, len(s.passes))
        else:
            ws.cell(row, 8, ws.cell(row, 8).value + len(s.passes))
        # Contribute Passes to Sum of Passes
        sum_passes += len(s.passes)
    ws['C5'] = sum_passes
    # Save it
    wb.save(saveFile)
    
def export_all_to_excel(series: SeriesData, saveFile: str):
    s = series
    i = s.info
    
    wb = Workbook()
    # AppInfo Sheet
    ws = wb.active
    ws.title = 'App Info'
    # Table Series
    labels = ['series','created','modified','notes_setup','notes_analyst']
    vals = [i.series,i.created,i.modified,i.notes_setup,i.notes_analyst]
    # Table Flyin
    labels.extend(['flyin_name','flyin_location','flyin_date','flyin_analyst'])
    vals.extend([i.flyin_name,i.flyin_location,i.flyin_date,i.flyin_analyst])
    # Table Applicator
    labels.extend(['pilot','business','street','city','state','zip','phone','email'])
    vals.extend([i.pilot,i.business,i.street,i.city,i.state,i.zip,i.phone,i.email])
    # Table Aircraft
    labels.extend(['regnum','make','model','wingspan','wingspan_units','winglets'])
    vals.extend([i.regnum,i.make,i.model,i.wingspan,i.wingspan_units,i.winglets])
    # Table Spray System
    labels.extend(['swath','swath_adjusted','swath_units','rate','rate_units','pressure','pressure_units','boom_width','boom_width_units','boom_drop','boom_drop_units','nozzle_spacing','nozzle_spacing_units']) 
    vals.extend([i.swath,i.swath_adjusted,i.swath_units,i.rate,i.rate_units,i.pressure,i.pressure_units, i.boom_width,i.boom_width_units,i.boom_drop,i.boom_drop_units,i.nozzle_spacing,i.nozzle_spacing_units])
    # Table Nozzles
    for n in i.nozzles:
        labels.extend([f'Nozzle {n.id} type',f'Nozzle {n.id} size',f'Nozzle {n.id} deflection',f'Nozzle {n.id} quantity'])
        vals.extend([n.type,n.size,n.deflection,n.quantity])
    # Table Series String
    labels.extend(['center_average','smooth_average','equalize_integrals','simulated_adjascent_passes'])
    vals.extend([s.string_average_center_method,s.string_average_smooth,s.string_equalize_integrals,s.string_simulated_adjascent_passes])
    # plot it 
    for i, (label, val) in enumerate(zip(labels,vals)):
        ws.cell(i+1, 1, label)
        ws.cell(i+1, 2, val)
    for cell in ws['A']:
        cell.style = 'Pandas'
    
    # Passes Sheet
    ws = wb.create_sheet('Passes')
    labels = ['pass_name','pass_number','ground_speed','ground_speed_units','spray_height','spray_height_units','pass_heading','wind_direction','wind_speed','wind_speed_units','temperature','temperature_units','humidity','include_in_composite','excitation_wav','emission_wav','trim_left','trim_right','trim_vertical', 'center', 'smooth', 'data_loc_units']
    for i, label in enumerate(labels):
        ws.cell(i+1,1,label)
    p: Pass
    for j, p in enumerate(s.passes):
        vals = [p.name,p.number,p.ground_speed,p.ground_speed_units,p.spray_height,p.spray_height_units,p.pass_heading,p.wind_direction,p.wind_speed,p.wind_speed_units,p.temperature,p.temperature_units,p.humidity,p.include_in_composite,p.excitation_wav,p.emission_wav,p.trim_l,p.trim_r,p.trim_v,p.string_center_method, p.string_smooth, p.data_loc_units]
        for i, val in enumerate(vals):
            ws.cell(i+1, j+2, val)
    for cell in ws['A'] + ws[1]:
        cell.style = 'Pandas'
    
            
    # String Sheet
    ws = wb.create_sheet('String Data')
    # Join all df's
    df = pd.DataFrame()
    for i, p in enumerate(s.passes):
        df = pd.concat([df, p.data_ex, p.data], axis=1)
    for j, p in enumerate(s.passes):
        ws.cell(1,1+(j*4),p.name)
        ws.merge_cells(start_row=1,start_column=1+(j*4),end_row=1,end_column=4+(j*4))
        ws.cell(2,1+(j*4),'Excitation')
        ws.merge_cells(start_row=2,start_column=1+(j*4),end_row=2,end_column=2+(j*4))
        ws.cell(2, 3+(j*4), 'Emission')
        ws.merge_cells(start_row=2,start_column=3+(j*4),end_row=2,end_column=4+(j*4))
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    for cell in ws[1] + ws[2] +ws[3]:
        cell.style = 'Pandas'
    
    # Card Sheet
    ws = wb.create_sheet('Card Data')
    col_pass_name = 2
    for j, p in enumerate(s.passes):
        if len(p.spray_cards) > 0:
            ws.cell(1, col_pass_name, p.name)
            ws.merge_cells(start_row=1,start_column=col_pass_name,end_row=1,end_column=col_pass_name+len(p.spray_cards)-1)
            for k, c in enumerate(p.spray_cards):
                c: SprayCard
                labels = ['name','has_image','include_in_composite','location','units','threshold_type','threshold_method_grayscale','threshold_grayscale','threshold_method_color','threshold_color_hue_min','threshold_color_hue_max','threshold_color_saturation_min','threshold_color_saturation_max','threshold_color_brightness_min','threshold_color_brightness_max','dpi','spread_method','sf_a','sf_b','sf_c']
                vals = [c.name,c.has_image,c.include_in_composite,c.location,c.location_units,c.threshold_type,c.threshold_method_grayscale, c.threshold_grayscale, c.threshold_method_color, c.threshold_color_hue[0], c.threshold_color_hue[1], c.threshold_color_saturation[0], c.threshold_color_saturation[1], c.threshold_color_brightness[0], c.threshold_color_brightness[1], c.dpi, c.spread_method, c.spread_factor_a, c.spread_factor_b, c.spread_factor_c]
                for i, (label, val) in enumerate(zip(labels,vals)):
                    ws.cell(2+i,1,label)
                    ws.cell(2+i,col_pass_name+k,val)
            col_pass_name += len(p.spray_cards)
    
    for cell in ws['A'] + ws[1] + ws[2]:
        cell.style = 'Pandas'
        
    # Save it
    wb.save(saveFile)
