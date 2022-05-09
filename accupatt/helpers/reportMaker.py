import math
from io import BytesIO

import accupatt.config as cfg
import cv2
from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.models.sprayCard import SprayCard
from accupatt.widgets.mplwidget import MplWidget
from PIL import Image
from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph, Table, TableStyle
from reportlab.platypus.flowables import Flowable
from svglib.svglib import svg2rlg


class ReportMaker:
    def __init__(self, file: str, seriesData: SeriesData):
        self.s = seriesData
        self.i = seriesData.info

        self.canvas = canvas.Canvas(file, pagesize=letter)
        self.page_width, self.page_height = letter
        self.bound_x_left = int(0.05 * self.page_width)
        self.bound_x_right = int(0.95 * self.page_width)
        self.bound_width = round(0.90 * self.page_width)
        self.canvas.setLineCap(2)
        self.canvas.setFont("Helvetica", 8)

        self.style = ParagraphStyle(
            name="normal", fontName="Helvetica", fontSize=6, leading=10
        )

        self.tablestyle = [
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey, None, (2, 2, 2)),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LEADING", (0, 0), (-1, -1), 9.5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING", (1, 0), (-1, -1), 4),
            ("RIGHTPADDING", (1, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ("SPAN", (0, 0), (0, -1)),
        ]

        self.tablestyle_with_headers = self.tablestyle + [
            ("BACKGROUND", (2, 0), (-1, 0), colors.lightgrey),
            ("BACKGROUND", (0, 1), (0, -1), colors.lightgrey),
            ("SPAN", (0, 1), (0, -1)),
            ("SPAN", (0, 0), (1, 0)),
            ("LINEBEFORE", (2, 0), (2, 0), 0.25, colors.black),
            ("LINEBEFORE", (0, 1), (0, -1), 0.25, colors.black),
            ("LINEBELOW", (0, -1), (-1, -1), 0.25, colors.black),
            ("LINEAFTER", (-1, 0), (-1, -1), 0.25, colors.black),
            ("LINEABOVE", (2, 0), (-1, 0), 0.25, colors.black),
            ("LINEABOVE", (0, 1), (1, 1), 0.25, colors.black),
        ]
        self.tablestyle_with_headers.remove(
            ("BOX", (0, 0), (-1, -1), 0.25, colors.black)
        )
        self.tablestyle_with_headers.remove(("SPAN", (0, 0), (0, -1)))
        self.tablestyle_with_headers.remove(
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey)
        )

    def save(self):
        self.canvas.save()

    def printHeaders(
        self,
        applicator: bool = True,
        aircraft: bool = True,
        spray_system: bool = True,
        nozzles: bool = True,
        flyin: bool = True,
        observables: bool = True,
        setup_notes: bool = True,
        string_include=False,
        cards_include=False,
    ):
        # Build first row of tables
        line_1 = []
        if applicator:
            line_1.append(self._header_applicator())
        if aircraft:
            line_1.append(self._header_aircraft())
        if spray_system:
            line_1.append(self._header_spray_system())
        if nozzles:
            line_1.append(self._header_nozzles())
        if len(line_1) > 0:
            # Make table of tables for row 1 and add it to canvas
            t_1 = Table([line_1], hAlign="CENTER", vAlign="CENTER")
            t_1.wrapOn(self.canvas, 50, 30)
            f_1 = Frame(
                self.bound_x_left,
                700,
                self.bound_width,
                75,
                leftPadding=0,
                rightPadding=0,
                bottomPadding=0,
                topPadding=0,
                showBoundary=0,
            )
            f_1.addFromList([t_1], self.canvas)
        # Build second row of tables
        line_2 = []
        if flyin:
            line_2.append(self._header_flyin())
        if observables:
            line_2.append(
                self._header_observables(
                    string_included=string_include, cards_included=cards_include
                )
            )
        if setup_notes:
            line_2.append(self._header_setup_notes())
        if len(line_2) > 0:
            # Make table of tables for row 2 and add it to canvas
            t_2 = Table([line_2], hAlign="CENTER", vAlign="CENTER")
            t_2.wrapOn(self.canvas, 50, 30)
            f_2 = Frame(
                self.bound_x_left,
                610,
                self.bound_width,
                90,
                leftPadding=0,
                rightPadding=0,
                bottomPadding=0,
                topPadding=0,
                showBoundary=0,
            )
            f_2.addFromList([t_2], self.canvas)

    def report_safe_string(
        self,
        overlayWidget: MplWidget,
        averageWidget: MplWidget,
        racetrackWidget: MplWidget,
        backAndForthWidget: MplWidget,
        tableView,
    ):
        # Headers
        self.printHeaders(string_include=True)
        # String Plots
        y_space = 25
        y_tall = 140
        y_short = 110
        y = 435
        renderPDF.draw(
            self._drawing_from_plot_widget(
                overlayWidget, 0.8 * self.bound_width / inch, y_tall / inch
            ),
            self.canvas,
            self.bound_x_left,
            y,
        )
        y = y - y_space - y_tall
        renderPDF.draw(
            self._drawing_from_plot_widget(
                averageWidget, 0.8 * self.bound_width / inch, y_tall / inch
            ),
            self.canvas,
            self.bound_x_left,
            y,
        )
        y = y - y_space - y_short
        renderPDF.draw(
            self._drawing_from_plot_widget(
                racetrackWidget,
                0.6 * self.bound_width / inch,
                y_short / inch,
                legend_outside=True,
            ),
            self.canvas,
            self.bound_x_left,
            y,
        )
        y = y - y_space - y_short + 5
        renderPDF.draw(
            self._drawing_from_plot_widget(
                backAndForthWidget,
                0.6 * self.bound_width / inch,
                y_short / inch,
                legend_outside=True,
            ),
            self.canvas,
            self.bound_x_left,
            y,
        )
        # String CV Table
        table_cv = self._table_string_cv(tableView)
        table_cv.wrapOn(self.canvas, 100, 250)
        table_cv.drawOn(self.canvas, 450, 45)
        # Page Break
        self.canvas.showPage()

    def report_safe_card_summary(
        self,
        spatialDVWidget: MplWidget,
        spatialCoverageWidget: MplWidget,
        histogramNumberWidget: MplWidget,
        histogramCoverageWidget: MplWidget,
        tableView,
        passData: Pass,
    ):
        # Headers
        self.printHeaders(cards_include=True)
        # Card Plots
        y_space = 25
        y_tall = 140
        y_short = 110
        y = 435
        renderPDF.draw(
            self._drawing_from_plot_widget(
                spatialDVWidget,
                0.8 * self.bound_width / inch,
                y_tall / inch,
                legend_outside=True,
            ),
            self.canvas,
            self.bound_x_left,
            y,
        )
        y = y - y_space - y_tall
        renderPDF.draw(
            self._drawing_from_plot_widget(
                spatialCoverageWidget,
                0.8 * self.bound_width / inch,
                y_tall / inch,
                legend_outside=True,
            ),
            self.canvas,
            self.bound_x_left,
            y,
        )
        y = y - y_space - y_short
        renderPDF.draw(
            self._drawing_from_plot_widget(
                histogramNumberWidget, 0.5 * self.bound_width / inch, y_short / inch
            ),
            self.canvas,
            self.bound_x_left,
            y,
        )
        y = y - y_space - y_short + 5
        renderPDF.draw(
            self._drawing_from_plot_widget(
                histogramCoverageWidget, 0.5 * self.bound_width / inch, y_short / inch
            ),
            self.canvas,
            self.bound_x_left,
            y,
        )
        # Droplet Dist Table
        table_cv = self._table_card_stats(tableView, passData.name)
        table_cv.wrapOn(self.canvas, 100, 250)
        table_cv.drawOn(self.canvas, 400, 150)
        # Disclaimers
        size = 6
        y = 80
        x = 405
        frame_disclaimers = Frame(400, 20, 160, 120)
        frame_disclaimers.addFromList(self._list_disclaimers(passData), self.canvas)
        # Page Break
        self.canvas.showPage()

    def report_card_individuals_concise(self, passData: Pass):
        self.canvas.setPageSize((self.page_height, self.page_width))
        cards_per_page = cfg.get_report_card_image_per_page()
        image_type = cfg.get_report_card_image_type()
        use_compression = False
        h_gap = 10
        card_window_width = round((0.9 * self.page_height) / cards_per_page - h_gap)
        card_window_height = 275
        x_start = round(0.05 * self.page_height)
        x_space = round(card_window_width) + h_gap
        y_start = 270

        cards_paged = 0
        cards_to_page = [
            c for c in passData.cards.card_list if c.include_in_composite and c.has_image
        ]
        pages_needed = math.ceil(len(cards_to_page) / cards_per_page)

        for i in range(pages_needed):
            for j in range(cards_per_page):
                if cards_paged >= len(cards_to_page):
                    break
                x = x_start + (j * x_space)
                y = y_start
                card: SprayCard = cards_to_page[cards_paged]
                print(
                    f"card name = {card.name}, x={x}, y={y}, window_width={card_window_width}"
                )
                self.canvas.drawImage(
                    self._get_image(card, image_type),
                    x,
                    y,
                    card_window_width,
                    card_window_height,
                    preserveAspectRatio=True,
                    showBoundary=True,
                    anchor="s",
                )
                # More Stuff
                table = self._detail_card(card)
                table.wrapOn(self.canvas, card_window_width, 200)
                frame = Frame(
                    x,
                    y - 200,
                    card_window_width,
                    180,
                    leftPadding=0,
                    rightPadding=0,
                    bottomPadding=0,
                    topPadding=0,
                    showBoundary=0,
                )
                frame.addFromList([table], self.canvas)

                # table.drawOn(self.canvas, x, y-200)
                cards_paged += 1
            self.canvas.drawCentredString(
                round(self.page_height / 2),
                30,
                f"{self.s.info.string_reg_series()} - Individual Card Data for {passData.name} - Page {i+1}/{pages_needed}",
            )
            self.canvas.showPage()

        self.canvas.setPageSize((self.page_width, self.page_height))

    def _detail_card(self, card: SprayCard):
        tablestyle_alt = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 6), (-1, 6), colors.palegreen),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.lightgrey,
                    None,
                    (2, 2, 2),
                ),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("SPAN", (0, 0), (1, 0)),
            ]
        )
        data = []
        data.append([card.name, ""])
        stains = len(card.stain_areas_valid_px2)
        area = card._px2_to_in2(card.area_px2)
        if stains > 0:
            dv01, dv05, dv09, rs, dsc = card.volumetric_stats()
            rs = f"{rs:.2f}"
            cov = f"{card.percent_coverage():.2f}"
            spsi = round(stains / area)
        else:
            dv01 = "-"
            dv05 = "-"
            dv09 = "-"
            rs = "-"
            dsc = "-"
            cov = "-"
            spsi = "-"
        area = f"{area:.2f}"
        data.append(["DSC", dsc])
        data.append(["Dv0.1", f"{dv01} \u03BCm"])
        data.append(["VMD", f"{dv05} \u03BCm"])
        data.append(["Dv0.9", f"{dv09} \u03BCm"])
        data.append(["RS", rs])
        data.append(["Cov.", f"{cov}%"])
        data.append(["Area", f"{area} in\u00B2"])
        data.append(["St.", stains])
        data.append(["St./in\u00B2", spsi])
        return Table(data, style=tablestyle_alt)

    def _get_image(self, card: SprayCard, image_type: str):
        if image_type == cfg.REPORT_CARD_IMAGE_TYPE_OUTLINE:
            im_cv = card.images_processed()[0]
        elif image_type == cfg.REPORT_CARD_IMAGE_TYPE_MASK:
            im_cv = card.images_processed()[1]
        else:
            im_cv = card.image_original()
        # Change Color Space to RGB
        im_cv = cv2.cvtColor(im_cv, cv2.COLOR_BGR2RGB)
        # Convert to PIL image
        im_pil = Image.fromarray(im_cv)
        # Return a reportlab-friendly wrapper
        return ImageReader(im_pil)

    def _header_applicator(self):
        return Table(
            [
                [TTR("Applicator"), self.i.pilot],
                ["", self.i.business],
                ["", self.i.addressLine1()],
                ["", self.i.addressLine2()],
                ["", self.i.string_phone()],
                ["", self.i.email],
            ],
            style=self.tablestyle,
        )

    def _header_aircraft(self):
        tablestyle_alt = self.tablestyle + [
            ("BACKGROUND", (1, 0), (-1, 1), colors.palegreen),
        ]
        return Table(
            [
                [TTR("Aircraft"), "Reg. #:", self.i.regnum],
                ["", "Series:", self.i.series],
                ["", "Make:", self.i.make],
                ["", "Model:", self.i.model],
                ["", "Wingspan:", self.i.string_wingspan()],
                ["", "Winglets?:", self.i.winglets],
            ],
            style=tablestyle_alt,
        )

    def _header_spray_system(self):
        return Table(
            [
                [TTR("Spray System"), "Target Swath:", self.i.string_swath()],
                ["", "Target Rate:", self.i.string_rate()],
                ["", "Boom Pressure:", self.i.string_pressure()],
                ["", "Boom Width:", self.i.string_boom_width()],
                ["", "Boom Drop:", self.i.string_boom_drop()],
                ["", "Nozzle Spacing:", self.i.string_nozzle_spacing()],
            ],
            style=self.tablestyle,
        )

    def _header_nozzles(self):
        tablestyle_alt = self.tablestyle + [
            ("BACKGROUND", (1, 0), (-1, 0), colors.lightgrey),
            ("BACKGROUND", (1, 3), (-1, 3), colors.lightgrey),
        ]
        nozzle1 = (
            self.i.nozzles[0].as_string_tuple() if len(self.i.nozzles) > 0 else ("", "")
        )
        nozzle2 = (
            self.i.nozzles[1].as_string_tuple() if len(self.i.nozzles) > 1 else ("", "")
        )
        return Table(
            [
                [TTR("Nozzles"), "Set #1"],
                ["", f"{nozzle1[0]}"],
                ["", f"{nozzle1[1]}"],
                ["", "Set #2"],
                ["", f"{nozzle2[0]}"],
                ["", f"{nozzle2[1]}"],
            ],
            style=tablestyle_alt,
        )

    def _header_flyin(self):
        return Table(
            [
                [TTR("Fly-In"), self.i.flyin_name],
                ["", self.i.flyin_location],
                ["", self.i.flyin_date],
                ["", f"Analyst: {self.i.flyin_analyst}"],
            ],
            style=self.tablestyle,
        )

    def _header_observables(self, string_included=False, cards_included=False):
        # Pass data
        row1 = ["", ""]
        row2 = [TTR("Observables"), "Airspeed:"]
        row3 = ["", "Spray Height:"]
        row4 = ["", "Wind Speed:"]
        row5 = ["", "X-Wind Speed:"]
        row6 = ["", "Temperature:"]
        row7 = ["", "Humidity:"]
        # Run series calcs first to obtain common units
        _, airspeed_units, airspeed_string = self.s.get_airspeed_mean(
            string_included=string_included, cards_included=cards_included
        )
        _, spray_height_units, spray_height_string = self.s.get_spray_height_mean(
            string_included=string_included, cards_included=cards_included
        )
        _, wind_speed_units, wind_speed_string = self.s.get_wind_speed_mean(
            string_included=string_included, cards_included=cards_included
        )
        _, crosswind_speed_units, crosswind_speed_string = self.s.get_crosswind_mean(
            string_included=string_included, cards_included=cards_included
        )
        _, temperature_units, temperature_string = self.s.get_temperature_mean(
            string_included=string_included, cards_included=cards_included
        )
        _, humidity_units, humidity_string = self.s.get_humidity_mean(
            string_included=string_included, cards_included=cards_included
        )
        p: Pass
        for p in self.s.get_includable_passes(
            string_included=string_included, cards_included=cards_included
        ):
            row1.append(p.name)
            row2.append(p.get_airspeed(airspeed_units)[2])
            row3.append(p.get_spray_height(spray_height_units)[2])
            row4.append(p.get_wind_speed(wind_speed_units)[2])
            row5.append(p.get_crosswind(crosswind_speed_units)[2])
            row6.append("-")
            row7.append("-")
        row1.append("Average")
        row2.append(airspeed_string)
        row3.append(spray_height_string)
        row4.append(wind_speed_string)
        row5.append(crosswind_speed_string)
        row6.append(temperature_string)
        row7.append(humidity_string)
        return Table(
            [row1, row2, row3, row4, row5, row6, row7],
            style=self.tablestyle_with_headers,
        )

    def _header_setup_notes(self):
        notes = [[TTR("Setup Notes"), Paragraph(self.i.notes_setup, style=self.style)]]
        return Table(
            notes, style=self.tablestyle, rowHeights=[75], colWidths=[None, 80]
        )

    def _drawing_from_plot_widget(
        self, plot_widget: MplWidget, width_in, height_in, legend_outside: bool = False
    ):
        if legend_outside:
            plot_widget.canvas.ax.legend(
                loc="center left", bbox_to_anchor=(1, 0.5), fontsize=6
            )
        else:
            plot_widget.canvas.ax.legend(fontsize=6)
        plot_widget.canvas.ax.xaxis.label.set_size(6)
        plot_widget.canvas.ax.yaxis.label.set_size(6)
        plot_widget.canvas.ax.tick_params(axis="both", which="major", labelsize=6)
        fig = plot_widget.canvas.fig
        fig.set_size_inches(width_in, height_in)
        fig.set_tight_layout(True)

        imgdata = BytesIO()
        fig.savefig(imgdata, format="svg")
        imgdata.seek(0)  # rewind the data
        return svg2rlg(imgdata)

    def _table_string_cv(self, tableView):
        tablestyle_alt = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("BACKGROUND", (0, 6), (-1, 6), colors.palegreen),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.lightgrey,
                    None,
                    (2, 2, 2),
                ),
            ]
        )
        data = []
        data.append(["Swath", "RT", "BF"])
        for row in range(tableView.rowCount()):
            data.append(
                [
                    tableView.item(row, 0).text(),
                    tableView.item(row, 1).text(),
                    tableView.item(row, 2).text(),
                ]
            )
        return Table(data, style=tablestyle_alt)

    def _table_card_stats(self, tableWidget, passName: str):
        tablestyle_alt = self.tablestyle_with_headers + [
            ("BACKGROUND", (3, 6), (3, -1), colors.lightgrey)
        ]
        dv01, dv05, dv09, plt100, plt200, dsc, rs = self.s.calc_droplet_stats(
            cards_included=True
        )
        data = []
        data.append(["", "", "Measured \u00B9\u22C5\u00B2", "USDA Model \u00B3"])
        for row in range(tableWidget.rowCount()):
            data.append(
                [
                    "",
                    tableWidget.item(row, 0).text(),
                    tableWidget.item(row, 1).text(),
                    "",
                ]
            )
        data[1][0] = TTR(f"Composite - {passName}")
        data[1][3] = dsc
        data[2][3] = f"{dv01} μm"
        data[3][3] = f"{dv05} μm"
        data[4][3] = f"{dv09} μm"
        data[5][3] = f"{rs:.2f}"
        return Table(data, style=tablestyle_alt)

    def _list_disclaimers(self, passData: Pass):
        disclaimers = []
        sc: SprayCard
        sc = [card for card in passData.cards.card_list if card.include_in_composite][0]
        disclaimers.append(
            Paragraph(
                f"\u00B9  Based on inputs, minimum detectable droplet diameter is {sc.minimum_detectable_droplet_diameter()} μm.",
                style=self.style,
            )
        )
        disclaimers.append(
            Paragraph(
                f"\u00B2  Measured Droplet Spectrum Category is calculated with reference nozzle data, and should not be considered absolute.",
                style=self.style,
            )
        )
        disclaimers.append(
            Paragraph(
                f"\u00B3  USDA Model flow-weighted and interpolated composite calculation based on stated nozzle configuration and quantities.",
                style=self.style,
            )
        )
        return disclaimers


class TTR(Flowable):  # TableTextRotate
    """Rotates a tex in a table cell."""

    def __init__(self, text):
        Flowable.__init__(self)
        self.text = text

    def draw(self):
        canvas = self.canv
        canvas.rotate(90)
        canvas.drawString(1, -canvas._leading + 2, self.text)

    def wrap(self, aW, aH):
        canv = self.canv
        return canv._leading, canv.stringWidth(self.text)
