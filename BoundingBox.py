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
    imageL = cv2.imread('/home/hp/Documents/Dimensions_testing/Picture.jpg')
    #imageL = imageL[0:450]
    #imageL = cv2.convertScaleAbs(imageL, alpha=2, beta=0)
    grayL = cv2.cvtColor(imageL, cv2.COLOR_BGR2GRAY)
    grayL = cv2.GaussianBlur(grayL, (7, 7), 0)
    # perform edge detection, then perform a dilation + erosion to
    # close gaps in between object edges
    edgedL = cv2.Canny(grayL, 50, 100)
    edgedL = cv2.dilate(edgedL, None, iterations=1)
    edgedL = cv2.erode(edgedL, None, iterations=1)
    cv2.imshow("Edged", edgedL)
    cv2.waitKey(0)

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
    
##    print(c.shape)
##    print(c)
##    for cord in c:
##        print(cord[:,0])
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
    cv2.circle(orig, leftmost, 1, (0, 0, 255), -1)
    cv2.circle(orig, rightmost, 1, (0, 255, 0), -1)
    cv2.circle(orig, topmost, 1, (255, 0, 0), -1)
    cv2.circle(orig, bottommost, 1, (255, 255, 0), -1)        
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
    print(cv2.line(orig, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)),
        (255, 0, 255), 2).shape)
    cv2.line(orig, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)),
         (255, 0, 255), 2)
##    #points_on_line = np.linspace((tltrX, tltrY), (blbrX, blbrY), int(dist.euclidean((tltrX, tltrY), (blbrX, blbrY))))
##    points_on_line = np.linspace((tltrX, tltrY), (blbrX, blbrY), 100, dtype = int)
##    print(points_on_line)
    # compute the Euclidean distance between the midpoints
    dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
    dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))
    print(dA, dB)
    cv2.imwrite('DisplayPic.jpg', orig)
    cv2.imshow("Image", orig)
    cv2.waitKey(0)
    #cv2.destroyAllWindows()
    return box, c, (tltrX, tltrY), (blbrX, blbrY), (tlblX, tlblY), (trbrX, trbrY), extremes
##
## # Configure depth and color streams
##pipeline = rs.pipeline()
##config = rs.config()
##config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
##config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
##
### Start streaming
##pipeline.start(config)
##
##try:
##    while True:
##
##        # Wait for a coherent pair of frames: depth and color
##        frames = pipeline.wait_for_frames()
##        depth_frame = frames.get_depth_frame()
##        #print(depth_frame.get_distance(300,300))
##        color_frame = frames.get_color_frame()
##        if not depth_frame or not color_frame:
##            continue
##        
##        # Convert images to numpy arrays
##        depth_image = np.asanyarray(depth_frame.get_data())
##        color_image = np.asanyarray(color_frame.get_data())
##        #depth_value = np.asanyarray(depth_frame.get_distance())
##        #print(depth_image)
##        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
##        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
##
##        # Stack both images horizontally
##        images = np.vstack((color_image, depth_colormap))
##
##        # Show images
##        #x+=x
##        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
##        cv2.imshow('RealSense', images)
##        if cv2.waitKey(1) & 0xFF == ord('c'):
##            cv2.imwrite('Picture.jpg', color_image)
##            break
##        
##    array_points, c, top, bottom, left, right = get_dimensions()
####    print(array_points)
##
##    for cord in c:
##        print(cord, depth_frame.get_distance(cord[:,0],cord[:,1]))
##    zero_array = []
##    object_array = []
##    xmax = int(np.max(array_points[:, 0]))
##    xmin = int(np.min(array_points[:, 0]))
##    ymax = int(np.max(array_points[:, 1]))
##    ymin = int(np.min(array_points[:, 1]))
##    cv2.circle(color_image, (int(xmin), int(ymin)), 5, (255, 0, 0), -1)
##    cv2.circle(color_image, (int(xmin), int(ymax)), 5, (255, 0, 0), -1)
##    cv2.circle(color_image, (int(xmax), int(ymin)), 5, (255, 0, 0), -1)
##    cv2.circle(color_image, (int(xmax), int(ymax)), 5, (255, 0, 0), -1)
##    array = np.zeros(depth_image.shape)
##    for x in range(xmin-30, xmax+30):
##        for y in range(ymin-30, ymax+30):
##            array[y][x] = round(depth_frame.get_distance(x,y), 3)
##            if (x < xmin or x > xmax) and (y < ymin or y > ymax):
##                zero_array.append(round(depth_frame.get_distance(x,y), 3))
##            if (x > xmin and x < xmax) and (y > ymin and y < ymax):
##                object_array.append((round(depth_frame.get_distance(x,y), 3), x, y))
##    np.array(zero_array)
##    object_array = np.array(object_array)
##    object_array = object_array[object_array[:,0] >0]
##    #print(object_array)
####    print(np.mean(zero_array))
####    print(np.min(object_array[:,0]))
####    print("height: ", (np.mean(zero_array)-np.min(object_array[:, 0]))*1000)
####    for x in range(depth_image.shape[1]):
####        for y in range(depth_image.shape[0]):
####            array[y][x] = round(depth_frame.get_distance(x,y), 3)
##
####            if array[y][x] < .6 and array[y][x] > 0:
####                array2[y][x] = array[y][x]
##
####    new_array = depth_image[ymin:ymax,xmin:xmax]
##    cord = list(zip(np.where(object_array == np.min(object_array[:, 0]))))
####    print(cord)
##    for val in cord[0][0]:
####        print(val)
##        xcord = object_array[val][1]
##        ycord = object_array[val][2]
####        print(xcord, ycord)
##        cv2.circle(color_image, (int(xcord), int(ycord)), 1, (0, 0, 255), -1)
##    #cv2.circle(orig, (int(tltrX), int(tltrY)), 5, (255, 0, 0), -1)
##    cv2.imshow("color", color_image)
##    cv2.waitKey(0)
##    new_array = color_image[ymin:ymax,xmin:xmax]
##    array2 = array[ymin:ymax,xmin:xmax]
##    #print(array)
##    #np.savetxt('BoundingBoxHeight.txt', array2, fmt='%1.3f')
##    #print(new_array.shape)
##    
##    cv2.imshow("spliced", new_array)
##    cv2.waitKey(0)
##finally:
##    pipeline.stop()
##    cv2.destroyAllWindows()


