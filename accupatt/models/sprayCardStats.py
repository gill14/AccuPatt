import math

from accupatt.models.sprayCardSpreadFactors import SprayCardSpreadFactors


class SprayCardStats:

    UM_PER_IN = 25400.0

    def __init__(self, dpi):
        self.area_px2 = 0.0
        self.stain_areas_all_px2 = []
        self.stain_areas_valid_px2 = []
        self.dpi = dpi
        self.sf = SprayCardSpreadFactors()

    def percent_coverage(self):
        if len(self.stain_areas_all_px2) == 0:
            return 0
        stain_area_px2_sum = 0
        for area in self.stain_areas_all_px2:
            stain_area_px2_sum += area
        cov = stain_area_px2_sum / self.area_px2
        return cov*100.0

    def stains_per_in2(self):
        return round(len(self.stain_areas_all_px2) / self._px2_to_in2(self.area_px2)) 

    def volumetric_stats(self):
        drop_dia_um = []
        drop_vol_um3 = []
        drop_vol_um3_sum = 0.0
        for area in self.stain_areas_valid_px2:
            area_um2 = self._px2_to_um2(area)
            dia_um = math.sqrt((4.0 * area_um2) / math.pi)
            drop_dia_um.append(self.sf.stain_dia_to_drop_dia(dia_um))
            vol_um3 = (math.pi * dia_um**3) / 6.0
            drop_vol_um3.append(vol_um3)
            drop_vol_um3_sum += vol_um3
        drop_dia_um.sort()
        drop_vol_um3.sort()
        dv01 = 0
        dv01_vol = 0.10 * drop_vol_um3_sum
        dv01_found = False
        dv05 = 0
        dv05_vol = 0.50 * drop_vol_um3_sum
        dv05_found = False
        dv09 = 0
        dv09_vol = 0.90 * drop_vol_um3_sum
        dv09_found = False
        cumVol = []
        for i in range(0,len(drop_dia_um)-1):
            if i == 0: cumVol.append(drop_vol_um3[i])
            else: cumVol.append(drop_vol_um3[i]+cumVol[i-1])
            if not dv01_found and cumVol[i] >= dv01_vol:
                dv01_found = True
                dv01 = drop_dia_um[i]
                if i>0:
                    dv01 = drop_dia_um[i-1] + (dv01_vol - cumVol[i-1]) * ((drop_dia_um[i] - drop_dia_um[i-1]) / (cumVol[i] - cumVol[i-1]))
            if not dv05_found and cumVol[i] >= dv05_vol:
                dv05_found = True
                dv05 = drop_dia_um[i]
                if i>0:
                    dv05 = drop_dia_um[i-1] + (dv05_vol - cumVol[i-1]) * ((drop_dia_um[i] - drop_dia_um[i-1]) / (cumVol[i] - cumVol[i-1]))
            if not dv09_found and (cumVol[i] >= dv09_vol or i==len(drop_dia_um)-1):
                dv09_found = True
                dv09 = drop_dia_um[i]
                if i>0:
                    dv09 = drop_dia_um[i-1] + (dv09_vol - cumVol[i-1]) * ((drop_dia_um[i] - drop_dia_um[i-1]) / (cumVol[i] - cumVol[i-1]))
        rs = (dv09 - dv01) / dv05

        return round(dv01), round(dv05), round(dv09), rs
        


    def _px2_to_um2(self, area_px2):
        um_per_px = self.UM_PER_IN / self.dpi
        return area_px2 * um_per_px * um_per_px
    
    def _px2_to_in2(self, area_px2):
        return area_px2 / (self.dpi * self.dpi)


    