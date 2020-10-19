import pyrealsense2 as rs
import cv2
import numpy as np
from Point_Cloud import convert_depth_frame_to_pointcloud, convert_depth_pixel_to_metric_coordinate
import BoundingBox
from scipy.spatial import distance as dist
import math
import time

'''
------Set the resolution and frame rate-----
'''
#resolution_width = 1280 # pixels
#resolution_height = 720 # pixels
resolution_width = 640 # pixels
resolution_height = 480 # pixels
frame_rate = 30  # fps
dispose_frames_for_stablisation = 30  # frames

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, resolution_width, resolution_height, rs.format.z16, frame_rate)
config.enable_stream(rs.stream.infrared, 1, resolution_width, resolution_height, rs.format.y8, frame_rate)
config.enable_stream(rs.stream.color, resolution_width, resolution_height, rs.format.bgr8, frame_rate)

def get_Dimensions():

    '''
    Set the variables for the Max, Min, and Mean values that serve as the 'zeros'.
    '''
    zero = open("Zero_Length", 'r')
    zero_depth =zero.read()
    zero.close()
    zero_depth = float(zero_depth)

    zeroMax = open("Zero_Max", 'r')
    zero_max =zeroMax.read()
    zeroMax.close()
    zero_max = float(zero_max)

    zeroMin = open("Zero_Min", 'r')
    zero_min =zeroMin.read()
    zeroMin.close()
    zero_min = float(zero_min)
    
    '''
    Set timeout value
    '''
    timeout = time.time() + 1
    
    # Start streaming
    profile = pipeline.start(config)
    sensor = profile.get_device().first_depth_sensor()
    depth_stream=rs.video_stream_profile(profile.get_stream(rs.stream.depth))
    intrinsics = depth_stream.get_intrinsics()

    try:
        while True:

            # Wait for a coherent pair of frames: depth and color and align the frames
            frames = pipeline.wait_for_frames()
            align_to = rs.stream.color
            align = rs.align(align_to)
            aligned_frames = align.process(frames)
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            ir_frame = aligned_frames.get_infrared_frame()
            if not depth_frame or not color_frame:
                continue
            
            # Convert images to numpy arrays
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            new_image = np.asanyarray(ir_frame.get_data())
            
            # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

            if time.time() > timeout:
                cv2.imwrite('Picture.jpg', color_image)
                break

        #Call BoundingBox.py, return bounding box; contours; top, bottom, left and right midpoints; and extreme N,W,E,S values of countours
        bounding_box, c, top, bottom, left, right, extremes = BoundingBox.get_dimensions()

        #Create array of pixel values between the midpoints of bounding boxes
        points_on_lineL = np.linspace(top, bottom, int(dist.euclidean(top, bottom)), dtype = int)
        points_on_lineW = np.linspace(left, right, int(dist.euclidean(left, right)), dtype = int)

        '''
        Loop through each coordinate and set their metric_point_cloud values to a new array
        '''
        #Length
        metricL = []
        metricL = np.zeros([int(dist.euclidean(top, bottom)),3])

        i = 0 
        for points in points_on_lineL:
            metricL[i] = convert_depth_pixel_to_metric_coordinate(depth_frame.get_distance(points[0], points[1]), points[0], points[1], intrinsics)
            i+=1
        #Width
        metricW = []
        metricW = np.zeros([int(dist.euclidean(left, right)),3])

        j = 0 
        for points in points_on_lineW:
            metricW[j] = convert_depth_pixel_to_metric_coordinate(depth_frame.get_distance(points[0], points[1]), points[0], points[1], intrinsics)
            j+=1

        #Remove all 0 values, convert into a numpy array
        metricL = [ii for ii in metricL if all(ii)]
        metricW = [iii for iii in metricW if all(iii)]
        metricL = np.asanyarray(metricL)
        metricW = np.asanyarray(metricW)

        #Create an array 1-10
        Linear_Vals_10 = np.linspace(0, 9, 10)

        '''
        Set up to record the first and last 10 values, creating arrays marking index, depth, and difference in depth to next value
        '''
        Length_First10 = np.empty([10,3])    
        Length_First10[:,0] = Linear_Vals_10
        Length_First10[:,1] = metricL[0:10, 2]
        
        Width_First10 = np.empty([10,3])
        Width_First10[:,0] = Linear_Vals_10
        Width_First10[:,1] = metricW[0:10, 2]

        Length_Final10 = np.empty([10,3])
        Length_Final10_Index = np.linspace(metricL.shape[0]-10, metricL.shape[0]-1, 10)

        Length_Final10[:,0] = Length_Final10_Index
        Length_Final10[:,1] = metricL[metricL.shape[0]-10:metricL.shape[0], 2]

        Width_Final10 = np.empty([10,3])
        Width_Final10_Index = np.linspace(metricW.shape[0]-10, metricW.shape[0]-1, 10)
        
        Width_Final10[:,0] = Width_Final10_Index
        Width_Final10[:,1] = metricW[metricW.shape[0]-10:metricW.shape[0], 2]

        #Record difference in heights of neighboring pixels, first 10 coordinates 
        for k in range(10):
            Length_First10[k, 2] = (metricL[k, 2] - metricL[k+1, 2])*1000
            Width_First10[k, 2] = (metricW[k, 2] - metricW[k+1, 2])*1000

        #Record difference in heights of neighboring pixel coordinates, final 10
        #Length
        i=0
        for k in Length_Final10_Index:
            k = int(k)
            Length_Final10[i,2] =  (metricL[k, 2] - metricL[k-1, 2])*1000
            i+=1
        #Width
        i=0
        for k in Width_Final10_Index:
            k = int(k)
            Width_Final10[i,2] =  (metricW[k, 2] - metricW[k-1, 2])*1000
            i+=1

        #If the difference in Heights is greater than 5mm and height at pixel falls within 'zero' range, start measurment index at object
            #(Realsense has a vairation of ~1-3mm for distance values)
        for index in Length_First10:
            if index[2] > 5:
                if (index[1] > zero_min) and (index[1] < zero_max):
                    Starting_indexL = int(index[0]+1)+1
                    break
            else:
                Starting_indexL = 1
                continue
            
        for index in Width_First10:
            if index[2] > 5:
                if (index[1] > zero_min) and (index[1] < zero_max):
                    Starting_indexW = int(index[0]+1)+1
                    break
            else:
                Starting_indexW = 1
                continue

        for i in range(1,11):
            if Length_Final10[-i,2] > 5:
                if (Length_Final10[-i,1] > zero_min) and (Length_Final10[-i,1] < zero_max):
                    Final_indexL = int(Length_Final10[-i,0])-1
                    break
            else:
                Final_indexL = int(Length_Final10[-1,0])-1

        for i in range(1,11):
            if Width_Final10[-i,2] > 5:
                if (Width_Final10[-i,1] > zero_min) and (Width_Final10[-i,1] < zero_max):
                    Final_indexW = int(Width_Final10[-i,0])-1
                    break
            else:
                Final_indexW = int(Width_Final10[-1,0])-1

        #Calculate the length and width by finding euclidean distance from metric points on point cloud at values
        length = dist.euclidean((metricL[Starting_indexL,0], metricL[Starting_indexL,1]), (metricL[Final_indexL,0], metricL[Final_indexL,1]))
        width = dist.euclidean((metricW[Starting_indexW,0], metricW[Starting_indexW,1]), (metricW[Final_indexW,0], metricW[Final_indexW,1]))
        print("Length: ", length*1000, "mm   Width: ", width*1000, "mm")

        #Calculate the depth by subtracting the smallest height recorded in pointcloud by the 'zero' height
        pointCloud = convert_depth_frame_to_pointcloud(depth_image, intrinsics)
        pointCloud = np.asanyarray(pointCloud)
        height = (zero_depth - min(pointCloud[2,:]))*1000
        print("Height", height, "mm")

        #pic = cv2.imread('/home/hp/Documents/Dimensions_testing/Picture.jpg')
        #cv2.imshow("pic", pic)
        print(extremes[0][0]-10, extremes[1][0]+10, extremes[2][1]-10, extremes[3][1]+10)
        #cv2.waitKey(0)

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()

    return(length*1000, width*1000, height, extremes[0][0]-10, extremes[1][0]+10, extremes[2][1]-10, extremes[3][1]+10)
