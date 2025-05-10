from ultralytics import YOLO
import os  
import cv2
import numpy as np

img = cv2.imread('test.JPG')
model = YOLO('best.pt')  # Load a model
results = model.predict(source=img, conf=0.5, show=True)  # Predict with confidence threshold
for r in results:
    r.show()