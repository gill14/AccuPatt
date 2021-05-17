from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Frame, Paragraph
from reportlab.platypus.flowables import Flowable
from svglib.svglib import svg2rlg

class ReportMaker:

    def makeReport(self, seriesData, mplCanvasOverlay, mplCanvasAverage, mplCanvasRT, mplCanvasBF, tableView):
        c = canvas.Canvas('test2.pdf',pagesize=letter)
        width, height = letter
        c.setLineCap(2)
        c.setFont("Helvetica", 8)

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

        #Applicator Info Box
        c.line(20,705,175,705)
        c.line(175,705,175,775)
        c.line(175,775,20,775)
        c.line(20,775,20,705)
        c.drawString(25, 760, seriesData.info.pilot)
        c.drawString(25, 750, seriesData.info.business)
        c.drawString(25, 740, seriesData.info.addressLine1())
        c.drawString(25, 730, seriesData.info.addressLine2())
        c.drawString(25, 720, seriesData.info.phone)
        c.drawString(25, 710, seriesData.info.email)

        #Aircraft Info Box
        aircraft = [
            [TTR('Aircraft'), 'Reg. #:', seriesData.info.regnum],
            ['', 'Make:', seriesData.info.make],
            ['', 'Model:', seriesData.info.model],
            ['', 'Wingspan:', seriesData.info.string_wingspan()],
            ['', 'Winglets?:', seriesData.info.winglets]
        ]
        t = Table(aircraft,style=tablestyle)
        t.wrapOn(c, 50, 30)
        t.drawOn(c, 190, 705)

        #Start list for frame
        list = []

        #Spray System
        spray_system = [
            [TTR('Spray System'), 'Target Swath:', seriesData.info.string_swath()],
            ['', 'Target Rate:', seriesData.info.string_rate()],
            ['', 'Boom Pressure:', seriesData.info.string_pressure()],
            ['', 'Boom Width:', seriesData.info.string_boom_width()],
            ['', 'Boom Drop:', seriesData.info.string_boom_drop()],
            ['', 'Nozzle Spacing:', seriesData.info.string_nozzle_spacing()]
        ]
        t_spray_system = Table(spray_system,style=tablestyle)
        t_spray_system.wrapOn(c, 50, 30)
        t_spray_system.drawOn(c, 20, 620)

        #Nozzles
        nozzles = [
            [TTR('Nozzles'), 'Set #1'],
            ['', f'{seriesData.info.string_nozzle_1().splitlines()[0]}'],
            ['', f'{seriesData.info.string_nozzle_1().splitlines()[1]}'],
            ['', 'Set #2'],
            ['', f'{seriesData.info.string_nozzle_2().splitlines()[0]}'],
            ['', f'{seriesData.info.string_nozzle_2().splitlines()[1]}']
        ]
        tablestyle_alt = tablestyle + [
            ('BACKGROUND',(1,0),(-1,0),colors.navajowhite),
            ('BACKGROUND',(1,3),(-1,3),colors.navajowhite),
        ]

        t_nozzles = Table(nozzles,style=tablestyle_alt)
        t_nozzles.wrapOn(c, 50, 30)
        t_nozzles.drawOn(c, 150, 620)

        #Pass data
        p1,p2,p3 = 'Pass 1','Pass 2','Pass 3'
        observables = [
            ['', '', p1, p2, p3, 'Average'],
            [TTR('Observables'), 'Airspeed',
                seriesData.passes[p1].calc_airspeed(),
                seriesData.passes[p2].calc_airspeed(),
                seriesData.passes[p3].calc_airspeed(),
                f'{self.strip_num(seriesData.calc_airspeed_mean())} mph'],
            ['', 'Spray Height:',
                self.strip_num(seriesData.passes[p1].spray_height),
                self.strip_num(seriesData.passes[p2].spray_height),
                self.strip_num(seriesData.passes[p3].spray_height),
                f'{self.strip_num(seriesData.calc_spray_height_mean())} ft'],
            ['', 'Wind Speed:',
                self.strip_num(seriesData.passes[p1].wind_speed),
                self.strip_num(seriesData.passes[p2].wind_speed),
                self.strip_num(seriesData.passes[p3].wind_speed),
                f'{self.strip_num(seriesData.calc_wind_speed_mean())} mph'],
            ['', 'X-Wind Speed:',
                self.strip_num(seriesData.passes[p1].calc_crosswind()),
                self.strip_num(seriesData.passes[p2].calc_crosswind()),
                self.strip_num(seriesData.passes[p3].calc_crosswind()),
                f'{self.strip_num(seriesData.calc_crosswind_mean())} mph'],
            ['', 'Temperature:', '-', '-','-',
                f'{self.strip_num(seriesData.calc_temperature_mean())} °F'],
            ['', 'Humidity:', '-', '-','-',
                f'{self.strip_num(seriesData.calc_humidity_mean())}%']
        ]
        tablestyle_alt = tablestyle + [
            ('BACKGROUND',(2,0),(-1,0),colors.navajowhite),
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
        t_observables = Table(observables,style=tablestyle_alt)
        t_observables.wrapOn(c, 50, 30)
        t_observables.drawOn(c, 255, 620)

        #Droplet Spectrum
        droplet_spectrum = [
            [TTR('USDA Model'), 'Category:', seriesData.calc_dsc()],
            ['', 'VMD:', f'{seriesData.calc_dv05()} μm'],
            ['', 'Dv0.1:', f'{seriesData.calc_dv01()} μm'],
            ['', 'Dv0.9:', f'{seriesData.calc_dv09()} μm'],
            ['', '%v<100 μm:', f'{seriesData.calc_p_lt_100()}%'],
            ['', '%v<200 μm:', f'{seriesData.calc_p_lt_200()}%']
        ]
        t_droplet_spectrum = Table(droplet_spectrum,style=tablestyle)
        t_droplet_spectrum.wrapOn(c, 50, 30)
        t_droplet_spectrum.drawOn(c, 490, 620)

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
