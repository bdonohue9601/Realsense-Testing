from __future__ import print_function
from imutils import perspective
from imutils import contours
import numpy as np
import imutils
import cv2
from scipy.spatial import distance as dist
from imutils.video import VideoStream
import time
import pyrealsense2 as rs



'''
The next two definitions (Provided by pyimagesearch.com) are used later.
'''

def order_points(pts):
    # sort the points based on their x-coordinates
    xSorted = pts[np.argsort(pts[:, 0]), :]
    
    # grab the left-most and right-most points from the sorted
    # x-roodinate points
    leftMost = xSorted[:2, :]
    rightMost = xSorted[2:, :]
    
    # now, sort the left-most coordinates according to their
    # y-coordinates so we can grab the top-left and bottom-left
    # points, respectively
    leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
    (tl, bl) = leftMost
 
    # now that we have the top-left coordinate, use it as an
    # anchor to calculate the Euclidean distance between the
    # top-left and right-most points; by the Pythagorean
    # theorem, the point with the largest distance will be
    # our bottom-right point
    D = dist.cdist(tl[np.newaxis], rightMost, "euclidean")[0]
    (br, tr) = rightMost[np.argsort(D)[::-1], :]
 
    # return the coordinates in top-left, top-right,
    # bottom-right, and bottom-left order
    return np.array([tl, tr, br, bl], dtype="float32")

#Return midpoints
def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)

def get_dimensions():

    #Read the left and write images
    imageL = cv2.imread('/home/pi/Picture.jpg')
    #imageL = imageL[0:450]
    #imageL = cv2.convertScaleAbs(imageL, alpha=2, beta=0)
    grayL = cv2.cvtColor(imageL, cv2.COLOR_BGR2GRAY)
    grayL = cv2.GaussianBlur(grayL, (7, 7), 0)
    # perform edge detection, then perform a dilation + erosion to
    # close gaps in between object edges
    edgedL = cv2.Canny(grayL, 50, 100)
    edgedL = cv2.dilate(edgedL, None, iterations=1)
    edgedL = cv2.erode(edgedL, None, iterations=1)
##    cv2.imshow("Edged", edgedL)
##    cv2.waitKey(0)

    # find contours in the edge map
    cntsL = cv2.findContours(edgedL.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_NONE)
    cntsL = imutils.grab_contours(cntsL)

    # sort the contours from left-to-right and initialize the
    # 'pixels per metric' calibration variable
    (cntsL, _) = contours.sort_contours(cntsL)

    pixelsPerMetric = None
    # loop over the contours individually
    c = max(cntsL, key=cv2.contourArea)
    
    leftmost = tuple(c[c[:,:,0].argmin()][0])
    rightmost = tuple(c[c[:,:,0].argmax()][0])
    topmost = tuple(c[c[:,:,1].argmin()][0])
    bottommost = tuple(c[c[:,:,1].argmax()][0])
    extremes = leftmost, rightmost, topmost, bottommost


    areaL=0
    for c in cntsL:
        # if the contour is not sufficiently large, ignore it
        if cv2.contourArea(c) < 100:
            continue
        if areaL < cv2.contourArea(c):
            areaL = cv2.contourArea(c)
        else:
            continue
        # compute the rotated bounding box of the contour
        orig = imageL.copy()
        box = cv2.minAreaRect(c)
    #print(box)
    #cv2.circle(orig, leftmost, 1, (0, 0, 255), -1)
    #cv2.circle(orig, rightmost, 1, (0, 255, 0), -1)
    #cv2.circle(orig, topmost, 1, (255, 0, 0), -1)
    #cv2.circle(orig, bottommost, 1, (255, 255, 0), -1)        
##    box = 0
    box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
    box = np.array(box, dtype="int")
    #print(box)
    # order the points in the contour such that they appear
    # in top-left, top-right, bottom-right, and bottom-left
    # order, then draw the outline of the rotated bounding
    # box
    box = perspective.order_points(box)
    #cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)
    #print([box.astype("int")])
    # loop over the original points and draw them
##    for (x, y) in box:
##        cv2.circle(orig, (int(x), int(y)), 3, (0, 0, 255), -1)


    # unpack the ordered bounding box, then compute the midpoint
    # between the top-left and top-right coordinates, followed by
    # the midpoint between bottom-left and bottom-right coordinates
    (tl, tr, br, bl) = box
    cv2.circle(orig, tuple(tl), 5, (0, 0, 255), -1)
    cv2.circle(orig, tuple(tr), 5, (0, 0, 255), -1)
    cv2.circle(orig, tuple(br), 5, (0, 0, 255), -1)
    cv2.circle(orig, tuple(bl), 5, (0, 0, 255), -1)        

    
    #print(tl, tr, br, bl)
    (tltrX, tltrY) = midpoint(tl, tr)
    (blbrX, blbrY) = midpoint(bl, br)

    # compute the midpoint between the top-left and top-right points,
    # followed by the midpoint between the top-righ and bottom-right
    (tlblX, tlblY) = midpoint(tl, bl)
    (trbrX, trbrY) = midpoint(tr, br)

    # draw the midpoints on the image
    cv2.circle(orig, (int(tltrX), int(tltrY)), 1, (255, 0, 0), -1)
    cv2.circle(orig, (int(blbrX), int(blbrY)), 1, (255, 0, 0), -1)
    cv2.circle(orig, (int(tlblX), int(tlblY)), 1, (255, 0, 0), -1)
    cv2.circle(orig, (int(trbrX), int(trbrY)), 1, (255, 0, 0), -1)

    # draw lines between the midpoints
    cv2.line(orig, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)),
        (255, 0, 255), 2)
    cv2.line(orig, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)),
         (255, 0, 255), 2)
##    #points_on_line = np.linspace((tltrX, tltrY), (blbrX, blbrY), int(dist.euclidean((tltrX, tltrY), (blbrX, blbrY))))
##    points_on_line = np.linspace((tltrX, tltrY), (blbrX, blbrY), 100, dtype = int)
##    print(points_on_line)
    # compute the Euclidean distance between the midpoints
    dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
    dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))
    #print(dA, dB)
    cv2.imwrite('DisplayPic.jpg', orig)
##    cv2.imshow("Image", orig)
##    cv2.waitKey(0)
    #cv2.destroyAllWindows()
    return box, c, (tltrX, tltrY), (blbrX, blbrY), (tlblX, tlblY), (trbrX, trbrY), extremes

