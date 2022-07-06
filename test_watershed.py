import cv2
import time

testfile = "/Users/gill14/Library/Mobile Documents/com~apple~CloudDocs/Projects/AccuPatt/testing/N802EX 01.db"
from accupatt.helpers.dBBridge import load_from_db
from accupatt.models.seriesData import SeriesData
from accupatt.models.sprayCard import SprayCard, SprayCardImageProcessor, SprayCardStats
s = SeriesData()
load_from_db(testfile, s)
sc = s.passes[-1].cards.card_list[6]
sc.watershed = True

scip = SprayCardImageProcessor(sprayCard=sc)

# Plot
#figure(figsize=(8, 6), dpi=1200)
#plt.imshow(scip.get_source_mask())
#plt.show()

pre = time.perf_counter()
cv2.imshow("old",scip.draw_and_log_stains()[0])
post = time.perf_counter()
print(f"old in {post-pre:.4f} sec")
pre = time.perf_counter()
scip.process_stains()
cv2.imshow("new",scip.get_source_mask())
post = time.perf_counter()
print(f"new in {post-pre:.4f} sec")
#waits for user to press any key 
#(this is necessary to avoid Python kernel form crashing)
cv2.waitKey(0) 
  
#closing all open windows 
cv2.destroyAllWindows() 