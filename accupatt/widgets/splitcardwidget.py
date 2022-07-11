from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap, QResizeEvent
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QGraphicsPixmapItem, QGraphicsScene

import cv2

class SplitCardWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fit = Qt.AspectRatioMode.KeepAspectRatioByExpanding

        layout = QHBoxLayout(self)

        # Show original
        self.pixmap_item_original = QGraphicsPixmapItem()
        scene1 = QGraphicsScene(self)
        scene1.addItem(self.pixmap_item_original)
        self.graphicsView1 = QtWidgets.QGraphicsView()
        layout.addWidget(self.graphicsView1)
        self.graphicsView1.setScene(scene1)
        # Show threshold
        self.pixmap_item_thresh = QGraphicsPixmapItem()
        scene2 = QGraphicsScene(self)
        scene2.addItem(self.pixmap_item_thresh)
        self.graphicsView2 = QtWidgets.QGraphicsView()
        layout.addWidget(self.graphicsView2)
        self.graphicsView2.setScene(scene2)

        # Signals for syncing scrollbars
        self.graphicsView1.verticalScrollBar().valueChanged[int].connect(
            self.scrollGV_V
        )
        self.graphicsView2.verticalScrollBar().valueChanged[int].connect(
            self.scrollGV_V
        )
        self.graphicsView1.horizontalScrollBar().valueChanged[int].connect(
            self.scrollGV_H
        )
        self.graphicsView2.horizontalScrollBar().valueChanged[int].connect(
            self.scrollGV_H
        )

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.resize_and_fit()

    def scrollGV_V(self, value):
        self.graphicsView1.verticalScrollBar().setValue(value)
        self.graphicsView2.verticalScrollBar().setValue(value)

    def scrollGV_H(self, value):
        self.graphicsView1.horizontalScrollBar().setValue(value)
        self.graphicsView2.horizontalScrollBar().setValue(value)

    def updateSprayCardView(self, cvImg1=None, cvImg2=None, fit="horizontal"):
        self.clearSprayCardView()
        if not (cvImg1 is None or cvImg2 is None):
            # Left Image (1)
            self.pixmap_item_original.setPixmap(
                QPixmap.fromImage(SplitCardWidget.qImg_from_cvImg(cv2.cvtColor(cvImg1, cv2.COLOR_RGB2BGR)))
            )
            # Right Image(2)
            self.pixmap_item_thresh.setPixmap(
                QPixmap.fromImage(SplitCardWidget.qImg_from_cvImg(cv2.cvtColor(cvImg2, cv2.COLOR_RGB2BGR)))
            )
        # Auto-resize to fit width or height of card to width or height of graphicsView
        if fit == "horizontal":
            self.fit = Qt.AspectRatioMode.KeepAspectRatioByExpanding
        else:
            self.fit = Qt.AspectRatioMode.KeepAspectRatio
        self.resize_and_fit()

    def resize_and_fit(self):
        scene1 = self.graphicsView1.scene()
        scene1.setSceneRect(scene1.itemsBoundingRect())
        self.graphicsView1.fitInView(scene1.sceneRect(), self.fit)
        scene2 = self.graphicsView2.scene()
        scene2.setSceneRect(scene2.itemsBoundingRect())
        self.graphicsView2.fitInView(scene2.sceneRect(), self.fit)

    def clearSprayCardView(self):
        self.pixmap_item_original.setPixmap(QPixmap())
        self.pixmap_item_thresh.setPixmap(QPixmap())

    def qImg_from_cvImg(cvImg):
        height, width = cvImg.shape[:2]
        if len(cvImg.shape) == 2:
            bytesPerLine = 1 * width
            qImg = QImage(
                cvImg.data, width, height, bytesPerLine, QImage.Format.Format_Grayscale8
            )
        elif len(cvImg.shape) == 3:
            bytesPerLine = 3 * width
            qImg = QImage(
                cvImg.data, width, height, bytesPerLine, QImage.Format.Format_BGR888
            )
        return qImg
