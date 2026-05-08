import os

import accupatt.config as cfg
import cv2
import numpy as np
from PIL import Image
from accupatt.models.sprayCard import SprayCard
from accupatt.windows.loadCards import _CardImageBase
from PyQt6 import uic
from PyQt6.QtCore import Qt, QEventLoop, QObject, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QDialogButtonBox,
    QGraphicsPixmapItem,
    QMessageBox,
    QProgressDialog,
)

Ui_Form, _ = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "scanCards.ui")
)

try:
    from Foundation import NSObject, NSRunLoop, NSDate, NSDefaultRunLoopMode
    from ImageCaptureCore import (
        ICDeviceBrowser,
        ICScannerDevice,
        ICScannerPixelDataTypeRGB,
        ICScannerBitDepth8Bits,
        ICScannerFunctionalUnitTypeFlatbed,
        ICDeviceTypeMaskScanner,
        ICDeviceLocationTypeMaskLocal,
        ICDeviceLocationTypeMaskBonjour,
        ICDeviceLocationTypeMaskBluetooth,
        ICDeviceLocationTypeMaskShared,
    )
    # Combined mask: all location types, scanner devices only
    _ICA_SCANNER_MASK = (
        ICDeviceTypeMaskScanner
        | ICDeviceLocationTypeMaskLocal
        | ICDeviceLocationTypeMaskBonjour
        | ICDeviceLocationTypeMaskBluetooth
        | ICDeviceLocationTypeMaskShared
    )
    _ICA_AVAILABLE = True
except ImportError:
    _ICA_AVAILABLE = False

# ICA delivers all callbacks on this custom run loop mode, not NSDefaultRunLoopMode.
# Qt's event loop never services it, so we must pump it explicitly.
_ICA_RUN_LOOP_MODE = "com.apple.ImageCaptureCore"


# ---------------------------------------------------------------------------
# Qt signal carriers — bridge ICA Objective-C delegate callbacks to Qt slots
# ---------------------------------------------------------------------------

class _BrowserSignals(QObject):
    device_added = pyqtSignal(object, bool)  # (ICScannerDevice, more_coming)
    device_removed = pyqtSignal(object)      # ICScannerDevice


class _ScannerSignals(QObject):
    session_opened = pyqtSignal(object)  # NSError or None
    fu_selected = pyqtSignal(object)     # NSError or None (functional unit selected)
    scan_done = pyqtSignal(str)          # path to TIFF file
    scan_failed = pyqtSignal(str)        # error description


# ---------------------------------------------------------------------------
# ICA Objective-C delegates
# ---------------------------------------------------------------------------

if _ICA_AVAILABLE:

    class _ICABrowserDelegate(NSObject):
        # Set as instance attribute after alloc().init(); class-level None is the fallback.
        _signals = None

        def deviceBrowser_didAddDevice_moreComing_(self, browser, device, more_coming):
            if self._signals and isinstance(device, ICScannerDevice):
                self._signals.device_added.emit(device, bool(more_coming))

        def deviceBrowser_didRemoveDevice_moreGoing_(self, browser, device, more_going):
            if self._signals:
                self._signals.device_removed.emit(device)

    class _ICAScannerDelegate(NSObject):
        # Set as instance attribute after alloc().init(); class-level None is the fallback.
        _signals = None

        def device_didOpenSessionWithError_(self, device, error):
            if self._signals:
                self._signals.session_opened.emit(error)

        def scannerDevice_didSelectFunctionalUnit_error_(self, scanner, fu, error):
            if self._signals:
                self._signals.fu_selected.emit(error)

        def scannerDevice_didScanToURL_(self, scanner, url):
            if self._signals:
                path = url.path() if url else None
                if path:
                    self._signals.scan_done.emit(path)
                else:
                    self._signals.scan_failed.emit("Scan produced no output file.")

        def scannerDevice_didScanToURL_data_(self, scanner, url, data):
            # Older ICA versions use this three-argument variant
            if self._signals:
                path = url.path() if url else None
                if path:
                    self._signals.scan_done.emit(path)
                else:
                    self._signals.scan_failed.emit("Scan produced no output file.")

        def device_didEncounterError_(self, device, error):
            if self._signals:
                msg = str(error.localizedDescription()) if error else "Unknown device error"
                self._signals.scan_failed.emit(msg)


# ---------------------------------------------------------------------------
# ScanCards dialog
# ---------------------------------------------------------------------------

class ScanCards(_CardImageBase):
    """Acquire spray card images from a macOS-compatible flatbed scanner.

    Workflow:
      1. Scanner devices are discovered automatically via ImageCaptureCore.
      2. Click "Preview Scan" → 75 DPI image displayed with auto-detected ROIs.
      3. Adjust ROIs interactively (same controls as LoadCards).
      4. Click OK → high-res scan at selected DPI, ROIs cropped and saved to database.
    """

    def __init__(self, card_list: list[SprayCard], parent=None):
        super().__init__(card_list=card_list, parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._setup_shared_ui()

        self._preview_dpi: int = cfg.SCANNER_PREVIEW_DPI
        self._preview_img_raw: np.ndarray | None = None  # unflipped BGR array from preview scan

        # ICA state
        self._browser: "ICDeviceBrowser | None" = None
        self._browser_delegate: "_ICABrowserDelegate | None" = None
        self._browser_signals: "_BrowserSignals | None" = None
        self._scanner_delegate: "_ICAScannerDelegate | None" = None
        self._scanner_signals: "_ScannerSignals | None" = None
        self._session_open: bool = False
        self._scan_gen: int = 0  # incremented each scan; guards against stale callbacks

        # Pump the ICA run loop mode so callbacks are delivered while Qt owns the event loop
        self._ica_pump_timer = QTimer(self)
        self._ica_pump_timer.setInterval(50)
        self._ica_pump_timer.timeout.connect(self._pump_ica_events)

        # OK button disabled until a preview scan completes
        self._ok_button = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if self._ok_button:
            self._ok_button.setEnabled(False)

        self.ui.buttonRefreshDevices.clicked.connect(self._on_refresh)
        self.ui.buttonPreviewScan.clicked.connect(self._on_preview_scan)
        self.ui.checkBoxFlipHorizontal.setChecked(cfg.get_image_flip_x())
        self.ui.checkBoxFlipVertical.setChecked(cfg.get_image_flip_y())
        self.ui.checkBoxFlipHorizontal.toggled[bool].connect(self._flip_x_changed)
        self.ui.checkBoxFlipVertical.toggled[bool].connect(self._flip_y_changed)

        # Clean up ICA session when dialog closes (OK or Cancel)
        self.finished.connect(self._cleanup)

        if not _ICA_AVAILABLE:
            self._set_status(
                "ImageCaptureCore is not available. "
                "Install pyobjc-framework-ImageCaptureCore to enable scanner support."
            )
            self.ui.buttonPreviewScan.setEnabled(False)
            self.ui.buttonRefreshDevices.setEnabled(False)
        else:
            self._set_status("Searching for scanners…")
            QTimer.singleShot(200, self._start_browser)

        self.show()

    # ------------------------------------------------------------------
    # Device browser
    # ------------------------------------------------------------------

    def _pump_ica_events(self):
        """Service both ICA's private run loop mode and the default mode briefly."""
        if _ICA_AVAILABLE:
            now = NSDate.dateWithTimeIntervalSinceNow_(0.0)
            NSRunLoop.currentRunLoop().runMode_beforeDate_(NSDefaultRunLoopMode, now)
            NSRunLoop.currentRunLoop().runMode_beforeDate_(_ICA_RUN_LOOP_MODE, now)

    def _start_browser(self):
        self._browser_signals = _BrowserSignals()
        self._browser_signals.device_added.connect(self._on_device_added)
        self._browser_signals.device_removed.connect(self._on_device_removed)

        self._browser_delegate = _ICABrowserDelegate.alloc().init()
        self._browser_delegate._signals = self._browser_signals

        self._browser = ICDeviceBrowser.alloc().init()
        self._browser.setDelegate_(self._browser_delegate)
        self._browser.setBrowsedDeviceTypeMask_(_ICA_SCANNER_MASK)
        self._browser.start()
        self._ica_pump_timer.start()

    @pyqtSlot()
    def _on_refresh(self):
        if self._browser:
            try:
                self._browser.setDelegate_(None)
            except Exception:
                pass
            self._browser.stop()
            self._browser = None
        self.ui.comboBoxDevice.clear()
        self.ui.buttonPreviewScan.setEnabled(False)
        self._set_status("Searching for scanners…")
        self._start_browser()

    @pyqtSlot(object, bool)
    def _on_device_added(self, device, more_coming: bool):
        label = str(device.name()) if hasattr(device, "name") else "Scanner"
        self.ui.comboBoxDevice.addItem(label, userData=device)
        # Enable scan button as soon as any device is present
        self.ui.buttonPreviewScan.setEnabled(True)
        count = self.ui.comboBoxDevice.count()
        if not more_coming:
            self._set_status(
                f"Found {count} scanner(s). Click 'Preview Scan' to begin."
            )
            # Restore last-used device selection
            last = cfg.get_scanner_device()
            for i in range(count):
                if str(self.ui.comboBoxDevice.itemData(i).name()) == last:
                    self.ui.comboBoxDevice.setCurrentIndex(i)
                    break
        else:
            self._set_status(f"Found {count} scanner(s) so far…")

    @pyqtSlot(object)
    def _on_device_removed(self, device):
        for i in range(self.ui.comboBoxDevice.count()):
            if self.ui.comboBoxDevice.itemData(i) is device:
                self.ui.comboBoxDevice.removeItem(i)
                break
        if self.ui.comboBoxDevice.count() == 0:
            self.ui.buttonPreviewScan.setEnabled(False)
            self._set_status("No scanners connected.")

    def _current_device(self):
        idx = self.ui.comboBoxDevice.currentIndex()
        return self.ui.comboBoxDevice.itemData(idx) if idx >= 0 else None

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def _ensure_session(self, device) -> bool:
        """Open an ICA session and select the flatbed functional unit. Returns True on success."""
        if self._session_open:
            return True

        self._scanner_signals = _ScannerSignals()
        self._scanner_delegate = _ICAScannerDelegate.alloc().init()
        self._scanner_delegate._signals = self._scanner_signals
        device.setDelegate_(self._scanner_delegate)

        # Step 1: open session
        loop = QEventLoop()
        session_error = [None]
        timed_out = [False]

        def on_opened(error):
            session_error[0] = error
            loop.quit()

        def on_timeout():
            timed_out[0] = True
            loop.quit()

        self._scanner_signals.session_opened.connect(on_opened)
        QTimer.singleShot(10_000, on_timeout)
        device.requestOpenSession()
        loop.exec()

        if timed_out[0]:
            self._set_status("Timed out waiting for scanner session.")
            return False
        if session_error[0] is not None:
            msg = str(session_error[0].localizedDescription())
            self._set_status(f"Could not open scanner session: {msg}")
            return False

        # Step 2: select the flatbed functional unit
        loop2 = QEventLoop()
        fu_error = [None]
        fu_timed_out = [False]

        def on_fu_selected(error):
            fu_error[0] = error
            loop2.quit()

        def on_fu_timeout():
            fu_timed_out[0] = True
            loop2.quit()

        self._scanner_signals.fu_selected.connect(on_fu_selected)
        QTimer.singleShot(10_000, on_fu_timeout)
        device.requestSelectFunctionalUnit_(ICScannerFunctionalUnitTypeFlatbed)
        loop2.exec()

        if fu_timed_out[0]:
            self._set_status("Timed out waiting for scanner functional unit.")
            return False
        if fu_error[0] is not None:
            msg = str(fu_error[0].localizedDescription())
            self._set_status(f"Could not select flatbed unit: {msg}")
            return False

        self._session_open = True
        return True

    def _close_session(self, device):
        if self._session_open and device is not None:
            device.requestCloseSession()
            self._session_open = False

    # ------------------------------------------------------------------
    # Scan acquisition
    # ------------------------------------------------------------------

    def _acquire_scan(
        self,
        device,
        dpi: int,
        label: str,
        scan_area_in: tuple[float, float, float, float] | None = None,
    ) -> np.ndarray | None:
        """Open session, configure resolution and scan area, scan, return BGR array.

        scan_area_in: (x, y, w, h) in physical inches. None = full bed.
        """
        if not self._ensure_session(device):
            return None

        fu = device.selectedFunctionalUnit()
        if fu is None:
            self._set_status("Scanner has no active functional unit.")
            return None

        actual_dpi = self._nearest_resolution(fu, dpi)
        fu.setResolution_(actual_dpi)
        fu.setPixelDataType_(ICScannerPixelDataTypeRGB)
        fu.setBitDepth_(ICScannerBitDepth8Bits)

        # ICA requires an explicit scan area; a zero-sized rect causes the scan to abort.
        if scan_area_in is not None:
            x, y, w, h = scan_area_in
        else:
            phys = fu.physicalSize()
            x, y, w, h = 0.0, 0.0, phys.width, phys.height
        fu.setScanArea_(((x, y), (w, h)))

        # Show progress and scan
        prog = QProgressDialog(label, None, 0, 0, self)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.setMinimumDuration(0)
        prog.setValue(0)

        # Increment generation so any callback from a previous scan is ignored.
        self._scan_gen += 1
        my_gen = self._scan_gen

        signals = _ScannerSignals()
        self._scanner_delegate._signals = signals

        loop = QEventLoop()
        tiff_path: list[str | None] = [None]
        error_msg: list[str | None] = [None]

        def on_done(path: str):
            if self._scan_gen == my_gen:
                tiff_path[0] = path
                loop.quit()

        def on_failed(msg: str):
            if self._scan_gen == my_gen:
                error_msg[0] = msg
                loop.quit()

        signals.scan_done.connect(on_done)
        signals.scan_failed.connect(on_failed)
        QTimer.singleShot(120_000, loop.quit)  # 2-minute hard timeout

        device.requestScan()
        loop.exec()
        prog.close()

        if error_msg[0]:
            self._set_status(f"Scan failed: {error_msg[0]}")
            QMessageBox.critical(self, "Scan Error", error_msg[0])
            return None
        if not tiff_path[0]:
            self._set_status("Scan timed out or produced no output.")
            return None

        pil_img = Image.open(tiff_path[0]).convert("RGB")
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    @staticmethod
    def _nearest_resolution(fu, requested_dpi: int) -> int:
        """Return the closest supported resolution to requested_dpi."""
        try:
            supported = set(fu.supportedResolutions())
            if not supported:
                return requested_dpi
            return min(supported, key=lambda r: abs(r - requested_dpi))
        except Exception:
            return requested_dpi

    # ------------------------------------------------------------------
    # Preview scan
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _on_preview_scan(self):
        device = self._current_device()
        if device is None:
            QMessageBox.warning(self, "No Scanner", "Please select a scanner device.")
            return

        self._set_status(f"Preview scan at {self._preview_dpi} DPI…")
        img_bgr = self._acquire_scan(
            device,
            self._preview_dpi,
            f"Preview scan in progress ({self._preview_dpi} DPI)…",
        )
        if img_bgr is None:
            return

        self._preview_img_raw = img_bgr
        self._display_preview(img_bgr)

    @pyqtSlot(bool)
    def _flip_x_changed(self, checked: bool):
        cfg.set_image_flip_x(checked)
        if self._preview_img_raw is not None:
            self._display_preview(self._preview_img_raw)

    @pyqtSlot(bool)
    def _flip_y_changed(self, checked: bool):
        cfg.set_image_flip_y(checked)
        if self._preview_img_raw is not None:
            self._display_preview(self._preview_img_raw)

    def _display_preview(self, img_bgr: np.ndarray):
        if self.ui.checkBoxFlipHorizontal.isChecked():
            img_bgr = cv2.flip(img_bgr, 1)
        if self.ui.checkBoxFlipVertical.isChecked():
            img_bgr = cv2.flip(img_bgr, 0)
        h_full, w_full = img_bgr.shape[:2]
        self._size_og_wh = (w_full, h_full)

        # Scale down for display if >33 MP (same threshold as LoadCards)
        if w_full * h_full > 33_000_000:
            scale = min(2000 / w_full, 2000 / h_full)
            new_w, new_h = int(w_full * scale), int(h_full * scale)
            img_display = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            scale = 1.0
            img_display = img_bgr

        self.display_scale = scale

        # BGR → RGB → QImage → QPixmap
        img_rgb = cv2.cvtColor(img_display, cv2.COLOR_BGR2RGB)
        dh, dw = img_rgb.shape[:2]
        qimg = QImage(img_rgb.data, dw, dh, 3 * dw, QImage.Format.Format_RGB888).copy()
        self.img = QGraphicsPixmapItem(QPixmap.fromImage(qimg))
        self.ui.plotWidget.clear()
        self.ui.plotWidget.addItem(self.img)
        self.ui.plotWidget.getPlotItem().invertY(True)

        self.ui.comboBoxDPI.setCurrentText(str(self.dpi))
        self.show_image_characteristics()

        self.roi_rectangles = self._find_rois(img_display)
        self.rois = []
        self.draw_rois()

        self._set_status(
            f"Preview complete ({w_full}×{h_full} px at {self._preview_dpi} DPI). "
            "Adjust ROIs, then click OK to perform the final high-res scan."
        )
        if self._ok_button:
            self._ok_button.setEnabled(True)

    # ------------------------------------------------------------------
    # Accept (final scan)
    # ------------------------------------------------------------------

    @pyqtSlot()
    def accept(self):
        if not self.rois:
            QMessageBox.information(
                self,
                "No ROIs",
                "No card regions are defined. Perform a preview scan and assign ROIs first.",
            )
            return

        device = self._current_device()
        if device is None:
            QMessageBox.warning(self, "No Scanner", "Please select a scanner device.")
            return

        self._persist_roi_config()
        try:
            cfg.set_scanner_device(str(device.name()))
        except Exception:
            pass

        preview_w, preview_h = self._size_og_wh        # unflipped preview dimensions (px)
        flip_x = self.ui.checkBoxFlipHorizontal.isChecked()
        flip_y = self.ui.checkBoxFlipVertical.isChecked()
        ds = self.display_scale
        pad_prev = 0.25 * self._preview_dpi             # 0.25" padding in preview pixels

        def to_unflipped_preview(x_d: float, y_d: float) -> tuple[float, float]:
            """Display pixel → unflipped preview pixel."""
            x, y = x_d / ds, y_d / ds
            if flip_x:
                x = preview_w - x
            if flip_y:
                y = preview_h - y
            return x, y

        # Bounding box of all ROI corners in unflipped preview pixels
        corners = []
        for roi in self.rois:
            x_d, y_d = roi.pos()
            w_d, h_d = roi.size()
            corners.append(to_unflipped_preview(x_d,       y_d      ))
            corners.append(to_unflipped_preview(x_d + w_d, y_d + h_d))

        sa_left  = max(0.0,       min(c[0] for c in corners) - pad_prev)
        sa_top   = max(0.0,       min(c[1] for c in corners) - pad_prev)
        sa_right = min(preview_w, max(c[0] for c in corners) + pad_prev)
        sa_bot   = min(preview_h, max(c[1] for c in corners) + pad_prev)

        scan_area_in = (
            sa_left / self._preview_dpi,
            sa_top  / self._preview_dpi,
            (sa_right - sa_left) / self._preview_dpi,
            (sa_bot   - sa_top)  / self._preview_dpi,
        )

        img_full = self._acquire_scan(
            device,
            self.dpi,
            f"Final scan in progress ({self.dpi} DPI)…",
            scan_area_in=scan_area_in,
        )
        if img_full is None:
            return

        # img_full is unflipped (ICA physical coordinates).  Convert each display-space
        # ROI corner to final-scan pixel space: undo display scale, undo flip, scale by
        # DPI ratio, subtract scan area origin.
        ratio = self.dpi / self._preview_dpi

        def to_scan_px(x_d: float, y_d: float) -> tuple[float, float]:
            x, y = to_unflipped_preview(x_d, y_d)
            return (x - sa_left) * ratio, (y - sa_top) * ratio

        img_h, img_w = img_full.shape[:2]

        prog = QProgressDialog(self)
        prog.setMinimumDuration(0)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.setRange(0, len(self.rois))

        for i, roi in enumerate(self.rois):
            prog.setValue(i)
            prog.setLabelText(
                f"Cropping {self.card_list[i].name} and saving to the database"
            )
            if prog.wasCanceled():
                return

            x_d, y_d = roi.pos()
            w_d, h_d = roi.size()
            x1, y1 = to_scan_px(x_d,       y_d      )
            x2, y2 = to_scan_px(x_d + w_d, y_d + h_d)

            x_lo = max(0, int(min(x1, x2)))
            y_lo = max(0, int(min(y1, y2)))
            x_hi = min(img_w, int(max(x1, x2)))
            y_hi = min(img_h, int(max(y1, y2)))

            if x_hi <= x_lo or y_hi <= y_lo:
                continue

            img_crop = img_full[y_lo:y_hi, x_lo:x_hi]
            _, buffer = cv2.imencode("*.png", img_crop)

            card = self.card_list[i]
            card.save_image_to_file(buffer)
            card.has_image = True
            card.include_in_composite = True
            card.dpi = self.dpi

        prog.setValue(len(self.rois))
        super().accept()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _cleanup(self):
        self._ica_pump_timer.stop()
        # Detach delegates before any teardown so ICA has no Python objects to
        # call back into when the session closes and the browser stops.
        device = self._current_device()
        if device is not None:
            self._close_session(device)
            try:
                device.setDelegate_(None)
            except Exception:
                pass
        if self._browser is not None:
            try:
                self._browser.setDelegate_(None)
            except Exception:
                pass
            self._browser.stop()
            self._browser = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, text: str):
        self.ui.labelStatus.setText(text)
