import pyrealsense2 as rs
import cv2
import numpy as np
from Point_Cloud import convert_depth_frame_to_pointcloud, convert_depth_pixel_to_metric_coordinate
import BoundingBox
from scipy.spatial import distance as dist
import math


def percent_error(actual):
    
    error = abs((actual-zero_depth)/zero_depth)*100
    return(error)

zero = open("Zero_Length", 'r')
zero_depth =zero.read()
zero.close()
zero_depth = float(zero_depth)

resolution_width = 1280 # pixels
resolution_height = 720 # pixels
#resolution_width = 640 # pixels
#resolution_height = 480 # pixels
frame_rate = 30  # fps
dispose_frames_for_stablisation = 30  # frames
# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, resolution_width, resolution_height, rs.format.z16, frame_rate)
config.enable_stream(rs.stream.infrared, 1, resolution_width, resolution_height, rs.format.y8, frame_rate)
config.enable_stream(rs.stream.color, resolution_width, resolution_height, rs.format.bgr8, frame_rate)


# Start streaming
profile = pipeline.start(config)
sensor = profile.get_device().first_depth_sensor()
#sensor.set_option(rs.option.emitter_enabled, 0)
#sensor.set_option(rs.option.laser_power, 330)
depth_stream=rs.video_stream_profile(profile.get_stream(rs.stream.depth))
#print(depth_stream.get_intrinsics().ppx)
intrinsics = depth_stream.get_intrinsics()
try:
    while True:

        # Wait for a coherent pair of frames: depth and color
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
        
        # Stack both images horizontally
        #images = np.vstack((color_image, depth_colormap))
        images = np.vstack((depth_colormap, color_image))
        #print(new_image)
        # Show images
        #x+=x
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', depth_colormap)
        cv2.imshow('color', color_image)
        #cv2.imshow('new Image', new_image)
        if cv2.waitKey(1) & 0xFF == ord('c'):
            #cv2.imwrite('Picture.jpg', color_image)
            cv2.imwrite('Picture.jpg', color_image)
            break
    bounding_box, c, top, bottom, left, right, extremes = BoundingBox.get_dimensions()
    
    Depth = depth_frame.get_distance(int(top[0]), int(top[1]))
    [X,Y,Z] = convert_depth_pixel_to_metric_coordinate(Depth, top[0], top[1], intrinsics)
    Depth1 = depth_frame.get_distance(int(bottom[0]), int(bottom[1]))
    [X1,Y1,Z1] = convert_depth_pixel_to_metric_coordinate(Depth1, bottom[0], bottom[1], intrinsics)
    Depth2 = depth_frame.get_distance(int(left[0]), int(left[1]))
    [X2,Y2,Z2] = convert_depth_pixel_to_metric_coordinate(Depth2, left[0], left[1], intrinsics)
    Depth3 = depth_frame.get_distance(int(right[0]), int(right[1]))
    [X3,Y3,Z3] = convert_depth_pixel_to_metric_coordinate(Depth3, right[0], right[1], intrinsics)
    dA = dist.euclidean((X, Y), (X1, Y1))
    dB = dist.euclidean((X2, Y2), (X3, Y3))

    c = np.array(c)
    c = np.resize(c, (c.shape[0],2))
    
    xmax = int(np.max(bounding_box[:, 0]))
    xmin = int(np.min(bounding_box[:, 0]))
    ymax = int(np.max(bounding_box[:, 1]))
    ymin = int(np.min(bounding_box[:, 1]))
    #print(ymin, ymax, xmin, xmax)
    depth = depth_frame.get_distance(xmin, ymin)
    depth1 = depth_frame.get_distance(xmin, ymax)
    depth2 = depth_frame.get_distance(xmax, ymin)
    depth3 = depth_frame.get_distance(xmax, ymax)
    [x,y,z] = convert_depth_pixel_to_metric_coordinate(depth, xmin, ymin, intrinsics)
    [x1,y1,z1] = convert_depth_pixel_to_metric_coordinate(depth1, xmin, ymax, intrinsics)
    [x2,y2,z2] = convert_depth_pixel_to_metric_coordinate(depth2, xmax, ymin, intrinsics)
    [x3,y3,z3] = convert_depth_pixel_to_metric_coordinate(depth3, xmax, ymax, intrinsics)
    boundry = [[x,y,z], [x1,y1,z1], [x2,y2,z2], [x3,y3,z3]]
    boundry = np.asanyarray(boundry)
    Xmin = np.min(boundry[:,0])
    Xmax = np.max(boundry[:,0])
    Ymin = np.min(boundry[:,1])
    Ymax = np.max(boundry[:,1])
    #print("Boundry: ", boundry)

    zeroMin = open("Zero_Min", 'r')
    zero_min = float(zeroMin.read())
    zeroMin.close()
    zeroMax = open("Zero_Max", 'r')
    zero_max = float(zeroMax.read())
    zeroMax.close()
    
    
    #print(bounding_box)
    pointCloud = convert_depth_frame_to_pointcloud(depth_image, intrinsics)
    pointCloud = np.asanyarray(pointCloud)
    pointCloud = pointCloud[:,np.logical_and(pointCloud[0,:]<Xmax, pointCloud[0,:]>Xmin)]
    #print(pointCloud.shape)
    pointCloud = pointCloud[:,np.logical_and(pointCloud[1,:]<Ymax, pointCloud[1,:]>Ymin)]
    pointCloud2 = pointCloud[:, pointCloud[2,:]<zero_min]
    print(pointCloud)

    coord = np.c_[pointCloud[0,:], pointCloud[1,:]].astype('float32')
    coord2 = np.c_[pointCloud2[0,:], pointCloud2[1,:]].astype('float32')
    min_area_rectangle = cv2.minAreaRect(coord)
    min_area_rectangle2 = cv2.minAreaRect(coord2)
    height = max(pointCloud[2,:]) - min(pointCloud[2,:])
    print("height", (0.5515710586734694 - min(pointCloud[2,:]))*1000, "mm")
    print(top)
    print(bottom)
    #print(min_area_rectangle)
    print("minAreaRect: ", min_area_rectangle[1][0], min_area_rectangle[1][1])
    print("minAreaRect2: ", min_area_rectangle2[1][0], min_area_rectangle2[1][1])
    cv2.waitKey(0)

finally:
    pipeline.stop()
    cv2.destroyAllWindows()


