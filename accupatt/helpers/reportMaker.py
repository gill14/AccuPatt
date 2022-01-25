from io import BytesIO

from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph, Table, TableStyle
from reportlab.platypus.flowables import Flowable
from svglib.svglib import svg2rlg


class ReportMaker:

    def makeReport(self, seriesData: SeriesData, mplCanvasOverlay, mplCanvasAverage, mplCanvasRT, mplCanvasBF, tableView):
        s = seriesData
        i = s.info
        
        c = canvas.Canvas('test2.pdf',pagesize=letter)
        width, height = letter
        c.setLineCap(2)
        c.setFont("Helvetica", 8)
        style = ParagraphStyle(
            name='normal',
            fontName='Helvetica',
            fontSize=8,
            leading=10
        )

        tablestyle = [
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.lightgrey, None, (2,2,2)),
            ('FONTSIZE',(0,0),(-1,-1), 8),
            ('LEADING',(0,0),(-1,-1), 9.5),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('BOTTOMPADDING',(0,0),(-1,-1),1),
            ('LEFTPADDING',(1,0),(-1,-1),4),
            ('RIGHTPADDING',(1,0),(-1,-1),4),
            ('TOPPADDING',(0,0),(-1,-1),1),
            ('BACKGROUND',(0,0),(0,-1),colors.lightgrey),
            ('BOX', (0,0), (-1,-1), 0.25, colors.black),
            ('SPAN',(0,0),(0,-1)),
        ]

        list = []
        
        business = [
            [TTR('Applicator'), i.pilot],
            ['', i.business],
            ['', i.addressLine1()],
            ['', i.addressLine2()],
            ['', i.string_phone()],
            ['', i.email]
        ]
        list.append(Table(business, style=tablestyle))

        aircraft = [
            [TTR('Aircraft'), 'Reg. #:', i.regnum],
            ['', 'Series:', i.series],
            ['', 'Make:', i.make],
            ['', 'Model:', i.model],
            ['', 'Wingspan:', i.string_wingspan()],
            ['', 'Winglets?:', i.winglets]
        ]
        tablestyle_alt = tablestyle + [
            ('BACKGROUND',(1,0),(-1,1),colors.palegreen),
        ]
        list.append(Table(aircraft,style=tablestyle_alt))

        spray_system = [
            [TTR('Spray System'), 'Target Swath:', i.string_swath()],
            ['', 'Target Rate:', i.string_rate()],
            ['', 'Boom Pressure:', i.string_pressure()],
            ['', 'Boom Width:', i.string_boom_width()],
            ['', 'Boom Drop:', i.string_boom_drop()],
            ['', 'Nozzle Spacing:', i.string_nozzle_spacing()]
        ]
        list.append(Table(spray_system,style=tablestyle))

        nozzle1 = i.nozzles[0].as_string_tuple() if len(i.nozzles) > 0 else ('','')
        nozzle2 = i.nozzles[1].as_string_tuple() if len(i.nozzles) > 1 else ('','')
        nozzles = [
            [TTR('Nozzles'), 'Set #1'],
            ['', f'{nozzle1[0]}'],
            ['', f'{nozzle1[1]}'],
            ['', 'Set #2'],
            ['', f'{nozzle2[0]}'],
            ['', f'{nozzle2[1]}'],
        ]
        tablestyle_alt = tablestyle + [
            ('BACKGROUND',(1,0),(-1,0),colors.lightgrey),
            ('BACKGROUND',(1,3),(-1,3),colors.lightgrey),
        ]
        list.append(Table(nozzles,style=tablestyle_alt))
        
        t_info = Table([list],hAlign='CENTER',vAlign='CENTER')
        t_info.wrapOn(c, 50, 30)
        f_info = Frame(int(0.05*width), 700, int(0.90*width), 75, leftPadding=0,rightPadding=0, bottomPadding=0, topPadding=0, showBoundary=0)
        f_info.addFromList([t_info],c)

        flyin = [
            [TTR('Fly-In'), i.flyin_name],
            ['', i.flyin_location],
            ['', i.flyin_date],
            ['', f'Analyst: {i.flyin_analyst}']
        ]
        list = []
        list.append(Table(flyin,style=tablestyle))

        #Pass data
        row1 = ['','']
        row2 = [TTR('Observables'),'Airspeed:']
        row3 = ['','Spray Height:']
        row4 = ['', 'Wind Speed:']
        row5 = ['', 'X-Wind Speed:']
        row6 = ['', 'Temperature:']
        row7 = ['', 'Humidity:']
        p: Pass
        for p in s.passes:
            row1.append(p.name)
            row2.append(p.str_airspeed(units='mph'))
            row3.append(p.str_spray_height())
            row4.append(p.str_wind_speed())
            row5.append(p.str_crosswind(units='mph'))
            row6.append('-')
            row7.append('-')
        row1.append('Average')
        row2.append(f'{s.calc_airspeed_mean()} mph')
        row3.append(f'{s.calc_spray_height_mean():.1f} ft')
        row4.append(f'{s.calc_wind_speed_mean():.1f} mph')
        row5.append(f'{s.calc_crosswind_mean():.1f} mph')
        row6.append(f'{s.calc_temperature_mean()} °F')
        row7.append(f'{s.calc_humidity_mean()}%')
        observables = [row1,row2,row3,row4,row5,row6,row7]
        tablestyle_alt = tablestyle + [
            ('BACKGROUND',(2,0),(-1,0),colors.lightgrey),
            ('BACKGROUND',(0,1),(0,-1),colors.lightgrey),
            ('SPAN',(0,1),(0,-1)),
            ('SPAN',(0,0),(1,0)),
            ('LINEBEFORE',(2,0), (2,0), 0.25, colors.black),
            ('LINEBEFORE',(0,1), (0,-1), 0.25, colors.black),
            ('LINEBELOW',(0,-1), (-1,-1), 0.25, colors.black),
            ('LINEAFTER',(-1,0), (-1,-1), 0.25, colors.black),
            ('LINEABOVE',(2,0), (-1,0), 0.25, colors.black),
            ('LINEABOVE',(0,1), (1,1), 0.25, colors.black)
        ]
        tablestyle_alt.remove(('BOX', (0,0), (-1,-1), 0.25, colors.black))
        tablestyle_alt.remove(('SPAN',(0,0),(0,-1)))
        tablestyle_alt.remove(('BACKGROUND',(0,0),(0,-1),colors.lightgrey))
        list.append(Table(observables,style=tablestyle_alt))
        
        notes = [
            [TTR('Setup Notes'), Paragraph(i.notes_setup,style=style)]
        ]
        list.append(Table(notes,style=tablestyle,rowHeights=[75],colWidths=[None,80]))
        
        
        t_observables = Table([list],hAlign='CENTER',vAlign='CENTER')
        t_observables.wrapOn(c, 50, 30)
        f_observables = Frame(int(0.05*width), 610, int(0.90*width), 90, leftPadding=0,rightPadding=0, bottomPadding=0, topPadding=0, showBoundary=0)
        f_observables.addFromList([t_observables],c)
        #t_observables.drawOn(c, 255, 620)

        #Droplet Spectrum
        '''droplet_spectrum = [
            [TTR('USDA Model'), 'Category:', s.calc_dsc()],
            ['', 'VMD:', f'{s.calc_dv05()} μm'],
            ['', 'Dv0.1:', f'{s.calc_dv01()} μm'],
            ['', 'Dv0.9:', f'{s.calc_dv09()} μm'],
            ['', '%v<100 μm:', f'{s.calc_p_lt_100()}%'],
            ['', '%v<200 μm:', f'{s.calc_p_lt_200()}%']
        ]
        t_droplet_spectrum = Table(droplet_spectrum,style=tablestyle)
        t_droplet_spectrum.wrapOn(c, 50, 30)
        t_droplet_spectrum.drawOn(c, 490, 620)'''
        
        #Overlay
        fig = mplCanvasOverlay.fig
        fig.set_size_inches(6, 2)
        fig.set_tight_layout(True)
        imgdata = BytesIO()
        fig.savefig(imgdata, format='svg')
        imgdata.seek(0)  # rewind the data
        drawing=svg2rlg(imgdata)
        renderPDF.draw(drawing,c, 30, 435)

        #Average
        fig = mplCanvasAverage.fig
        fig.set_size_inches(6, 2)
        fig.set_tight_layout(True)
        imgdata = BytesIO()
        fig.savefig(imgdata, format='svg')
        imgdata.seek(0)  # rewind the data
        drawing=svg2rlg(imgdata)
        renderPDF.draw(drawing,c, 30, 270)

        #RT
        fig = mplCanvasRT.fig
        mplCanvasRT.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=6)
        fig.set_size_inches(4.5, 1.5)
        fig.set_tight_layout(True)
        imgdata = BytesIO()
        fig.savefig(imgdata, format='svg')
        imgdata.seek(0)  # rewind the data
        drawing=svg2rlg(imgdata)
        renderPDF.draw(drawing,c, 20, 145)
        mplCanvasRT.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        #BF
        fig = mplCanvasBF.fig
        mplCanvasBF.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=6)
        fig.set_size_inches(4.5, 1.5)
        fig.set_tight_layout(True)
        imgdata = BytesIO()
        fig.savefig(imgdata, format='svg')
        imgdata.seek(0)  # rewind the data
        drawing=svg2rlg(imgdata)
        renderPDF.draw(drawing,c, 20, 15)
        mplCanvasBF.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        #Table
        data = []
        data.append(['Swath','RT','BF'])
        tv = tableView
        for row in range(tv.rowCount()):
            data.append([tv.item(row,0).text(), tv.item(row,1).text(), tv.item(row,2).text()])
        t = Table(data)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
            ('BACKGROUND',(0,6),(-1,6),colors.palegreen),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.lightgrey, None, (2,2,2))]))
        t.wrapOn(c, 100, 250)
        t.drawOn(c, 450, 45)

        c.showPage()
        c.save()

    def strip_num(self, x) -> str:
        if type(x) is str:
            if x == '':
                x = 0
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return f'{round(float(x), 1):.1f}'

class TTR(Flowable):       #TableTextRotate
    '''Rotates a tex in a table cell.'''
    def __init__(self, text ):
        Flowable.__init__(self)
        self.text=text
    def draw(self):
        canvas = self.canv
        canvas.rotate(90)
        canvas.drawString(1, -canvas._leading+2, self.text)
    def wrap(self,aW,aH):
         canv = self.canv
         return canv._leading, canv.stringWidth(self.text)
     
