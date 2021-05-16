import pandas as pd
import numpy as np

class DataAccuPatt:

    def __init__(self, inputFile):
        self.dataFile = inputFile

    def readFromFile(self):
        """self.flyinData = pd.read_excel (self.dataFile, sheet_name='Fly-In Data', header=None, dtype=str)
        self.flyinData = self.flyinData.fillna('')
        self.aircraftData = pd.read_excel (self.dataFile, sheet_name='Aircraft Data', header=None, dtype=str)
        self.aircraftData = self.aircraftData.fillna('')
        self.seriesData = pd.read_excel (self.dataFile, sheet_name='Series Data')
        self.seriesData = self.seriesData.fillna('')
        self.patternData = pd.read_excel (self.dataFile, sheet_name='Pattern Data', header=None)"""
        #self.df3 = self.df3.replace('nan','')

        #Load entire WB into dict of sheets
        self.df_map = pd.read_excel(self.dataFile, sheet_name=None, header=None)
        #Assign reference dfs to each sheet
        self.flyinData = self.df_map['Fly-In Data']
        self.flyinData = self.flyinData.fillna('')
        self.aircraftData = self.df_map['Aircraft Data']
        self.aircraftData = self.aircraftData.fillna('')
        self.seriesData = self.df_map['Series Data']
        self.seriesData = self.seriesData.fillna('')
        self.patternData = self.df_map['Pattern Data']

    def getFlyinData(self):
        return self.flyinData

    def getAircraftData(self):
        #Need to masage this into a cohesive df before returning
        d = self.aircraftData.iloc[0:6,[0,1]]
        d = d.append({0:'ZIP', 1:self.aircraftData.iloc[5,2]}, ignore_index=True)
        d = d.append({0:'Email', 1:self.aircraftData.iloc[0,2]}, ignore_index=True)
        d = d.append(self.aircraftData.iloc[6:21, [0,1]], ignore_index=True)
        d = d.append({0:'Printed Swath', 1:self.aircraftData.iloc[20,2]}, ignore_index=True)
        d = d.append(self.aircraftData.iloc[26:34, [0,1]], ignore_index=True)
        d = d.append(self.aircraftData.iloc[35:36, [0,1]], ignore_index=True)
        d.columns = ['Label', 'Value']
        d = d.astype({'Value':str})
        #print(d)
        #d['Value'] = d['Value'].apply(str)
        return d

    def getSeriesData(self):
        header = self.seriesData.iloc[0]
        d = self.seriesData[1:]
        d.columns = header
        return d

    def getPatternInfo(self):
        d = pd.DataFrame({'Pass 1':[], 'Pass 2':[], 'Pass 3':[], 'Pass 4':[], 'Pass 5':[], 'Pass 6':[]})
        dd = self.patternData.iloc[0:3,[2, 4, 6, 8, 10, 12]]
        dd.columns = ['Pass 1', 'Pass 2', 'Pass 3', 'Pass 4', 'Pass 5', 'Pass 6']
        d = d.append(dd, ignore_index=True)
        dd = self.patternData.iloc[1:2,[1, 3, 5, 7, 9, 11]]
        dd.columns = ['Pass 1', 'Pass 2', 'Pass 3', 'Pass 4', 'Pass 5', 'Pass 6']
        #dd = dd.mask(np.NaN, 0)
        #dd = dd.mask(dd > 0, 1)
        #dd = dd.replace(to_replace=np.NaN,value=False)
        #dd.where(dd!=False, True, inplace=True)
        d = d.append(dd, ignore_index=True)
        #d.insert(0, 'Mod', ['TrimL','TrimR','TrimV'], True)

        return d

    def getPatternData(self):
        d = pd.DataFrame({'loc':[], 'Pass 1':[], 'Pass 2':[], 'Pass 3':[], 'Pass 4':[], 'Pass 5':[], 'Pass 6':[]})
        dd = self.patternData.iloc[5:,[0,2,4,6,8,10,12]]
        dd.columns = ['loc', 'Pass 1', 'Pass 2', 'Pass 3', 'Pass 4', 'Pass 5', 'Pass 6']
        d = d.append(dd, ignore_index=True)
        return d

    def getExcitationData(self):
        d = pd.DataFrame({'loc':[], 'Pass 1':[], 'Pass 2':[], 'Pass 3':[], 'Pass 4':[], 'Pass 5':[], 'Pass 6':[]})
        dd = self.patternData.iloc[5:,[0,1,3,5,7,9,11]]
        dd.columns = ['loc', 'Pass 1', 'Pass 2', 'Pass 3', 'Pass 4', 'Pass 5', 'Pass 6']
        d = d.append(dd, ignore_index=True)
        return d
