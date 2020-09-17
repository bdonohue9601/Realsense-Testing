import pyrealsense2 as rs
import cv2
import numpy as np
from Point_Cloud import convert_depth_frame_to_pointcloud, convert_depth_pixel_to_metric_coordinate
import BoundingBox
from scipy.spatial import distance as dist

def poll_frames(self):
    """
    Poll for frames from the enabled Intel RealSense devices. This will return at least one frame from each device. 
    If temporal post processing is enabled, the depth stream is averaged over a certain amount of frames
    
    Parameters:
    -----------
    """
    frames = {}
    while len(frames) < len(self._enabled_devices.items()) :
        for (serial, device) in self._enabled_devices.items():
            streams = device.pipeline_profile.get_streams()
            frameset = device.pipeline.poll_for_frames() #frameset will be a pyrealsense2.composite_frame object
            if frameset.size() == len(streams):
                frames[serial] = {}
                for stream in streams:
                    if (rs.stream.infrared == stream.stream_type()):
                        frame = frameset.get_infrared_frame(stream.stream_index())
                        key_ = (stream.stream_type(), stream.stream_index())
                    else:
                        frame = frameset.first_or_default(stream.stream_type())
                        key_ = stream.stream_type()
                    frames[serial][key_] = frame

    return frames

def load_settings_json(self, path_to_settings_file):
    """
    Load the settings stored in the JSON file
    """

    with open(path_to_settings_file, 'r') as file:
            json_text = file.read().strip()

    for (device_serial, device) in self._enabled_devices.items():
        # Get the active profile and load the json file which contains settings readable by the realsense
        device = device.pipeline_profile.get_device()
        advanced_mode = rs.rs400_advanced_mode(device)
        advanced_mode.load_json(json_text)


zero = open("Zero_Length", 'r')
zero_depth =zero.read()
zero.close()

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
    print(top)
    #points_on_line = np.linspace(top, bottom, 100, dtype = int)
    points_on_lineL = np.linspace(top, bottom, int(dist.euclidean(top, bottom)), dtype = int)
    points_on_lineW = np.linspace(left, right, int(dist.euclidean(left, right)), dtype = int)
    print(points_on_lineL.shape)
    metricL = []
    metricL = np.zeros([int(dist.euclidean(top, bottom)),3])
    print(metricL)
    #print(points_on_line[0, :])
    i = 0 
    #line_cloud = convert_depth_pixel_to_metric_coordinate(depth_frame.get_distance(points_on_line[:,0], points_on_line[:,1]), points_on_line[:,0], points_on_line[:,0], intrinsics)
    for points in points_on_lineL:
        metricL[i] = convert_depth_pixel_to_metric_coordinate(depth_frame.get_distance(points[0], points[1]), points[0], points[1], intrinsics)
        metric = convert_depth_pixel_to_metric_coordinate(depth_frame.get_distance(points[0], points[1]), points[0], points[1], intrinsics)
        #print(points, [metric])
        
        #metric = np.vstack(metric, ([x,y,z]))
        #print(metric)
        #print([x,y,z])
        i+=1

    metricW = []
    metricW = np.zeros([int(dist.euclidean(left, right)),3])
    #print(points_on_line[0, :])
    j = 0 
    #line_cloud = convert_depth_pixel_to_metric_coordinate(depth_frame.get_distance(points_on_line[:,0], points_on_line[:,1]), points_on_line[:,0], points_on_line[:,0], intrinsics)
    for points in points_on_lineW:
        metricW[j] = convert_depth_pixel_to_metric_coordinate(depth_frame.get_distance(points[0], points[1]), points[0], points[1], intrinsics)
        metric = convert_depth_pixel_to_metric_coordinate(depth_frame.get_distance(points[0], points[1]), points[0], points[1], intrinsics)
        print(j, points, metric)
        #print([x,y,z])
        j+=1
    print(metricL)
    #print(metricL[:,2])
    #print(np.mean(metricL[:,2]))
    print(metricW)
    print(metricW.shape)
    print("L x W", dA*1000, "mm", dB*1000, "mm")

    metricL = [ii for ii in metricL if all(ii)]
    metricW = [iii for iii in metricW if all(iii)]
    metricL = np.asanyarray(metricL)
    metricW = np.asanyarray(metricW)
    L10 = np.empty([10,3])
    linL = np.linspace(0, 9, 10)
    L10[:,0] = linL
    L10[:,1] = metricL[0:10, 2]
    W10 = np.empty([10,3])
    linW = np.linspace(0, 9, 10)
    W10[:,0] = linW
    W10[:,1] = metricW[0:10, 2]

    Lfinal10 = np.empty([10,3])
    linL = np.linspace(metricL.shape[0]-10, metricL.shape[0]-1, 10)
    Lfinal10[:,0] = linL
    Lfinal10[:,1] = metricL[metricL.shape[0]-10:metricL.shape[0], 2]


    Wfinal10 = np.empty([10,3])
    linW = np.linspace(metricW.shape[0]-10, metricW.shape[0]-1, 10)
    Wfinal10[:,0] = linW
    Wfinal10[:,1] = metricW[metricW.shape[0]-10:metricW.shape[0], 2]
    


    length = dist.euclidean((metricL[1,0], metricL[1,1]), (metricL[(metricL.shape[0]-2),0], metricL[(metricL.shape[0]-2),1]))
    width = dist.euclidean((metricW[1,0], metricW[1,1]), (metricW[(metricW.shape[0]-2),0], metricW[(metricW.shape[0]-2),1]))
    #print("Length: ", length*1000, "mm   Width: ", width*1000, "mm")

    
    for k in range(10):
        #print(k,": ", (metricL[k, 2] - metricL[k+1, 2])*1000)
        L10[k, 2] = (metricL[k, 2] - metricL[k+1, 2])*1000
        
    #print("Final L: \n", Lfinal10)
    i=0
    for k in linL:
        k = int(k)
        #print(k,": ", (metricL[k-1, 2] - metricL[k, 2])*1000)
        Lfinal10[i,2] =  (metricL[k, 2] - metricL[k-1, 2])*1000
        i+=1
    
    print( ' ')
    #print("First 10 width Heights: \n", W10, "\n")
    for k in range(10):
        #print(k,": ", (metricW[k, 2] - metricW[k+1, 2])*1000)
        W10[k, 2] = (metricW[k, 2] - metricW[k+1, 2])*1000
    
    i=0
    for k in linW:
        k = int(k)
        #print(k,": ", (metricW[k-1, 2] - metricW[k, 2])*1000)
        Wfinal10[i,2] =  (metricW[k, 2] - metricW[k-1, 2])*1000
        i+=1
    print("First L: \n", L10)
    print("Final L: \n", Lfinal10, "\n")

    print("First W: \n", W10)
    print("Final W: \n", Wfinal10, "\n")

    for index in L10:
        if index[2] > 5:
            Starting_indexL = int(index[0]+1)+1
            break
        else:
            Starting_indexL = 1
            continue
    for index in W10:
        if index[2] > 5:
            Starting_indexW = int(index[0]+1)+1
            break
        else:
            Starting_indexW = 1
            continue

    for i in range(1,11):
        if Lfinal10[-i,2] > 5:
            Final_indexL = int(Lfinal10[-i,0])-1
            break
        else:
            Final_indexL = int(Lfinal10[-1,0])-1

    for i in range(1,11):
        if Wfinal10[-i,2] > 5:
            Final_indexW = int(Wfinal10[-i,0])-1
            break
        else:
            Final_indexW = int(Wfinal10[-1,0])-1
    print("Length-Start: ", Starting_indexL, "End: ", Final_indexL)
    print("Width-Start: ", Starting_indexW, "End: ", Final_indexW)

    length = dist.euclidean((metricL[Starting_indexL,0], metricL[Starting_indexL,1]), (metricL[Final_indexL,0], metricL[Final_indexL,1]))
    width = dist.euclidean((metricW[Starting_indexW,0], metricW[Starting_indexW,1]), (metricW[Final_indexW,0], metricW[Final_indexW,1]))
    print("Length: ", length*1000, "mm   Width: ", width*1000, "mm")

    
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

    
    #print(bounding_box)
    pointCloud = convert_depth_frame_to_pointcloud(depth_image, intrinsics)
    pointCloud = np.asanyarray(pointCloud)
    pointCloud = pointCloud[:,np.logical_and(pointCloud[0,:]<Xmax, pointCloud[0,:]>Xmin)]
    #print(pointCloud.shape)
    pointCloud = pointCloud[:,np.logical_and(pointCloud[1,:]<Ymax, pointCloud[1,:]>Ymin)]
    #print(pointCloud.shape)
    #print(pointCloud)
    #print(pointCloud.shape)
    #pointCloud_clipped = pointCloud[ymin:ymax, xmin:xmax]
    #print(pointCloud_clipped)
    coord = np.c_[pointCloud[0,:], pointCloud[1,:]].astype('float32')
    #print(coord)
    min_area_rectangle = cv2.minAreaRect(coord)
    height = max(pointCloud[2,:]) - min(pointCloud[2,:])
    print("height", (0.5515710586734694 - min(pointCloud[2,:]))*1000, "mm")
    #print(min_area_rectangle)
    #print("minAreaRect", min_area_rectangle[1][0], min_area_rectangle[1][1])
    cv2.waitKey(0)

finally:
    pipeline.stop()
    cv2.destroyAllWindows()


