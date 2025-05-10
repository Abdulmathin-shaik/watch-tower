from ultralytics import YOLO

import cv2
import time

import torch

# Load YOLOv5 model (you can use 'yolov5s', 'yolov5m', etc.)
# model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
model = YOLO('best.pt')  # Load your custom model
model.conf = 0.4  # confidence threshold

# Start webcam
cap = cv2.VideoCapture(0)

# Define the Region of Interest (ROI) as a box
x1, y1, x2, y2 = 400, 400, 800, 800

# Background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2()

# Timing control
last_trigger_time = 0
cooldown = 3  # seconds

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Draw ROI box
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Extract ROI from frame
    roi = frame[y1:y2, x1:x2]

    # Apply background subtraction
    fgmask = fgbg.apply(roi)

    # Find motion contours
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = False
    for cnt in contours:
        if cv2.contourArea(cnt) > 800:  # Filter small movements
            motion_detected = True
            break

    if motion_detected:
        current_time = time.time()
        if current_time - last_trigger_time > cooldown:
            print("🎯 Motion detected! Running YOLO...")

            # Run YOLO detection
                        # Run YOLO detection
            results = model(frame)
            
            # Extract detection labels using boxes
            detection_labels = []
            for r in results:
                if r.boxes is not None and len(r.boxes) > 0:
                    # Get class indices
                    class_indices = r.boxes.cls.cpu().numpy()
                    # Convert to class names
                    detection_labels.extend([r.names[int(i)] for i in class_indices])
            
            # Check if the product has a 'date'
            if "date" not in detection_labels:
                print("No date detected for the product!")
                print("Detected classes:", detection_labels)
            else:
                print("Date detected!")
                print("All detections:", detection_labels)
            
            last_trigger_time = current_time
            # Print results
            # labels = results.pandas().xyxy[0]['name'].tolist()
            # print("Detected:", labels)

            # # Save annotated frame
            # annotated_frame = results.render()[0]
            # filename = f"yolo_result_{int(current_time)}.jpg"
            # cv2.imwrite(filename, annotated_frame)
            # print(f"[Saved] {filename}")

            last_trigger_time = current_time

    # Display
    cv2.imshow("Live Feed", frame)
    cv2.imshow("Motion Mask", fgmask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
