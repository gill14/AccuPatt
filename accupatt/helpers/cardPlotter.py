import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import RectangleSelector
import cv2
import numpy as np

class ROIViewer(object):
    def __init__(self):
        im = cv2.imread('/Users/gill14/Desktop/Scan.png')
        self.fig, self.ax = plt.subplots()
        self.ax.imshow(im)
        self.rect = patches.Rectangle((0, 0), 1, 1, linewidth=1, edgecolor='r', facecolor='none')
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.ax.add_patch(self.rect)
        self.ax.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.ax.figure.canvas.mpl_connect('button_release_event', self.on_release)

    def on_press(self, event):
        print('press')
        self.x0 = event.xdata
        self.y0 = event.ydata

    def on_release(self, event):
        print('release')
        self.x1 = event.xdata
        self.y1 = event.ydata
        self.rect.set_width(self.x1 - self.x0)
        self.rect.set_height(self.y1 - self.y0)
        self.rect.set_xy((self.x0, self.y0))
        self.ax.figure.canvas.draw()

class CardPlotter:
    
    def draw_pass_dvs(mplCanvas, pass_data, swath_units):
        ax = mplCanvas.ax
        ax.clear()
        ax.set_yticks([])
        ax.set_xlabel(f'Location ({swath_units})')

        cards = pass_data.spray_cards

#a = ROIViewer()
#plt.show()

#img_path='/Users/gill14/Desktop/L-8.png'
img_path='/Users/gill14/Desktop/Scan.png'
# Read image
img = cv2.imread(img_path)
img = cv2.resize(img, dsize=None, fx=0.1, fy=0.1, interpolation=cv2.INTER_AREA)


ROIs = cv2.selectROI('Select ROI', img, fromCenter=False)

for i, roi in enumerate(ROIs):
    cv2.imshow(str(i),img[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]])

#ROI_1 = img[ROIs[0][1]:ROIs[0][1]+ROIs[0][3], ROIs[0][0]:ROIs[0][0]+ROIs[0][2]]
#ROI_2 = img[ROIs[1][1]:ROIs[1][1]+ROIs[1][3], ROIs[1][0]:ROIs[1][0]+ROIs[1][2]]
#ROI_3 = img[ROIs[2][1]:ROIs[2][1]+ROIs[2][3], ROIs[2][0]:ROIs[2][0]+ROIs[2][2]]

#cv2.imshow('1', ROI_1)
#cv2.imshow('2', ROI_2)
#cv2.imshow('3', ROI_3)

cv2.waitKey(0)
cv2.destroyAllWindows()