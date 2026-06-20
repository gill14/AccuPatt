import operator
import os

from send2trash import send2trash

import accupatt.config as cfg
import cv2
import numpy as np
import pyqtgraph as pg
from accupatt.models.sprayCard import SprayCard
from PIL import Image
from PyQt6 import uic
from PyQt6.QtGui import QCursor, QImage, QImageReader, QPixmap
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QRectF
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QGraphicsPixmapItem,
    QListWidget,
    QMessageBox,
    QProgressDialog,
)
from pyqtgraph.functions import mkPen

Ui_Form, _ = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "loadCards.ui")
)
Ui_Form_Pre, baseclass_pre = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "loadCardsPreBatch.ui")
)


class _CardImageBase(QDialog):
    """Shared base for image-based card acquisition dialogs (file and scanner).

    Subclass must: call super().__init__(), do setupUi, then call _setup_shared_ui().
    Subclass must set self.img (QGraphicsPixmapItem) before draw_rois() is called.
    """

    def __init__(self, card_list: list[SprayCard], parent=None):
        super().__init__(parent=parent)
        self.card_list = card_list
        self.roi_rectangles: list = []
        self.rois: list = []
        self.display_scale: float = 1.0
        self.img: QGraphicsPixmapItem | None = None
        # Load persistent config
        self.dpi = cfg.get_image_dpi()
        self.orientation = cfg.get_image_roi_acquisition_orientation()
        self.order = cfg.get_image_roi_acquisition_order()
        self.scale = cfg.get_image_roi_scale()

    def _setup_shared_ui(self):
        """Wire shared controls and configure pyqtgraph. Call after setupUi."""
        self.ui.comboBoxDPI.addItems([str(dpi) for dpi in cfg.IMAGE_DPI_OPTIONS])
        self.ui.comboBoxDPI.setCurrentText(str(self.dpi))
        self.ui.comboBoxOrientation.addItems(cfg.ROI_ACQUISITION_ORIENTATIONS)
        self.ui.comboBoxOrientation.setCurrentIndex(
            cfg.ROI_ACQUISITION_ORIENTATIONS.index(self.orientation)
        )
        self.ui.comboBoxOrder.addItems(cfg.ROI_ACQUISITION_ORDERS)
        self.ui.comboBoxOrder.setCurrentIndex(
            cfg.ROI_ACQUISITION_ORDERS.index(self.order)
        )
        self.ui.comboBoxScale.addItems([f"{s}%" for s in cfg.ROI_SCALES])
        self.ui.comboBoxScale.setCurrentIndex(cfg.ROI_SCALES.index(self.scale))

        self.ui.comboBoxDPI.currentTextChanged[str].connect(self.dpi_changed)
        self.ui.comboBoxOrientation.currentIndexChanged[int].connect(
            self.orientation_changed
        )
        self.ui.comboBoxOrder.currentIndexChanged[int].connect(self.order_changed)
        self.ui.comboBoxScale.currentIndexChanged[int].connect(self.scale_changed)
        self.ui.buttonAddCard.clicked.connect(self.click_add_card)
        self.ui.buttonRemoveCard.clicked.connect(self.click_remove_card)

        pg.setConfigOptions(antialias=True)
        self.ui.plotWidget.getPlotItem().showAxis("left", False)
        self.ui.plotWidget.getPlotItem().showAxis("right", True)
        self.ui.plotWidget.getViewBox().setAspectLocked()

    def _persist_roi_config(self):
        cfg.set_image_dpi(int(self.ui.comboBoxDPI.currentText()))
        cfg.set_image_roi_acquisition_orientation(
            self.ui.comboBoxOrientation.currentText()
        )
        cfg.set_image_roi_acquisition_order(self.ui.comboBoxOrder.currentText())
        cfg.set_image_roi_scale(cfg.ROI_SCALES[self.ui.comboBoxScale.currentIndex()])

    def show_image_characteristics(self):
        if not hasattr(self, "_size_og_wh"):
            return
        w_px, h_px = self._size_og_wh
        self.ui.label_size.setText(f'{(w_px/self.dpi):.1f}"x{(h_px/self.dpi):.1f}"')
        self.ui.label_pixel_area.setText(f"{int(25400 / self.dpi)} microns")

    def draw_rois(self):
        if self.img is None:
            return
        self._sort_rois(self.orientation, self.order)
        for r in self.rois:
            self.ui.plotWidget.getViewBox().removeItem(r)
        self.rois = []
        for i, r in enumerate(self.roi_rectangles):
            if i < len(self.card_list):
                x, y, w, h = r
                roi = pg.RectROI(
                    [x, y],
                    [w, h],
                    pen=mkPen("m", width=3),
                    hoverPen=mkPen("r", width=5),
                    handlePen=mkPen("r", width=3),
                    handleHoverPen=mkPen("r", width=5),
                    removable=True,
                    centered=True,
                    sideScalers=True,
                    scaleSnap=True,
                    translateSnap=True,
                )
                roi.scale(s=float(self.scale) / 100, center=[0.5, 0.5])
                label = pg.TextItem(text=self.card_list[i].name, color="m")
                label.setParentItem(roi)
                roi.setParentItem(self.img)
                roi.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
                roi.sigClicked.connect(self.roi_clicked)
                roi.sigRemoveRequested.connect(self.remove_roi)
                self.rois.append(roi)
        self.ui.buttonAddCard.setEnabled(len(self.rois) < len(self.card_list))

    @pyqtSlot(str)
    def dpi_changed(self, newString):
        if newString == "":
            return
        try:
            self.dpi = int(newString)
        except Exception:
            return
        self.show_image_characteristics()

    @pyqtSlot(int)
    def orientation_changed(self, newIndex):
        self.orientation = cfg.ROI_ACQUISITION_ORIENTATIONS[newIndex]
        self.draw_rois()

    @pyqtSlot(int)
    def order_changed(self, newIndex):
        self.order = cfg.ROI_ACQUISITION_ORDERS[newIndex]
        self.draw_rois()

    @pyqtSlot(int)
    def scale_changed(self, newIndex):
        self.scale = cfg.ROI_SCALES[newIndex]
        self.draw_rois()

    @pyqtSlot(object)
    def remove_roi(self, roi):
        del self.roi_rectangles[self.rois.index(roi)]
        self.draw_rois()

    @pyqtSlot()
    def click_add_card(self):
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.CrossCursor))
        viewBox: pg.ViewBox = self.ui.plotWidget.getPlotItem().getViewBox()
        viewBox.setMouseMode(pg.ViewBox.RectMode)
        viewBox.rbScaleBox.setPen(pg.mkPen((0, 128, 0), width=1))
        viewBox.rbScaleBox.setBrush(pg.mkBrush(0, 128, 0, 100))

        def mouseDragEvent(ev, axis=None):
            ev.accept()
            if ev.button() & Qt.MouseButton.LeftButton:
                if viewBox.state["mouseMode"] == pg.ViewBox.RectMode and axis is None:
                    if ev.isFinish():
                        QTimer.singleShot(0, self.restoreCursor)
                        viewBox.rbScaleBox.hide()
                        ax = QRectF(
                            pg.Point(ev.buttonDownPos(ev.button())), pg.Point(ev.pos())
                        )
                        ax = viewBox.childGroup.mapRectFromParent(ax)
                        self.roi_rectangles.append(ax.getRect())
                        self.draw_rois()
                        viewBox.mouseDragEvent = temp
                        viewBox.setMouseMode(pg.ViewBox.PanMode)
                    else:
                        viewBox.updateScaleBox(ev.buttonDownPos(), ev.pos())

        def keyPressE_mouseDrag(event):
            if event.key() == Qt.Key.Key_Escape:
                QTimer.singleShot(0, self.restoreCursor)
                viewBox.rbScaleBox.hide()
                viewBox.mouseDragEvent = temp
                viewBox.setMouseMode(pg.ViewBox.PanMode)
            else:
                QDialog.keyPressEvent(self, event)

        self.keyPressEvent = keyPressE_mouseDrag
        temp = viewBox.mouseDragEvent
        viewBox.mouseDragEvent = mouseDragEvent

    def restoreCursor(self):
        QApplication.restoreOverrideCursor()
        self.ui.plotWidget.getViewBox().setMouseMode(pg.ViewBox.PanMode)

    @pyqtSlot(object, object)
    def roi_clicked(self, roi: pg.ROI, _):
        self.ui.buttonRemoveCard.setEnabled(True)
        self.roi_to_remove = roi
        self.ui.buttonRemoveCard.setText(
            "Remove " + self.card_list[self.rois.index(roi)].name
        )

    @pyqtSlot()
    def click_remove_card(self):
        self.remove_roi(self.roi_to_remove)
        self.ui.buttonRemoveCard.setText("Remove")
        self.ui.buttonRemoveCard.setEnabled(False)

    def _save_roi_crops_to_cards(
        self,
        img,
        effective_display_scale: float,
        origin_display: tuple[float, float] = (0.0, 0.0),
    ) -> bool:
        """Crop each ROI from img using effective_display_scale and save to cards.

        origin_display: display-pixel offset of the scan/image origin relative to the
        preview coordinate system. Used when the final scan covers only a sub-region.
        Returns False if user canceled the progress dialog.
        """
        prog = QProgressDialog(self)
        prog.setMinimumDuration(0)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        for i, roi in enumerate(self.rois):
            if i == 0:
                prog.setRange(0, len(self.rois))
            prog.setValue(i)
            prog.setLabelText(
                f"Cropping {self.card_list[i].name} and saving to the database"
            )
            if prog.wasCanceled():
                return False
            roi: pg.RectROI
            img_h, img_w = img.shape[:2]
            x = max(0, int((roi.pos()[0] - origin_display[0]) / effective_display_scale))
            y = max(0, int((roi.pos()[1] - origin_display[1]) / effective_display_scale))
            w = min(int(roi.size()[0] / effective_display_scale), img_w - x)
            h = min(int(roi.size()[1] / effective_display_scale), img_h - y)
            if w <= 0 or h <= 0:
                continue
            img_crop = img[y : y + h, x : x + w]
            _, buffer = cv2.imencode("*.png", img_crop)
            sprayCard: SprayCard = self.card_list[i]
            sprayCard.save_image_to_file(buffer)
            sprayCard.has_image = True
            sprayCard.current = False
            sprayCard.stats.current = False
            sprayCard.include_in_composite = True
            sprayCard.dpi = self.dpi
            if i == len(self.rois) - 1:
                prog.setValue(i + 1)
        return True

    def _find_rois(self, img) -> list:
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_gray = cv2.GaussianBlur(img_gray, (0, 0), 3, borderType=cv2.BORDER_REFLECT)

        def _detect(thresh_type):
            _, img_thresh = cv2.threshold(img_gray, 0, 255, thresh_type | cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(img_thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            return [r for r in [cv2.boundingRect(c) for c in contours] if self._check_roi_params(r, img.shape)]

        rois = _detect(cv2.THRESH_BINARY)
        return rois if rois else _detect(cv2.THRESH_BINARY_INV)

    def _check_roi_params(self, rectangle, img_shape) -> bool:
        x, y, w, h = rectangle
        if w < 0.05 * img_shape[1] or h < 0.05 * img_shape[0]:
            return False
        if w > 0.95 * img_shape[1] and h > 0.95 * img_shape[0]:
            return False
        return True

    def _sort_rois(self, orientation, order):
        rois_original = self.roi_rectangles.copy()
        rois_sorted = []
        while len(rois_sorted) < len(self.roi_rectangles):
            dists_from_origin = []
            for r in rois_original:
                x, y, w, h = r
                dists_from_origin.append(np.sqrt(x**2 + y**2))
            x1, y1, w1, h1 = [
                r for _, r in sorted(zip(dists_from_origin, rois_original))
            ][0]
            current = []
            for r in rois_original:
                x, y, w, h = r
                if orientation == "Horizontal":
                    y_c = y + h / 2
                    if y_c >= y1 and y_c <= y1 + h1:
                        current.append(r)
                else:
                    x_c = x + w / 2
                    if x_c >= x1 and x_c <= x1 + w1:
                        current.append(r)
            current = sorted(
                current,
                key=operator.itemgetter(0 if orientation == "Horizontal" else 1),
                reverse=(order == "Decreasing"),
            )
            if order == "Decreasing":
                rois_sorted[0:0] = current
            else:
                rois_sorted.extend(current)
            rois_original = [r for r in rois_original if r not in current]
        self.roi_rectangles = rois_sorted


class LoadCards(_CardImageBase):
    applied = pyqtSignal()

    def __init__(self, image_file: str, card_list: list[SprayCard], parent=None):
        super().__init__(card_list=card_list, parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._setup_shared_ui()

        self.image_file = image_file

        self.ui.checkBoxFlipHorizontal.setChecked(cfg.get_image_flip_x())
        self.ui.checkBoxFlipVertical.setChecked(cfg.get_image_flip_y())
        self.ui.checkBoxFlipHorizontal.toggled[bool].connect(self.flip_x_changed)
        self.ui.checkBoxFlipVertical.toggled[bool].connect(self.flip_y_changed)

        self.plot_image()

        self.show()
        self.show_image_characteristics()

    def plot_image(self):
        image_reader = QImageReader(self.image_file)
        image_reader.setAllocationLimit(1024)
        size_og = image_reader.size()
        self._size_og_wh = (size_og.width(), size_og.height())
        size_mod = size_og
        if size_og.width() * size_og.height() > 33000000:
            scale = min([2000 / size_mod.width(), 2000 / size_mod.height()])
            size_mod = size_mod.scaled(
                int(size_mod.width() * scale),
                int(size_mod.height() * scale),
                Qt.AspectRatioMode.IgnoreAspectRatio,
            )
        self.display_scale = size_mod.width() / size_og.width()
        image_reader.setScaledSize(size_mod)
        qimg = image_reader.read()
        qimg = qimg.mirrored(
            horizontal=cfg.get_image_flip_x(), vertical=cfg.get_image_flip_y()
        )
        qimg_rgba = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
        ptr = qimg_rgba.bits()
        h, w = qimg_rgba.height(), qimg_rgba.width()
        ptr.setsize(h * w * 4)
        img_display = cv2.cvtColor(
            np.frombuffer(ptr, dtype=np.uint8).reshape(h, w, 4).copy(),
            cv2.COLOR_RGBA2BGR,
        )
        self.img_pixmap = QPixmap.fromImage(qimg)
        self.img = QGraphicsPixmapItem(self.img_pixmap)

        self.ui.plotWidget.clear()
        self.ui.plotWidget.addItem(self.img)
        self.ui.plotWidget.getPlotItem().invertY(True)

        self.dpi = round(Image.open(self.image_file).info["dpi"][0])
        self.ui.comboBoxDPI.setCurrentText(str(self.dpi))
        self.show_image_characteristics()

        self.roi_rectangles = self._find_rois(img_display)
        self.rois = []
        self.draw_rois()

    @pyqtSlot(bool)
    def flip_x_changed(self, isFlip: bool):
        cfg.set_image_flip_x(isFlip)
        self.plot_image()

    @pyqtSlot(bool)
    def flip_y_changed(self, isFlip: bool):
        cfg.set_image_flip_y(isFlip)
        self.plot_image()

    @pyqtSlot()
    def accept(self):
        self._persist_roi_config()

        img = cv2.imread(self.image_file)
        if cfg.get_image_flip_x():
            img = cv2.flip(img, 1)
        if cfg.get_image_flip_y():
            img = cv2.flip(img, 0)

        if not self._save_roi_crops_to_cards(img, self.display_scale):
            return

        self.prompt_to_delete_original()
        super().accept()

    def prompt_to_delete_original(self):
        msg = QMessageBox()
        msg.setParent(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText("Trash Original File?")
        msg.setInformativeText(
            "All chosen regions have been cropped from the original image and sucessfully saved to the database."
        )
        msg.setWindowModality(Qt.WindowModality.WindowModal)
        button_delete = msg.addButton("Trash", QMessageBox.ButtonRole.ActionRole)
        button_do_not_delete = msg.addButton("Keep", QMessageBox.ButtonRole.ActionRole)
        msg.setDefaultButton(button_do_not_delete)
        msg.exec()
        if msg.clickedButton() == button_delete:
            send2trash(os.path.abspath(self.image_file))


class LoadCardsPreBatch(baseclass_pre):
    def __init__(self, image_files: list[str], card_list: list[SprayCard], parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form_Pre()
        self.ui.setupUi(self)

        self.cards = card_list
        self.files = image_files

        self.lwc: QListWidget = self.ui.listWidgetCard
        self.lwf: QListWidget = self.ui.listWidgetFile
        self.cbc: QCheckBox = self.ui.checkBoxCrop
        self.cbd: QComboBox = self.ui.comboBoxDpi

        self.lwc.verticalScrollBar().valueChanged.connect(self.lwf.verticalScrollBar().setValue)
        self.lwf.verticalScrollBar().valueChanged.connect(self.lwc.verticalScrollBar().setValue)

        self.lwc.addItems([c.name for c in self.cards])
        self.lwf.addItems(self.files)
        self.cbd.addItem("Auto")
        self.cbd.addItems([str(dpi) for dpi in cfg.IMAGE_DPI_OPTIONS])

        self.show()

    def accept(self):
        if self.cbc.isChecked():
            # TODO Send to Load Cards in loop
            pass
        else:
            for i in range(self.lwf.count()):
                if i < len(self.cards):
                    with open(self.lwf.item(i).text(), "rb") as file:
                        binary_data = file.read()
                    c = self.cards[i]
                    c.has_image = True
                    c.current = False
                    c.stats.current = False
                    c.include_in_composite = True
                    if self.cbd.currentIndex() == 0:
                        c.dpi = round(
                            Image.open(self.lwf.item(i).text()).info["dpi"][0]
                        )
                    else:
                        c.dpi = int(self.cbd.currentText())
                    c.save_image_to_file(image=binary_data)

        super().accept()
