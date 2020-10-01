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

    TLX, TLY = bounding_box[0,0]-1,bounding_box[0,1]+1
    TRX, TRY = bounding_box[1,0]-1,bounding_box[1,1]+1
    BLX, BLY = bounding_box[3,0]+1,bounding_box[3,1]-1
    BRX, BRY = bounding_box[2,0]+1,bounding_box[2,1]-1
    
    c = np.array(c)
    c = np.resize(c, (c.shape[0],2))
    

    nrows, ncols = c.shape
    dtype={'names':['f{}'.format(i) for i in range(ncols)],
           'formats':ncols * [c.dtype]}

    topline = np.linspace((bounding_box[0,0]-1,bounding_box[0,1]+1), (bounding_box[1,0]-1,bounding_box[1,1]+1), dtype = int)
    topline = topline.astype('int32')
    bottomline = np.linspace((bounding_box[3,0]+1,bounding_box[3,1]-1), (bounding_box[2,0]+1,bounding_box[2,1]-1), 100, dtype = int)
    bottomline = bottomline.astype('int32')
    print(bottomline)
    topPoints = np.intersect1d(c.view(dtype), topline.view(dtype))
    # This last bit is optional if you're okay with "C" being a structured array...
    topPoints = topPoints.view(c.dtype).reshape(-1, ncols)

    bottomPoints = np.intersect1d(c.view(dtype), bottomline.view(dtype))
    # This last bit is optional if you're okay with "C" being a structured array...
    bottomPoints = bottomPoints.view(c.dtype).reshape(-1, ncols)
    print(topPoints)
    print(bottomPoints)
    cv2.waitKey(0)
    orig = cv2.imread('/home/hp/Documents/Dimensions_testing/Picture.jpg')
    
    i = 0 
    topPointsM = np.zeros([topPoints.shape[0], 3])
    for point in topPoints:
        cv2.circle(orig, (point[0], point[1]), 1, (0, 255, 0), -1)
        Depth = depth_frame.get_distance(int(point[0]), int(point[0]))
        point_conv = convert_depth_pixel_to_metric_coordinate(Depth, point[0], point[1], intrinsics)
        topPointsM[i] = point_conv
        i += 1

    i = 0 
    bottomPointsM = np.zeros([bottomPoints.shape[0], 3])
    for point in bottomPoints:
        cv2.circle(orig, (point[0], point[1]), 1, (0, 255, 0), -1)
        Depth = depth_frame.get_distance(int(point[0]), int(point[0]))
        point_conv = convert_depth_pixel_to_metric_coordinate(Depth, point[0], point[1], intrinsics)
        bottomPointsM[i] = point_conv
        i += 1

    print(topPointsM)
    print(bottomPointsM)
    TopPoint = topPoints[0]
    BottomPoint = bottomPoints[0]
    print(TopPoint)
    print(BottomPoint)
    print(depth_frame.get_distance(int(BottomPoint[0]), int(BottomPoint[1])))
##    TopPoint = topPoints[int(topPoints.shape[0]/2)]
##    BottomPoint = bottomPoints[int(bottomPoints.shape[0]/2)]
    
    Depth = depth_frame.get_distance(int(TopPoint[0]), int(TopPoint[1]))
    TopPointM = topPointsM[0]

    Depth = depth_frame.get_distance(int(BottomPoint[0]), int(BottomPoint[1]))
    BottomPointM = bottomPointsM[0]

    print("TOP POINT:      ", TopPointM)
    print("Bottom POINT:      ", BottomPointM)


    firstDist = dist.euclidean((TopPointM[0], TopPointM[1]), (BottomPointM[0], BottomPointM[1]))*1000

    thetaOne = math.atan((topPoints[0,1]-bottomPoints[0,1])/(topPoints[0,0]-bottomPoints[0,0]))
    thetaTwo = math.atan((TLY-TRY)/(TLX-TRX))
    thetaTwo2 = math.atan((BLY-BRY)/(BLX-BRX))
    print(thetaOne)
    print(thetaTwo, thetaTwo2)

    if thetaOne > 0 and thetaTwo > 0:
        theta = thetaOne-thetaTwo
        
    elif thetaOne < 0 and thetaTwo > 0:
        theta = math.pi - (thetaTwo+thetaOne)
    else:
        theta = thetaOne-thetaTwo
    
    newDist = math.sin(theta)*firstDist
    print("New Dist: ", newDist)
    cv2.circle(orig, (TopPoint[0], TopPoint[1]), 5, (0, 0, 255), -1)
    cv2.circle(orig, (BottomPoint[0],BottomPoint[1]), 5, (0, 0, 255), -1)    
    
    cv2.imshow("NEWImage", orig)
    cv2.waitKey(0)


finally:
    pipeline.stop()
    cv2.destroyAllWindows()


