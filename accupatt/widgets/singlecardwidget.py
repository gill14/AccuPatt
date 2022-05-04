from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap, QResizeEvent
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QGraphicsPixmapItem, QGraphicsScene

class SingleCardWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QHBoxLayout(self)
        #Show original
        self.pixmap_item_original = QGraphicsPixmapItem()
        scene1 = QGraphicsScene(self)
        scene1.addItem(self.pixmap_item_original)
        self.graphicsView1 = QtWidgets.QGraphicsView()
        layout.addWidget(self.graphicsView1)
        self.graphicsView1.setScene(scene1)

        #Signals for syncing scrollbars
        self.graphicsView1.verticalScrollBar().valueChanged[int].connect(self.scrollGV_V)
        self.graphicsView1.horizontalScrollBar().valueChanged[int].connect(self.scrollGV_H)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.resize_and_fit()

    def scrollGV_V(self, value):
        self.graphicsView1.verticalScrollBar().setValue(value)

    def scrollGV_H(self, value):
        self.graphicsView1.horizontalScrollBar().setValue(value)

    def updateSprayCardView(self, cvImg1=None):
        self.clearSprayCardView()
        if not cvImg1 is None:
            self.pixmap_item_original.setPixmap(QPixmap.fromImage(SingleCardWidget.qImg_from_cvImg(cvImg1)))
        #Auto-resize to fit width of card to width of graphicsView
        scene1 = self.graphicsView1.scene()
        scene1.setSceneRect(scene1.itemsBoundingRect())
        self.fit = Qt.AspectRatioMode.KeepAspectRatioByExpanding
        self.resize_and_fit()

    def clearSprayCardView(self):
        self.pixmap_item_original.setPixmap(QPixmap())

    def resize_and_fit(self):
        scene1 = self.graphicsView1.scene()
        scene1.setSceneRect(scene1.itemsBoundingRect())
        self.graphicsView1.fitInView(scene1.sceneRect(), self.fit)

    def qImg_from_cvImg(cvImg):
        height, width = cvImg.shape[:2]
        if len(cvImg.shape) == 2:
            bytesPerLine = 1 * width
            qImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format.Format_Grayscale8)
        elif len(cvImg.shape) == 3:
            bytesPerLine = 3 * width
            qImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format.Format_BGR888)
        return qImg
        