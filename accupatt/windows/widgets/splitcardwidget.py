from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QResizeEvent
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QGraphicsPixmapItem, QGraphicsScene

class SplitCardWidget(QWidget):
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
        #Show threshold
        self.pixmap_item_thresh = QGraphicsPixmapItem()
        scene2 = QGraphicsScene(self)
        scene2.addItem(self.pixmap_item_thresh)
        self.graphicsView2 = QtWidgets.QGraphicsView()
        layout.addWidget(self.graphicsView2)
        self.graphicsView2.setScene(scene2)

        #Signals for syncing scrollbars
        self.graphicsView1.verticalScrollBar().valueChanged[int].connect(self.scrollGV_V)
        self.graphicsView2.verticalScrollBar().valueChanged[int].connect(self.scrollGV_V)
        self.graphicsView1.horizontalScrollBar().valueChanged[int].connect(self.scrollGV_H)
        self.graphicsView2.horizontalScrollBar().valueChanged[int].connect(self.scrollGV_H)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.updateSprayCardView()

    def scrollGV_V(self, value):
        self.graphicsView1.verticalScrollBar().setValue(value)
        self.graphicsView2.verticalScrollBar().setValue(value)

    def scrollGV_H(self, value):
        self.graphicsView1.horizontalScrollBar().setValue(value)
        self.graphicsView2.horizontalScrollBar().setValue(value)

    def updateSprayCardView(self, cvImg1=None, cvImg2=None):
        if not (cvImg1 is None or cvImg2 is None):
            #Left Image (1)
            self.pixmap_item_original.setPixmap(QPixmap.fromImage(SplitCardWidget.qImg_from_cvImg(cvImg1)))
            #Right Image(2)
            self.pixmap_item_thresh.setPixmap(QPixmap.fromImage(SplitCardWidget.qImg_from_cvImg(cvImg2)))
        #Auto-resize to fit width of crad to width of graphicsView
        scene = self.graphicsView2.scene()
        scene.setSceneRect(scene.itemsBoundingRect())
        self.graphicsView2.fitInView(scene.sceneRect(), Qt.KeepAspectRatioByExpanding)
        self.graphicsView1.fitInView(scene.sceneRect(), Qt.KeepAspectRatioByExpanding)

    def qImg_from_cvImg(cvImg):
        height, width = cvImg.shape[:2]
        if len(cvImg.shape) == 2:
            bytesPerLine = 1 * width
            qImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format_Grayscale8)
        elif len(cvImg.shape) == 3:
            bytesPerLine = 3 * width
            qImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
        return qImg
        