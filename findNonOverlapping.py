'''
This script finds isolated metaphase chromosonmes and creates a freehand line ROI
along the length of the chromosome.

Input: a monochrome DAPI stained image that includes metaphase chromosomes.

Output: A set of freehand line ROIs in the ROI Manager.

To Do: 	1. Convert many of the statis IJ.run calls to calls to the API methods. 
		2. Replace magic numbers with more robust derived paremeters. 

Author:			Aryeh Weiss
Last modified:	15 Sept 22

'''

from ij import IJ , Prefs
from ij.measure import ResultsTable 
from ij.gui import PolygonRoi, WaitForUserDialog
from java.awt import Polygon
from java.awt import Point
from  ij.plugin.frame import RoiManager 
import sys

# The Utils.py file must be on the Fiji search path.  
from Utils import *

def addPoints(p1, p2):
	return Point(p1.x+p2.x, p1.y+p2.y)

DEBUG = True # I should change this to a script parameter 

MIN_VALID_LINE = 20 # minimum valid line length 

# The following calls require my Utils.py file.
close_non_image_windows()
close_image_windows()
# inputImp = IJ.getImage()
inputImp, inputPrefix, inputDirPath  = open_image()
inputImp.show()


imp = inputImp.duplicate()
ip = imp.getProcessor()
IJ.run(imp, "Gaussian Blur...", "sigma=2")
imp.show()
IJ.setAutoThreshold(imp, "Default dark")
IJ.run(imp, "Convert to Mask", "")
IJ.run(imp, "Skeletonize", "")

# The skeleton is not a binary image, so I convert it to a binary image.
IJ.setRawThreshold(imp, 255, 255)
Prefs.blackBackground = True
IJ.run(imp, "Convert to Mask", "")

# I am not sure if this would be better placed before the last "Convert to Mask" 
# But this  works.
IJ.run(imp, "Analyze Skeleton (2D/3D)", "prune=none  show")

# Analyze skeleton produces two tables. 
# One is called "Results" and one is called "Branch information"
rt_branch =  ResultsTable.getResultsTable("Branch information")
if rt_branch == None:
	sys.exit("Branch results table not found")
	
rt =  ResultsTable.getResultsTable("Results")
if rt == None:
	sys.exit("Skeletons results table not found")

# find valid skeletons. 
# a valid skeleton has exactly one branch and is at least 20 pixels in length
numSkel = rt.getCounter() 
validSkel = []
for i in range(numSkel): 
	nBranch = rt.getValue("# Branches", i)
	avgBranchLen = rt.getValue("Average Branch Length", i)
	if int(nBranch) == 1 and avgBranchLen >= MIN_VALID_LINE:
		validSkel.append(i+1)

if DEBUG:
	print validSkel 

# create a list of end points of valid skeletons
# the V1 endpoint is used (there is also an unused V2 endpoint).
validSkelEnds = []
numBranches = rt_branch.getCounter()
for i in range(numBranches):
	if rt_branch.getValue("Skeleton ID",i) in validSkel:
		v1_x = rt_branch.getValue("V1 x", i)
		v1_y = rt_branch.getValue("V1 y", i)
		validSkelEnds.append(Point(int(v1_x), int(v1_y)))

if DEBUG:
	for i in validSkelEnds:
		print i

# set of 8 nearest neighbors to search for next point in the line. 
deltaPoint = [Point(-1,-1), Point(-1,0), Point(-1,1), Point(0,1), Point(0,-1), Point(1,-1), Point(1,0), Point(1,1)]

if DEBUG:
	print deltaPoint 
	
rm = RoiManager.getInstance()
if rm == None:
	rm = RoiManager()
	
# create line ROI for each valid skeleton
for i in validSkelEnds:
	count=0
	linePoints = []
	linePoints.append(i)
	currentPoint = i 
	lastPoint = addPoints(i, Point(-4,-4))
# look for a non-zero neighbor that is not already in the line
# when no such neighbor is found then the line is complete
	while True:
		for j in deltaPoint: 
			newPoint = addPoints(currentPoint, j)
			if DEBUG:
				print j, newPoint , ip.getPixel(newPoint.x, newPoint.y)
			if ip.getPixel(newPoint.x, newPoint.y) == 255 and newPoint != lastPoint :
				lastPoint = currentPoint
				currentPoint = newPoint
				linePoints.append(currentPoint)
				break
# The loop will exit if it runs more than 500 times. This magic number should be replaced
# with something more sensible, like the maximum valid chromosome length or a value based
# on the dimensions of the image. 
		count +=1
		if currentPoint == linePoints[-1] or  count==500:
			break
	
	if DEBUG:
		print len(linePoints), linePoints[-1] 

# create the freehand line ROI
	poly = Polygon()
	for p in linePoints:
		poly.addPoint(int(p.x), int(p.y)) 

	pRoi  = PolygonRoi(poly, PolygonRoi.POLYLINE)

# add the polyline to the ROI manager.
	rm.addRoi(pRoi)

