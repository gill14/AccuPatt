import math
from io import BytesIO
import os

import accupatt.config as cfg
import cv2
from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.models.sprayCard import SprayCard
from accupatt.widgets.mplwidget import MplWidget
from PIL import Image
from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Image as PImage
from reportlab.platypus import Frame, Paragraph, Table, TableStyle
from reportlab.platypus.flowables import Flowable
from svglib.svglib import svg2rlg


class ReportMaker:
    def __init__(self, file: str, seriesData: SeriesData, logo_path: str):
        self.s = seriesData
        self.i = seriesData.info

        self.canvas = canvas.Canvas(file, pagesize=letter)
        self.page_width, self.page_height = letter
        self.bound_x_left = int(0.05 * self.page_width)
        self.bound_x_right = int(0.95 * self.page_width)
        self.bound_y_top = int(0.95 * self.page_height)
        self.bound_y_bottom = int(0.05 * self.page_height)
        self.bound_width = int(0.90 * self.page_width)
        self.bound_height = int(0.90 * self.page_height)
        self.canvas.setLineCap(2)
        self.canvas.setFont("Helvetica", 8)

        self.style = ParagraphStyle(
            name="normal", fontName="Helvetica", fontSize=6, leading=10
        )

        self.style_center = ParagraphStyle(
            name="center",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
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

        self.include_logo = os.path.exists(logo_path)
        self.logo_path = logo_path

    def save(self):
        self.canvas.save()

    def get_logo_image(self, max_width=2 * inch, max_height=inch):
        # Load Image to get dims
        img = Image.open(self.logo_path)
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format=img.format)
        img = ImageReader(img_byte_arr)
        iw, ih = img.getSize()
        aspect = ih / float(iw)
        # Scale to max width
        width = max_width
        height = max_width * aspect
        # Scale (down only) to max height if needed
        if height > max_height:
            height = max_height
            width = height / aspect
        return PImage(self.logo_path, width=width, height=height)

    def report_safe_string(
        self,
        overlayWidget: MplWidget,
        averageWidget: MplWidget,
        racetrackWidget: MplWidget,
        backAndForthWidget: MplWidget,
        tableView,
    ):
        x, y = self._render_headers(string_include=True)
        h_space = 5
        h_large = 145
        h_small = 115
        w_large = self.bound_width
        w_small = 0.725 * self.bound_width
        y = y - (h_large+h_space)
        self._render_from_plot_widget(
            plot_widget = overlayWidget,
            x = x,
            y = y,
            width = w_large,
            height = h_large,
            legend_outside = False
        )
        y = y - (h_large + h_space)
        self._render_from_plot_widget(
            plot_widget = averageWidget,
            x = x,
            y = y,
            width = w_large,
            height = h_large,
            legend_outside = False
        )
        y = y - (h_small + h_space)
        self._render_from_plot_widget(
            plot_widget = racetrackWidget,
            x = x,
            y = y,
            width = w_small,
            height = h_small,
            legend_outside = True
        )
        y = y - (h_small + h_space)
        self._render_from_plot_widget(
            plot_widget = backAndForthWidget,
            x = x,
            y = y,
            width = w_small,
            height = h_small,
            legend_outside = True
        )
        self._render_table_string_cv(tableView, 450, 45, 130, 250)
        # Page Break
        self.canvas.showPage()

    def report_safe_card_summary(
        self,
        spatialCoverageWidget: MplWidget,
        histogramNumberWidget: MplWidget,
        histogramCoverageWidget: MplWidget,
        tableView,
        passData: Pass,
    ):
        # Headers (returns bottom y of headers for plotting start)
        x, y = self._render_headers(cards_include=True)
        # Card Plots
        w_large = self.bound_width
        w_small = 0.65 * self.bound_width
        h_large = 160
        h_small = 140
        h_space = 5
        y = y - (h_large + h_space)
        self._render_from_plot_widget(
            plot_widget = spatialCoverageWidget,
            x = x,
            y = y,
            width = w_large,
            height = h_large,
            legend_outside = True
        )
        y = y - (h_small + h_space)
        y_table = y + 20
        self._render_from_plot_widget(
            plot_widget = histogramNumberWidget,
            x = x,
            y = y,
            width = w_small,
            height = h_small,
            legend_outside = False
        )
        y = y - (h_small + h_space)
        self._render_from_plot_widget(
            plot_widget = histogramCoverageWidget,
            x = x,
            y = y,
            width = w_small,
            height = h_small,
            legend_outside = False
        )
        x_table = x + w_small + (0.025 * self.bound_width)
        h_table = 250
        w_table = 0.3 * self.bound_width
        self._render_table_card_stats(
            tableView,
            passData = passData,
            x = x_table,
            y = y_table,
            width = w_table,
            height = h_table
        )
        h_disclaimer = 125
        frame_disclaimers = Frame(x_table, y_table-h_disclaimer, w_table, h_disclaimer)
        frame_disclaimers.addFromList(self._list_disclaimers(passData), self.canvas)
        # Page Break
        self.canvas.showPage()

    def report_card_individuals_concise(self, passData: Pass):
        self.canvas.setPageSize((self.page_height, self.page_width))
        cards_per_page = cfg.get_report_card_image_per_page()
        image_type = cfg.get_report_card_image_type()
        downsample = cfg.get_report_card_image_downsample()
        h_gap = 10
        card_window_width = round((0.9 * self.page_height) / cards_per_page - h_gap)
        card_window_height = 275
        x_start = round(0.05 * self.page_height)
        x_space = round(card_window_width) + h_gap
        y_start = 270

        cards_paged = 0
        cards_to_page = [
            c
            for c in passData.cards.card_list
            if c.include_in_composite and c.has_image
        ]
        pages_needed = math.ceil(len(cards_to_page) / cards_per_page)

        for i in range(pages_needed):
            for j in range(cards_per_page):
                if cards_paged >= len(cards_to_page):
                    break
                x = x_start + (j * x_space)
                y = y_start
                card: SprayCard = cards_to_page[cards_paged]
                self.canvas.drawImage(
                    self._get_image(card, image_type, downsample),
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
        data.append(["DSC", card.stats.get_dsc()])
        data.append(["Dv0.1", card.stats.get_dv01(text=True)])
        data.append(["VMD", card.stats.get_dv05(text=True)])
        data.append(["Dv0.9", card.stats.get_dv09(text=True)])
        data.append(["RS", card.stats.get_relative_span(text=True)])
        data.append(["Cov.", card.stats.get_percent_coverage(text=True)])
        data.append(["Area", card.stats.get_card_area_in2(text=True)])
        data.append(["St.", card.stats.get_number_of_stains(text=True)])
        data.append(["St./in\u00B2", card.stats.get_stains_per_in2(text=True)])
        return Table(data, style=tablestyle_alt)

    def _get_image(self, card: SprayCard, image_type: str, downsample: bool):
        if image_type == cfg.REPORT_CARD_IMAGE_TYPE_OUTLINE:
            im_cv = card.process_image(overlay=True)
        elif image_type == cfg.REPORT_CARD_IMAGE_TYPE_MASK:
            im_cv = card.process_image(mask=True)
        else:
            im_cv = card.image_original()
        if downsample:
            im_cv = cv2.pyrDown(im_cv)
        # Change Color Space to RGB
        im_cv = cv2.cvtColor(im_cv, cv2.COLOR_BGR2RGB)
        # Convert to PIL image
        im_pil = Image.fromarray(im_cv)
        # Return a reportlab-friendly wrapper
        return ImageReader(im_pil)

    def _render_headers(
        self,
        applicator: bool = True,
        aircraft: bool = True,
        spray_system: bool = True,
        nozzles: bool = True,
        flyin: bool = True,
        observables: bool = True,
        setup_notes: bool = True,
        string_include: bool = False,
        cards_include: bool = False,
    ) -> tuple[int, int]:
        x = self.bound_x_left
        h_flyin_header = 10
        y_flyin_header = self.bound_y_top - h_flyin_header
        w = self.bound_width
        h_space = 5
        
        if flyin:
            Frame(
                x1=x,
                y1=y_flyin_header,
                width=w,
                height=h_flyin_header,
                leftPadding=0,
                rightPadding=0,
                bottomPadding=0,
                topPadding=0,
                showBoundary=1,
            ).add(Paragraph(
                f"{self.i.flyin_name}&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;{self.i.flyin_location}&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;{self.i.flyin_date}&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;Analyst:&nbsp;{self.i.flyin_analyst}",
                style=self.style_center,
            ), self.canvas)  

        # Build first row of tables
        h_row1 = 75
        y_row1 = y_flyin_header - (h_row1 + h_space)
        
        line_1 = []
        col_widths_1 = []
        if applicator:
            col_widths_1.append(150)
            line_1.append(self._header_applicator(box_width=col_widths_1[-1]))
        if aircraft:
            col_widths_1.append(150)
            line_1.append(self._header_aircraft(box_width=col_widths_1[-1]))
        if spray_system:
            col_widths_1.append(125)
            line_1.append(self._header_spray_system(box_width=col_widths_1[-1]))
        if nozzles:
            col_widths_1.append(125)
            line_1.append(self._header_nozzles(box_width=col_widths_1[-1]))
        if len(line_1) > 0:
            # Make table of tables for row 1 and add it to canvas
            t_1 = Table(
                [line_1],
                hAlign="CENTER",
                vAlign="CENTER",
                colWidths=col_widths_1,
            )
            t_1.wrapOn(self.canvas, w, h_row1)
            f_1 = Frame(
                x1=x,
                y1=y_row1,
                width=w,
                height=h_row1,
                leftPadding=0,
                rightPadding=0,
                bottomPadding=0,
                topPadding=0,
                showBoundary=0,
            )
            f_1.addFromList([t_1], self.canvas)
        
        # Build second row of tables
        h_row2 = 90
        y_row2 = y_row1 - (h_row2 + h_space)
        
        line_2 = []
        colWidths = []
        if observables:
            line_2.append(
                self._header_observables(
                    string_included=string_include, cards_included=cards_include
                )
            )
            colWidths.append(None)
        if setup_notes:
            line_2.append(self._header_setup_notes())
            colWidths.append(None)
        if self.include_logo:
            line_2.append(self.get_logo_image(max_width=1.5 * inch, max_height=h_row2))
            colWidths.append(line_2[-1].drawWidth + 10)

        if len(line_2) > 0:
            # Make table of tables for row 2 and add it to canvas
            t_2 = Table([line_2], hAlign="CENTER", vAlign="MIDDLE", colWidths=colWidths)
            t_2.setStyle(TableStyle([("VALIGN", (-1, -1), (-1, -1), "MIDDLE")]))
            t_2.wrapOn(self.canvas, self.bound_width, h_row2)
            f_2 = Frame(
                x1=x,
                y1=y_row2,
                width=w,
                height=h_row2,
                leftPadding=0,
                rightPadding=0,
                bottomPadding=0,
                topPadding=0,
                showBoundary=0,
            )
            f_2.addFromList([t_2], self.canvas)
        return x, y_row2

    def _truncate(
        self, text: str, max_width: float, font_name: str = "Helvetica", font_size: float = 8
    ) -> str:
        """Truncate text with an ellipsis so it fits within max_width."""
        text = str(text) if text is not None else ""
        if not text or self.canvas.stringWidth(text, font_name, font_size) <= max_width:
            return text
        ellipsis = "…"
        while text and self.canvas.stringWidth(text + ellipsis, font_name, font_size) > max_width:
            text = text[:-1]
        return text + ellipsis

    def _header_applicator(self, box_width):
        # colWidths=[14, None] -> single data column, minus its padding (4+4)
        value_width = box_width - 14 - 8
        return Table(
            [
                [TTR("Applicator"), self._truncate(self.i.pilot, value_width)],
                ["", self._truncate(self.i.business, value_width)],
                ["", self._truncate(self.i.addressLine1(), value_width)],
                ["", self._truncate(self.i.addressLine2(), value_width)],
                ["", self._truncate(self.i.string_phone(), value_width)],
                ["", self._truncate(self.i.email, value_width)],
            ],
            colWidths=[14, None],
            style=self.tablestyle,
        )

    def _header_aircraft(self, box_width):
        tablestyle_alt = self.tablestyle + [
            ("BACKGROUND", (1, 0), (-1, 1), colors.palegreen),
        ]
        labels = ["Reg. #:", "Series:", "Make:", "Model:", "Wingspan:", "Winglets?:"]
        # colWidths=[14, None, None] -> label col sized to its widest label,
        # value col gets whatever's left of box_width (each col padded 4+4)
        label_width = max(self.canvas.stringWidth(l, "Helvetica", 8) for l in labels)
        value_width = box_width - 14 - 8 - 8 - label_width
        return Table(
            [
                [TTR("Aircraft"), labels[0], self._truncate(self.i.regnum, value_width)],
                ["", labels[1], self._truncate(self.i.string_series(), value_width)],
                ["", labels[2], self._truncate(self.i.make, value_width)],
                ["", labels[3], self._truncate(self.i.model, value_width)],
                ["", labels[4], self._truncate(self.i.string_wingspan(), value_width)],
                ["", labels[5], self._truncate(self.i.winglets, value_width)],
            ],
            colWidths=[14, None, None],
            style=tablestyle_alt,
        )

    def _header_spray_system(self, box_width):
        labels = [
            "Target Swath:",
            "Target Rate:",
            "Boom Pressure:",
            "Boom Width:",
            "Boom Drop:",
            "Nozzle Spacing:",
        ]
        label_width = max(self.canvas.stringWidth(l, "Helvetica", 8) for l in labels)
        value_width = box_width - 14 - 8 - 8 - label_width
        return Table(
            [
                [TTR("Spray System"), labels[0], self._truncate(self.i.string_swath(), value_width)],
                ["", labels[1], self._truncate(self.i.string_rate(), value_width)],
                ["", labels[2], self._truncate(self.i.string_pressure(), value_width)],
                ["", labels[3], self._truncate(self.i.string_boom_width(), value_width)],
                ["", labels[4], self._truncate(self.i.string_boom_drop(), value_width)],
                ["", labels[5], self._truncate(self.i.string_nozzle_spacing(), value_width)],
            ],
            colWidths=[14, None, None],
            style=self.tablestyle,
        )

    def _header_nozzles(self, box_width):
        tablestyle_alt = self.tablestyle + [
            ("BACKGROUND", (1, 0), (-1, 0), colors.lightgrey),
            ("BACKGROUND", (1, 3), (-1, 3), colors.lightgrey),
        ]
        # colWidths=[14, None] -> single data column, minus its padding (4+4)
        value_width = box_width - 14 - 8
        nozzle1 = (
            self.i.nozzles[0].as_string_tuple() if len(self.i.nozzles) > 0 else ("", "")
        )
        nozzle2 = (
            self.i.nozzles[1].as_string_tuple() if len(self.i.nozzles) > 1 else ("", "")
        )
        nozzle1 = tuple(self._truncate(v, value_width) for v in nozzle1)
        nozzle2 = tuple(self._truncate(v, value_width) for v in nozzle2)
        return Table(
            [
                [TTR("Nozzles"), "Set #1"],
                ["", f"{nozzle1[0]}"],
                ["", f"{nozzle1[1]}"],
                ["", "Set #2"],
                ["", f"{nozzle2[0]}"],
                ["", f"{nozzle2[1]}"],
            ],
            colWidths=[14, None],
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
            colWidths=[14, None],
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
            v = p.airspeed_in(airspeed_units)
            row2.append(f"{v}" if v is not None else "-")
            v = p.spray_height_in(spray_height_units)
            row3.append(f"{v:.1f}" if v is not None else "-")
            v = p.wind_speed_in(wind_speed_units)
            row4.append(f"{v:g}" if v is not None else "-")
            v = p.crosswind_in(crosswind_speed_units)
            row5.append(f"{round(v, 1) + 0.:.1f}" if v is not None else "-")
            v = p.temperature_in(temperature_units)
            row6.append(f"{v:g}" if v is not None else "-")
            v = p.humidity_in()
            row7.append(f"{v:g}" if v is not None else "-")
        row1.append("Average")
        row2.append(airspeed_string)
        row3.append(spray_height_string)
        row4.append(wind_speed_string)
        row5.append(crosswind_speed_string)
        row6.append(temperature_string)
        row7.append(humidity_string)
        return Table(
            [row1, row2, row3, row4, row5, row6, row7],
            colWidths=[14] + [None] * (len(row1) - 1),
            style=self.tablestyle_with_headers,
        )

    def _header_setup_notes(self):
        notes = [[TTR("Setup Notes"), Paragraph(self.i.notes_setup, style=self.style)]]
        return Table(
            notes, style=self.tablestyle, rowHeights=[80], colWidths=[14, None]
        )

    def _render_from_plot_widget(
        self, plot_widget: MplWidget, x, y, width, height, legend_outside: bool = False
    ):
        # Resize the plot widget to the desired size in inches
        mplCanvas = plot_widget.canvas
        fig = mplCanvas.fig
        plot_widget.legend_outside = legend_outside
        plot_widget.resize_inches(width / inch, height / inch)
        mplCanvas.draw()
        # Save the plot to a BytesIO object in SVG format
        imgdata = BytesIO()
        fig.savefig(imgdata, format="svg")
        imgdata.seek(0)  # rewind the data
        # Reset the plot widget size to avoid affecting the UI
        plot_widget.resize_inches_reset()
        # Convert the SVG data to a ReportLab drawing and render it on the canvas
        renderPDF.draw(
            drawing=svg2rlg(imgdata),
            canvas=self.canvas,
            x=x,
            y=y,
        )
        
    def _render_table_string_cv(self, tableView, x, y, width, height):
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
        table = Table(data, style=tablestyle_alt)
        table.wrapOn(self.canvas, width, height)
        table.drawOn(self.canvas, x, y)

    def _render_table_card_stats(self, tableWidget, passData: Pass, x, y, width, height):
        tablestyle_alt = self.tablestyle_with_headers + [
            ("BACKGROUND", (3, 6), (3, -1), colors.lightgrey)
        ]
        dv01, dv05, dv09, dsc, rs = self.s.calc_droplet_stats(cards_included=True)
        model_values = {0: dsc, 1: dv01, 2: dv05, 3: dv09, 4: rs}
        data = [
            ["", "", "Measured \u00B9 \u00B2", "USDA Model \u00B3"],
            *[
                [
                    "",
                    tableWidget.item(row, 0).text(),
                    tableWidget.item(row, 1).text(),
                    model_values.get(row, ""),
                ]
                for row in range(tableWidget.rowCount())
            ],
        ]
        data[1][0] = TTR(f"Composite - {passData.name}")
        table = Table(data, colWidths=[14, None, None, None], style=tablestyle_alt)
        table.wrapOn(self.canvas, width, height)
        table.drawOn(self.canvas, x, y)

    def _list_disclaimers(self, passData: Pass):
        disclaimers = []
        sc: SprayCard
        sc = [card for card in passData.cards.card_list if card.include_in_composite][0]
        disclaimers.append(
            Paragraph(
                f"Based on inputs, minimum detectable droplet diameter is {sc.stats.get_minimum_detectable_droplet_diameter()} μm.",
                style=self.style,
                bulletText="\u00B9",
            )
        )
        disclaimers.append(
            Paragraph(
                "Measured Droplet Spectrum Category is calculated with reference nozzle data, and should not be considered absolute.",
                style=self.style,
                bulletText="\u00B2",
            )
        )
        disclaimers.append(
            Paragraph(
                "USDA Model flow-weighted and interpolated composite calculation based on stated nozzle configuration and quantities.",
                style=self.style,
                bulletText="\u00B3",
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
