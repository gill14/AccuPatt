import copy
import cv2
import time
import matplotlib.pyplot as plt

testfile = "/Users/gill14/Library/Mobile Documents/com~apple~CloudDocs/Projects/AccuPatt/testing/N802EX 01.db"
from accupatt.helpers.dBBridge import load_from_db
from accupatt.models.seriesData import SeriesData
from accupatt.models.sprayCard import SprayCard, SprayCardImageProcessor, SprayCardStats
import accupatt.config as cfg
s = SeriesData()
load_from_db(testfile, s)
sc = s.passes[-1].cards.card_list[4]
sc.watershed = True
sc.stain_approximation_method = cfg.STAIN_APPROXIMATION_CONVEX_HULL



# Plot
#figure(figsize=(8, 6), dpi=1200)
#plt.imshow(scip.get_source_mask())
#plt.show()

sc2 = copy.copy(sc)

pre = time.perf_counter()
scip2 = SprayCardImageProcessor(sprayCard=sc2)
scip2.process_stains()
#cv2.imshow("new",scip2.get_overlay_image())
#plt.imshow(cv2.cvtColor(scip2.get_overlay_image(), cv2.COLOR_BGR2RGB))
plt.subplot(1,2,1)
plt.imshow(scip2.get_overlay_image())
plt.subplot(1,2,2)
plt.imshow(scip2.get_mask_image())
post = time.perf_counter()
print(f"new in {post-pre:.4f} sec")
print(f"Total Stain Count = {len(sc2.stains)}")
print(f"Valid Stain Count = {len([s for s in sc2.stains if s['is_include']])}")
#waits for user to press any key 
#(this is necessary to avoid Python kernel form crashing)
#cv2.waitKey(0) 
plt.show()
#closing all open windows 
#cv2.destroyAllWindows() 