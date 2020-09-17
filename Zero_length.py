import cv2
import pyrealsense2 as rs
import numpy as np


 # Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
pipeline.start(config)

try:
    while True:

        # Wait for a coherent pair of frames: depth and color
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue
        
        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        #depth_value = np.asanyarray(depth_frame.get_distance())
        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        # Stack both images horizontally
        images = np.vstack((color_image, depth_colormap))

        # Show images
        #x+=x
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', images)
        if cv2.waitKey(1) & 0xFF == ord('c'):
            cv2.imwrite('Picture.jpg', color_image)
            break
    
    array = np.zeros(depth_image.shape)
    for x in range(200, 480):
        for y in range(100, 380):
            array[y][x] = round(depth_frame.get_distance(x,y), 3)

    print(array)
    new_array = array[100:380,200:480]
    print(np.mean(new_array))
    zero = open("Zero_Length", 'w')
    zero.write(str(np.mean(new_array)))
    zero.close()
    print("Max: ", np.max(new_array))
    print("Min: ", np.min(new_array))
    np.savetxt('zerolength.txt', new_array, fmt='%1.3f')
    cv2.imshow("spliced", new_array)
    cv2.waitKey(0)
finally:
    pipeline.stop()
    cv2.destroyAllWindows()


