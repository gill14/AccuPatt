#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  5 14:00:30 2020

@author: bradleyfritz
"""
import os, fnmatch, glob
from skimage import io
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from skimage.segmentation import watershed
from skimage.filters import (threshold_sauvola)
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage import measure
from skimage.measure import regionprops, label
from skimage.color import rgb2gray
from skimage.util import img_as_ubyte
from matplotlib.patches import Circle
from skimage.filters import threshold_otsu
from skimage.segmentation import clear_border
from skimage.morphology import closing, square
from skimage.color import label2rgb

import matplotlib.patches as mpatches


#imgOrg = cv2.imread('BradTest1Card.bmp',cv2.IMREAD_GRAYSCALE)
#imgOrg = cv2.imread('Scan0.bmp',cv2.IMREAD_GRAYSCALE)

def LinearExtrapolateVolDia(DF,Frac):
    x1 = DF.loc[DF['CumVolFrac']<Frac][-1:]['CumVolFrac'].values[0]
    x2 = DF.loc[DF['CumVolFrac']>Frac][0:]['CumVolFrac'].values[0]
    y1 = DF.loc[DF['CumVolFrac']<Frac][-1:]['MidBin'].values[0]
    y2 = DF.loc[DF['CumVolFrac']>Frac][0:]['MidBin'].values[0]

    VolDia = y1 + (Frac - x1)/(x2 - x1) * (y2 - y1)
    return VolDia

def CropROI(imgOrg):
    
    ImgList = []
    ImgNum = 0
    
    # apply threshold
    thresh = threshold_otsu(imgOrg)
    bw = closing(imgOrg > thresh, square(5))
    
    # label image regions
    label_image = label(bw)
    # to make the background transparent, pass the value of `bg_label`,
    # and leave `bg_color` as `None` and `kind` as `overlay`
    image_label_overlay = label2rgb(label_image, image=imgOrg, bg_label=0)
    
    for region in regionprops(label_image):
        # take regions with large enough areas
        if region.area >= 1000:
            
            # draw rectangle around segmented coins
            minr, minc, maxr, maxc = region.bbox
            
            buffPer = 0.05
            bufferC = int(buffPer*(maxc-minc))
            bufferR = int(buffPer*(maxr-minr))
            
            minr = minr + bufferR
            maxr = maxr - bufferR
            minc = minc + bufferC
            maxc = maxc - bufferC
            
            ImgROI = imgOrg[minr:maxr,minc:maxc] 
            
            ImgList.append(ImgROI)
 
    if len(ImgList) > 1:
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(image_label_overlay)
        for region in regionprops(label_image):
            # take regions with large enough areas
            if region.area >= 1000:                
                # draw rectangle around segmented coins
                minr, minc, maxr, maxc = region.bbox
                
                buffPer = 0.05
                bufferC = int(buffPer*(maxc-minc))
                bufferR = int(buffPer*(maxr-minr))
                
                minr = minr + bufferR
                maxr = maxr - bufferR
                minc = minc + bufferC
                maxc = maxc - bufferC
        
                rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                          fill=False, edgecolor='red', linewidth=2)
                ax.add_patch(rect)
                
                ax.text(minc+(maxc-minc)/2, minr+(maxr-minr)/2, str(ImgNum), color='black', fontsize=45)
                ImgNum += 1
        
        ax.set_axis_off()
        plt.tight_layout()
        plt.show()
        
        ImgChoice = eval(input('Enter Image Number to Return: '))
        
    else: ImgChoice = 0

    return ImgList[ImgChoice]

def WaterShed(img, WindSize, SauvolaK, FootPrint):

    window_size = WindSize
    sauvola = threshold_sauvola(img, window_size=window_size,k=SauvolaK)
    image = img < sauvola
    
    # Now we want to separate the two objects in image
    # Generate the markers as local maxima of the distance
    # to the background
    distance = ndi.distance_transform_edt(image)
    local_maxi = peak_local_max(
    distance, indices=False, footprint=np.ones((FootPrint,FootPrint)), labels=image)
    markers = measure.label(local_maxi)
    labels_ws = watershed(-distance, markers, mask=image)
    return labels_ws
    
def SizeAnalysis(labels_ws, h, w, scale):    
    # compute region properties
    props = regionprops(labels_ws)
    # get the sizes for each of the remaining objects and store in dataframe
    entries = []
    for p in props:
        entry = [p['centroid'][0], p['centroid'][1], p['area'], 
                 p['equivalent_diameter'], p['major_axis_length'],
                 p['minor_axis_length']]
        entries.append(entry)
    
    df = pd.DataFrame(entries, columns= ['ColX','RowY','Area_pix', 
                                          'EquivCircDia', 'MaxEllDist', 'MinEllDist'])
    df = df[df['Area_pix'] > 5]
    
    df['Dia_pix'] = 2 * np.sqrt(df['Area_pix']/3.14)
    df['Dia_um'] = df['Dia_pix']*scale
    
    df['AvgEllDia'] = scale*(df['MaxEllDist']+df['MinEllDist'])/2
    
    df['EdgeTest'] = (df['MaxEllDist']+df['MinEllDist'])/2
    MaxPixDia = df['EdgeTest'].max()
    
    rowFilter1 = df['ColX'] > 1.1 * MaxPixDia #allow for 110% of max Diameter
    rowFilter2 = df['ColX'] < h - 1.1 * MaxPixDia
    colFilter1 = df['RowY'] > 1.1 * MaxPixDia
    colFilter2 = df['RowY'] < w - 1.1 * MaxPixDia
    
    df = df[rowFilter1 & rowFilter2 & colFilter1 & colFilter2]
    '''
    Spread Factor Parameters
    DrpDia = DiaStain /(a * DiaStain^2 + b * DiaStain + c)
    '''
    a = 0
    b = 0.0009
    c = 1.63
    
    df['DrpDia'] = df['AvgEllDia']/(a*df['AvgEllDia']**2 + b*df['AvgEllDia'] + c)
    df['DrpVol'] = (4/3 * 3.14 * (df['DrpDia']/2)**3)/1e9
    
    return df
    
def SummaryStats(df, area):
    '''Compute Droplet Size Distribution from Data'''
   
    binz = np.linspace(df['DrpDia'].min(),df['DrpDia'].max(),200)
 
    QuantData, bins = pd.cut(df['DrpDia'], binz, right=False, retbins=True)
    
    BinData = df.groupby(QuantData)['DrpDia'].agg(['count'])
    BinData['Bins'] = BinData.index
    
    BinData['BinCent'] = BinData['Bins'].apply(lambda x: x.mid)
    BinData = BinData.reset_index()
    
    MidBins = pd.DataFrame(columns=['MidBin'])
    
    for i in range(0,len(bins)-1):
        MidPoint = (binz[i]+binz[i+1])/2
        BinCurrent = pd.DataFrame({'MidBin':[MidPoint]})
        MidBins = MidBins.append(BinCurrent, ignore_index = True)
        
    BinData = BinData.join(MidBins)
    
    BinData['TotVolBin'] = (BinData['count']*(4/3)*3.14*(BinData['MidBin']/2)**3)/1e9
    BinData['FracVol'] = BinData['TotVolBin']/BinData['TotVolBin'].sum()
    BinData['CumVolFrac'] = BinData['FracVol'].cumsum()
    
    NumDrops = BinData['count'].sum()
    # 10.6907 gpa = 1 ul/cm^2
    VolperArea = (BinData['TotVolBin'].sum()/area)*10.6907

    
    DV10 = LinearExtrapolateVolDia(BinData,0.1)
    DV50 = LinearExtrapolateVolDia(BinData,0.5)
    DV90 = LinearExtrapolateVolDia(BinData,0.9)
    
    return(DV10, DV50, DV90, VolperArea, NumDrops)

# Gerenate list of all *.bmp files

ImgFiles = []

WSPdata = pd.DataFrame(columns = ['Card', 'DV10', 'DV50', 'DV90', 'GPA', 'NumDrops'])

WindowSize = 45
Sauvola_K = 0.13
FootPrint = 7

knownWidth = 25400
scale=42.333 #pixels per um
#Area imaged 

FileList = []

os.chdir(".")
for fileN in glob.glob("*.bmp"):
    
    FileList.append(fileN)
    
if len(FileList) > 1:
    
    Choice = input('All cards Enter A or Single Card Enter S: ')
    
    if Choice == 'S':
        
        spot = input('Enter file number to process: ')
        ind = int(spot)-1
        file = FileList[ind]
        CardNum = float(file.translate({ord(i): None for i in 'Scan.bmp'}))
        # Read Image as greyscale
        imgOrg = img_as_ubyte(rgb2gray(io.imread(file)))
        # #imgOrg = img_as_ubyte(rgb2gray(io.imread('BradTest.bmp')))
        
        ImgROI = CropROI(imgOrg)
        h,w = ImgROI.shape
        AreaImg = (scale*h)*(scale*w)/1e8
        
        WS_Labels = WaterShed(ImgROI, WindowSize, Sauvola_K, FootPrint)
        DF = SizeAnalysis(WS_Labels, h, w, scale)
        DV10, DV50, DV90, GPA, NumDrps = SummaryStats(DF,AreaImg)
        
        fig, axes = plt.subplots(1, 1, figsize=(30, 30), constrained_layout=True)
        ax1 = axes
        ax1.imshow(ImgROI,cmap='Greys', interpolation='nearest')
        
        for index, row in DF.iterrows():
        
            radius = row['AvgEllDia']/(2*42.333)
            rowY = row['RowY']
            colX = row['ColX']
            circ = Circle( (rowY,colX) ,radius, fill=False, edgecolor='red',linewidth=2)
            ax1.add_patch(circ)
            
        ax1.text(w/5, h/2.25, 'DV10 = ' +str(round(DV10,0)), fontsize=75, color = 'white')
        ax1.text(w/5, h/2, 'DV50 = ' +str(round(DV50,0)), fontsize=75, color = 'white')
        ax1.text(w/5, h/1.75, 'DV90 = ' +str(round(DV90,0)), fontsize=75, color = 'white')
        ax1.text(w/8, h/1.55, 'NumDrops = ' +str(round(NumDrps,0)), fontsize=75, color = 'white')
        
        ax1.set_axis_off()
        
        plt.show()
    
    else:
        for file in FileList:

            CardNum = float(file.translate({ord(i): None for i in 'Scan.bmp'}))
            print(file)
            #Read Image as greyscale
            imgOrg = img_as_ubyte(rgb2gray(io.imread(file)))
            #imgOrg = img_as_ubyte(rgb2gray(io.imread('BradTest.bmp')))
            
            ImgROI = CropROI(imgOrg)
            h,w = ImgROI.shape
            AreaImg = (scale*h)*(scale*w)/1e8
            
            
            WS_Labels = WaterShed(ImgROI, WindowSize, Sauvola_K, FootPrint)
            DF = SizeAnalysis(WS_Labels, h, w, scale)
            DV10, DV50, DV90, GPA, NumDrps = SummaryStats(DF,AreaImg)
            
            dfNew = pd.DataFrame({'Card':[file], 'CardNum':[CardNum], 'DV10':[DV10], 'DV50':[DV50],
                                  'DV90':[DV90], 'GPA':[GPA], 'NumDrops':[NumDrps]})
        
            WSPdata = WSPdata.append(dfNew, ignore_index=True)

WSPdata.to_pickle('3 Feet WSP Data.pkl')


Plot = input('Plot Data? Y or N: ')

if Plot == 'Y':
    fig, axes = plt.subplots(1, 1, figsize=(30, 30), constrained_layout=True)
    ax1 = axes
    ax1.imshow(ImgROI,cmap='Greys', interpolation='nearest')
    
    for index, row in DF.iterrows():
    
        radius = row['AvgEllDia']/(2*42.333)
        rowY = row['RowY']
        colX = row['ColX']
        circ = Circle( (rowY,colX) ,radius, fill=False, edgecolor='red',linewidth=2)
        ax1.add_patch(circ)
        
    ax1.text(w/5, h/2.25, 'DV10 = ' +str(round(DV10,0)), fontsize=75, color = 'white')
    ax1.text(w/5, h/2, 'DV50 = ' +str(round(DV50,0)), fontsize=75, color = 'white')
    ax1.text(w/5, h/1.75, 'DV90 = ' +str(round(DV90,0)), fontsize=75, color = 'white')
    ax1.text(w/8, h/1.55, 'NumDrops = ' +str(round(NumDrps,0)), fontsize=75, color = 'white')
    
    ax1.set_axis_off()
    
    plt.show()


  