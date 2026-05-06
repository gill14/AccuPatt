import os

import accupatt.config as cfg
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from serial.tools import list_ports

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "settings.ui")
)


class Settings(baseclass):
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._populate()
        self.ui.buttonBox.accepted.connect(self._apply)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.btn_datafile_dir.clicked.connect(self._browse_datafile_dir)
        self.ui.btn_logo_path.clicked.connect(self._browse_logo_path)
        self.ui.btn_reset_defaults.clicked.connect(self._reset_defaults)

    def _populate(self):
        # --- General ---
        self.ui.le_datafile_dir.setText(cfg.get_datafile_dir())
        self.ui.le_flyin_name.setText(cfg.get_flyin_name())
        self.ui.le_flyin_location.setText(cfg.get_flyin_location())
        self.ui.le_flyin_date.setText(cfg.get_flyin_date())
        self.ui.le_flyin_analyst.setText(cfg.get_flyin_analyst())
        self.ui.sb_number_passes.setValue(cfg.get_number_of_passes())
        self.ui.sb_simulated_adjacent_passes.setValue(
            cfg.get_simulated_adjacent_passes()
        )
        self.ui.cbb_center_method.addItems(
            [cfg.CENTER_METHOD_CENTROID, cfg.CENTER_METHOD_COD]
        )
        self.ui.cbb_center_method.setCurrentText(cfg.get_center_method())

        # --- Observables ---
        self.ui.cbb_wingspan_units.addItems(cfg.UNITS_LENGTH_LARGE)
        self.ui.cbb_wingspan_units.setCurrentText(cfg.get_unit_wingspan())

        self.ui.cbb_swath_units.addItems(cfg.UNITS_LENGTH_LARGE)
        self.ui.cbb_swath_units.setCurrentText(cfg.get_unit_swath())

        self.ui.cbb_rate_units.addItems(cfg.UNITS_RATE)
        self.ui.cbb_rate_units.setCurrentText(cfg.get_unit_rate())

        self.ui.cbb_pressure_units.addItems(cfg.UNITS_PRESSURE)
        self.ui.cbb_pressure_units.setCurrentText(cfg.get_unit_pressure())

        self.ui.cbb_boom_width_units.addItems(cfg.UNITS_BOOM_WIDTH)
        self.ui.cbb_boom_width_units.setCurrentText(cfg.get_unit_boom_width())

        self.ui.cbb_boom_drop_units.addItems(cfg.UNITS_LENGTH_SMALL)
        self.ui.cbb_boom_drop_units.setCurrentText(cfg.get_unit_boom_drop())

        self.ui.cbb_nozzle_spacing_units.addItems(cfg.UNITS_LENGTH_SMALL)
        self.ui.cbb_nozzle_spacing_units.setCurrentText(cfg.get_unit_nozzle_spacing())

        self.ui.cbb_ground_speed_units.addItems(cfg.UNITS_GROUND_SPEED)
        self.ui.cbb_ground_speed_units.setCurrentText(cfg.get_unit_ground_speed())

        self.ui.cbb_spray_height_units.addItems(cfg.UNITS_SPRAY_HEIGHT)
        self.ui.cbb_spray_height_units.setCurrentText(cfg.get_unit_spray_height())

        self.ui.cbb_wind_speed_units.addItems(cfg.UNITS_WIND_SPEED)
        self.ui.cbb_wind_speed_units.setCurrentText(cfg.get_unit_wind_speed())

        self.ui.cbb_temperature_units.addItems(cfg.UNITS_TEMPERATURE)
        self.ui.cbb_temperature_units.setCurrentText(cfg.get_unit_temperature())

        # --- String ---
        self.ui.dsb_smooth_window.setValue(cfg.get_smooth_window())
        self.ui.sb_smooth_order.setValue(cfg.get_smooth_order())

        self.ui.cb_string_dash_overlay.setChecked(
            cfg.get_string_plot_average_dash_overlay()
        )
        self.ui.cbb_string_dash_method.addItems(
            [cfg.DASH_OVERLAY_METHOD_ISHA, cfg.DASH_OVERLAY_METHOD_AVERAGE]
        )
        self.ui.cbb_string_dash_method.setCurrentText(
            cfg.get_string_plot_average_dash_overlay_method()
        )
        self.ui.cbb_string_simulation_view.addItems(
            [cfg.STRING_SIMULATION_VIEW_WINDOW_ONE, cfg.STRING_SIMULATION_VIEW_WINDOW_ALL]
        )
        self.ui.cbb_string_simulation_view.setCurrentText(
            cfg.get_string_simulation_view_window()
        )

        # String Drive
        for port in list_ports.comports():
            self.ui.cbb_string_drive_port.addItem(port.device)
        saved_port = cfg.get_string_drive_port()
        idx = self.ui.cbb_string_drive_port.findText(saved_port)
        if idx >= 0:
            self.ui.cbb_string_drive_port.setCurrentIndex(idx)
        elif saved_port:
            self.ui.cbb_string_drive_port.addItem(saved_port)
            self.ui.cbb_string_drive_port.setCurrentText(saved_port)

        self.ui.dsb_string_length.setValue(cfg.get_string_length())
        self.ui.cbb_string_length_units.addItems(cfg.UNITS_STRING_DATA_LOCATION)
        self.ui.cbb_string_length_units.setCurrentText(cfg.get_unit_string_data_location())
        self.ui.cbb_string_length_units.currentTextChanged.connect(self._update_string_length_unit_labels)
        self.ui.dsb_string_speed.setValue(cfg.get_string_speed())
        self._update_string_length_unit_labels(cfg.get_unit_string_data_location())

        # --- Spray Cards ---
        self.ui.cbb_image_load_method.addItems(cfg.IMAGE_LOAD_METHODS)
        self.ui.cbb_image_load_method.setCurrentText(cfg.get_image_load_method())

        self.ui.cb_flip_x.setChecked(cfg.get_image_flip_x())
        self.ui.cb_flip_y.setChecked(cfg.get_image_flip_y())

        self.ui.cbb_image_dpi.addItems([str(d) for d in cfg.IMAGE_DPI_OPTIONS])
        self.ui.cbb_image_dpi.setCurrentText(str(cfg.get_image_dpi()))

        self.ui.cbb_roi_orientation.addItems(cfg.ROI_ACQUISITION_ORIENTATIONS)
        self.ui.cbb_roi_orientation.setCurrentText(
            cfg.get_image_roi_acquisition_orientation()
        )
        self.ui.cbb_roi_order.addItems(cfg.ROI_ACQUISITION_ORDERS)
        self.ui.cbb_roi_order.setCurrentText(cfg.get_image_roi_acquisition_order())

        self.ui.cbb_roi_scale.addItems([str(s) for s in cfg.ROI_SCALES])
        self.ui.cbb_roi_scale.setCurrentText(str(cfg.get_image_roi_scale()))

        self.ui.cbb_threshold_type.addItems(cfg.THRESHOLD_TYPES)
        self.ui.cbb_threshold_type.setCurrentText(cfg.get_threshold_type())

        self.ui.sb_threshold_grayscale.setValue(cfg.get_threshold_grayscale())
        self.ui.cbb_threshold_grayscale_method.addItems(cfg.THRESHOLD_GRAYSCALE_METHODS)
        self.ui.cbb_threshold_grayscale_method.setCurrentText(
            cfg.get_threshold_grayscale_method()
        )

        self.ui.sb_hsb_hue_min.setValue(cfg.get_threshold_hsb_hue_min())
        self.ui.sb_hsb_hue_max.setValue(cfg.get_threshold_hsb_hue_max())
        self.ui.cb_hsb_hue_pass.setChecked(cfg.get_threshold_hsb_hue_pass())
        self.ui.sb_hsb_sat_min.setValue(cfg.get_threshold_hsb_saturation_min())
        self.ui.sb_hsb_sat_max.setValue(cfg.get_threshold_hsb_saturation_max())
        self.ui.cb_hsb_sat_pass.setChecked(cfg.get_threshold_hsb_saturation_pass())
        self.ui.sb_hsb_brightness_min.setValue(cfg.get_threshold_hsb_brightness_min())
        self.ui.sb_hsb_brightness_max.setValue(cfg.get_threshold_hsb_brightness_max())
        self.ui.cb_hsb_brightness_pass.setChecked(
            cfg.get_threshold_hsb_brightness_pass()
        )

        self.ui.cb_watershed.setChecked(cfg.get_watershed())
        self.ui.sb_min_stain_area.setValue(cfg.get_min_stain_area_px())
        self.ui.cbb_stain_approximation.addItems(cfg.STAIN_APPROXIMATION_METHODS)
        self.ui.cbb_stain_approximation.setCurrentText(
            cfg.get_stain_approximation_method()
        )
        self.ui.sb_max_stain_count.setValue(cfg.get_max_stain_count())

        self.ui.cbb_spread_equation.addItems(cfg.SPREAD_METHODS)
        self.ui.cbb_spread_equation.setCurrentText(cfg.get_spread_factor_equation())
        self.ui.dsb_spread_a.setValue(cfg.get_spread_factor_a())
        self.ui.dsb_spread_b.setValue(cfg.get_spread_factor_b())
        self.ui.dsb_spread_c.setValue(cfg.get_spread_factor_c())

        self.ui.cbb_card_plot_y_axis.addItems(
            [cfg.CARD_PLOT_Y_AXIS_COVERAGE, cfg.CARD_PLOT_Y_AXIS_DEPOSITION]
        )
        self.ui.cbb_card_plot_y_axis.setCurrentText(cfg.get_card_plot_y_axis())

        self.ui.cb_card_shading.setChecked(cfg.get_card_plot_shading())
        self.ui.cbb_card_shading_method.addItems(
            [
                cfg.CARD_PLOT_SHADING_METHOD_DSC,
                cfg.CARD_PLOT_SHADING_METHOD_DEPOSITION_AVERAGE,
                cfg.CARD_PLOT_SHADING_METHOD_DEPOSITION_TARGET,
            ]
        )
        self.ui.cbb_card_shading_method.setCurrentText(
            cfg.get_card_plot_shading_method()
        )
        self.ui.cb_card_shading_interpolate.setChecked(
            cfg.get_card_plot_shading_interpolate()
        )
        self.ui.cb_card_dash_overlay.setChecked(cfg.get_card_plot_average_dash_overlay())
        self.ui.cbb_card_dash_method.addItems(
            [cfg.DASH_OVERLAY_METHOD_ISHA, cfg.DASH_OVERLAY_METHOD_AVERAGE]
        )
        self.ui.cbb_card_dash_method.setCurrentText(
            cfg.get_card_plot_average_dash_overlay_method()
        )
        self.ui.cbb_card_simulation_view.addItems(
            [cfg.CARD_SIMULATION_VIEW_WINDOW_ONE, cfg.CARD_SIMULATION_VIEW_WINDOW_ALL]
        )
        self.ui.cbb_card_simulation_view.setCurrentText(
            cfg.get_card_simulation_view_window()
        )

        # --- Report ---
        self.ui.cb_logo_include.setChecked(cfg.get_logo_include_in_report())
        self.ui.le_logo_path.setText(cfg.get_logo_path())

        self.ui.cb_card_images_include.setChecked(cfg.get_report_card_include_images())
        self.ui.cbb_card_image_type.addItems(cfg.REPORT_CARD_IMAGE_TYPES)
        self.ui.cbb_card_image_type.setCurrentText(cfg.get_report_card_image_type())
        self.ui.sb_card_images_per_page.setValue(cfg.get_report_card_image_per_page())
        self.ui.cb_card_images_downsample.setChecked(
            cfg.get_report_card_image_downsample()
        )

    def _apply(self):
        # --- General ---
        cfg.set_datafile_dir(self.ui.le_datafile_dir.text())
        cfg.set_flyin_name(self.ui.le_flyin_name.text())
        cfg.set_flyin_location(self.ui.le_flyin_location.text())
        cfg.set_flyin_date(self.ui.le_flyin_date.text())
        cfg.set_flyin_analyst(self.ui.le_flyin_analyst.text())
        cfg.set_number_of_passes(self.ui.sb_number_passes.value())
        cfg.set_simulated_adjacent_passes(
            self.ui.sb_simulated_adjacent_passes.value()
        )
        cfg.set_center_method(self.ui.cbb_center_method.currentText())

        # --- Observables ---
        cfg.set_unit_wingspan(self.ui.cbb_wingspan_units.currentText())
        cfg.set_unit_swath(self.ui.cbb_swath_units.currentText())
        cfg.set_unit_rate(self.ui.cbb_rate_units.currentText())
        cfg.set_unit_pressure(self.ui.cbb_pressure_units.currentText())
        cfg.set_unit_boom_width(self.ui.cbb_boom_width_units.currentText())
        cfg.set_unit_boom_drop(self.ui.cbb_boom_drop_units.currentText())
        cfg.set_unit_nozzle_spacing(self.ui.cbb_nozzle_spacing_units.currentText())
        cfg.set_unit_ground_speed(self.ui.cbb_ground_speed_units.currentText())
        cfg.set_unit_spray_height(self.ui.cbb_spray_height_units.currentText())
        cfg.set_unit_wind_speed(self.ui.cbb_wind_speed_units.currentText())
        cfg.set_unit_temperature(self.ui.cbb_temperature_units.currentText())

        # --- String ---
        cfg.set_smooth_window(self.ui.dsb_smooth_window.value())
        cfg.set_smooth_order(self.ui.sb_smooth_order.value())
        cfg.set_string_plot_average_dash_overlay(
            self.ui.cb_string_dash_overlay.isChecked()
        )
        cfg.set_string_plot_average_dash_overlay_method(
            self.ui.cbb_string_dash_method.currentText()
        )
        cfg.set_string_simulation_view_window(
            self.ui.cbb_string_simulation_view.currentText()
        )
        cfg.set_string_drive_port(self.ui.cbb_string_drive_port.currentText())
        cfg.set_string_length(self.ui.dsb_string_length.value())
        cfg.set_unit_string_data_location(self.ui.cbb_string_length_units.currentText())
        cfg.set_string_speed(self.ui.dsb_string_speed.value())

        # --- Spray Cards ---
        cfg.set_image_load_method(self.ui.cbb_image_load_method.currentText())
        cfg.set_image_flip_x(self.ui.cb_flip_x.isChecked())
        cfg.set_image_flip_y(self.ui.cb_flip_y.isChecked())
        cfg.set_image_dpi(int(self.ui.cbb_image_dpi.currentText()))
        cfg.set_image_roi_acquisition_orientation(
            self.ui.cbb_roi_orientation.currentText()
        )
        cfg.set_image_roi_acquisition_order(self.ui.cbb_roi_order.currentText())
        cfg.set_image_roi_scale(int(self.ui.cbb_roi_scale.currentText()))
        cfg.set_threshold_type(self.ui.cbb_threshold_type.currentText())
        cfg.set_threshold_grayscale(self.ui.sb_threshold_grayscale.value())
        cfg.set_threshold_grayscale_method(
            self.ui.cbb_threshold_grayscale_method.currentText()
        )
        cfg.set_threshold_hsb_hue_min(self.ui.sb_hsb_hue_min.value())
        cfg.set_threshold_hsb_hue_max(self.ui.sb_hsb_hue_max.value())
        cfg.set_threshold_hsb_hue_pass(self.ui.cb_hsb_hue_pass.isChecked())
        cfg.set_threshold_hsb_saturation_min(self.ui.sb_hsb_sat_min.value())
        cfg.set_threshold_hsb_saturation_max(self.ui.sb_hsb_sat_max.value())
        cfg.set_threshold_hsb_saturation_pass(self.ui.cb_hsb_sat_pass.isChecked())
        cfg.set_threshold_hsb_brightness_min(self.ui.sb_hsb_brightness_min.value())
        cfg.set_threshold_hsb_brightness_max(self.ui.sb_hsb_brightness_max.value())
        cfg.set_threshold_hsb_brightness_pass(
            self.ui.cb_hsb_brightness_pass.isChecked()
        )
        cfg.set_watershed(self.ui.cb_watershed.isChecked())
        cfg.set_min_stain_area_px(self.ui.sb_min_stain_area.value())
        cfg.set_stain_approximation_method(
            self.ui.cbb_stain_approximation.currentText()
        )
        cfg.set_max_stain_count(self.ui.sb_max_stain_count.value())
        cfg.set_spread_factor_equation(self.ui.cbb_spread_equation.currentText())
        cfg.set_spread_factor_a(self.ui.dsb_spread_a.value())
        cfg.set_spread_factor_b(self.ui.dsb_spread_b.value())
        cfg.set_spread_factor_c(self.ui.dsb_spread_c.value())
        cfg.set_card_plot_y_axis(self.ui.cbb_card_plot_y_axis.currentText())
        cfg.set_card_plot_shading(self.ui.cb_card_shading.isChecked())
        cfg.set_card_plot_shading_method(self.ui.cbb_card_shading_method.currentText())
        cfg.set_card_plot_shading_interpolate(
            self.ui.cb_card_shading_interpolate.isChecked()
        )
        cfg.set_card_plot_average_dash_overlay(
            self.ui.cb_card_dash_overlay.isChecked()
        )
        cfg.set_card_plot_average_dash_overlay_method(
            self.ui.cbb_card_dash_method.currentText()
        )
        cfg.set_card_simulation_view_window(
            self.ui.cbb_card_simulation_view.currentText()
        )

        # --- Report ---
        cfg.set_logo_include_in_report(self.ui.cb_logo_include.isChecked())
        cfg.set_logo_path(self.ui.le_logo_path.text())
        cfg.set_report_card_include_images(self.ui.cb_card_images_include.isChecked())
        cfg.set_report_card_image_type(self.ui.cbb_card_image_type.currentText())
        cfg.set_report_card_image_per_page(self.ui.sb_card_images_per_page.value())
        cfg.set_report_card_image_downsample(
            self.ui.cb_card_images_downsample.isChecked()
        )

        self.settings_changed.emit()
        self.accept()

    def _update_string_length_unit_labels(self, units: str):
        self.ui.lbl_smooth_window_units.setText(units)
        self.ui.lbl_string_speed_units.setText(f"{units}/sec")

    def _reset_defaults(self):
        msg = QMessageBox.question(
            self,
            "Clear All User-Defined Defaults?",
            "This will permanently erase all user-defined defaults for AccuPatt on this computer and revert all to their originally provided values. This includes all user-defined spray card sets. This cannot be undone. Are you sure you want to do this?",
        )
        if msg == QMessageBox.StandardButton.Yes:
            cfg.clear_all_settings()
            QMessageBox.information(self, "Success", "All user-defined defaults erased successfully.")
            self.reject()

    def _browse_datafile_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Data File Directory",
            self.ui.le_datafile_dir.text(),
        )
        if directory:
            self.ui.le_datafile_dir.setText(directory)

    def _browse_logo_path(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Logo File",
            self.ui.le_logo_path.text(),
            "Images (*.png *.jpg *.jpeg *.bmp *.svg)",
        )
        if path:
            self.ui.le_logo_path.setText(path)
