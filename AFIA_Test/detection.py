import cv2
import time
from typing import Tuple
from ultralytics import YOLO


def run_inspection(
    model_path: str = 'best.pt',
    conf_thresh: float = 0.4,
    cooldown: float = 3,
    roi: Tuple[int, int, int, int] = (100, 100, 540, 380)
) -> None:
    """
    Runs a motion-triggered YOLO inspection with a single resizable OpenCV window and ROI display.

    Prints to console whether 'date' is detected or not, then continues scanning until user quits with 'q'.
    """
    # Load YOLO model
    model = YOLO(model_path)
    model.conf = conf_thresh

    # Unpack ROI
    x1, y1, x2, y2 = roi

    # Initialize capture and background subtractor
    cap = cv2.VideoCapture(0)
    fgbg = cv2.createBackgroundSubtractorMOG2()

    # Setup window
    win_name = "Inspection Feed"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, 640, 480)

    last_trigger = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Draw ROI rectangle
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Motion detection on ROI
        roi_frame = frame[y1:y2, x1:x2]
        fgmask = fgbg.apply(roi_frame)
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        motion = any(cv2.contourArea(c) > 800 for c in contours)

        # Show only the main feed
        cv2.imshow(win_name, frame)

        if motion:
            now = time.time()
            if now - last_trigger > cooldown:
                last_trigger = now
                print("🎯 Motion detected! Running YOLO...")
                results = model(frame)

                # Collect labels
                labels = []
                for res in results:
                    for cls in res.boxes.cls.cpu().numpy():
                        labels.append(res.names[int(cls)])

                if 'date' in labels:
                    print("✅ Date detected! Detected:", labels)
                else:
                    print("⚠️ Date NOT detected. Detected:", labels)

        # Exit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()