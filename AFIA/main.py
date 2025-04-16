# import ultralytics
# from ultralytics import YOLO
import cv2
import numpy as np
import matplotlib.pyplot as plt
import time

video_source = '/Users/abdulshaik/Desktop/Watch Tower/AFIA/6167566-hd_1920_1080_30fps.mp4'
cap = cv2.VideoCapture(video_source)
if not cap.isOpened():
    print("Error opening video stream or file")
    exit(1)

BGS_ENABLED = True
if BGS_ENABLED:
    # Background Subtraction
    backSub = cv2.createBackgroundSubtractorMOG2(
       history=500,varThreshold=32,detectShadows=False)
    print("Background Subtraction enabled")
while True:
  ret,frame = cap.read()
  if not ret:
    break
 # 1. Remove shadows (shadows are gray: value 127)
  _, fgmask = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)

    # 2. Morphological opening to remove small noise
  kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
  fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

    # 3. (Optional) Dilation to fill small holes inside object
  fgmask = cv2.dilate(fgmask, kernel, iterations=2)

    # 4. Use the mask on the original frame (optional)
  result = cv2.bitwise_and(frame, frame, mask=fgmask)

    # Show result
  cv2.imshow("Foreground Mask", fgmask)
  cv2.imshow("Detected Objects", result)
''' 
  # Apply background subtraction
  fgmask = backSub.apply(frame)

  #Optional applying kernel
  kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
  cleaned = cv2.morphologyEx(fgmask,cv2.MORPH_OPEN,kernel)
#   cv2.imshow('frame',frame)

  cv2.imshow('frame',cleaned)
#   cv2.imshow('clean',frame)
'''
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()