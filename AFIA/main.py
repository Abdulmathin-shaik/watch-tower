import cv2
import time
from src.detection.detector import DateDetector
from src.ui.alert import DateAlert
import time

def main():
    detector = DateDetector()
    alert = DateAlert()
    
    try:
        while True:
            ret, frame = detector.cap.read()
            if not ret:
                break
                
            if detector.check_motion(frame):
                current_time = time.time()
                if current_time - detector.last_trigger_time > detector.cooldown:
                    results = detector.model(frame)
                    detection_labels = []
                    for r in results:
                        if r.boxes is not None and len(r.boxes) > 0:
                            class_indices = r.boxes.cls.cpu().numpy()
                            detection_labels.extend([r.names[int(i)] for i in class_indices])
                    
                    if "date" not in detection_labels:
                        alert.show_alert(f"NO DATE DETECTED!\nFound: {detection_labels}")
                    detector.last_trigger_time = current_time
                    
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        detector.cleanup()

if __name__ == "__main__":
    main()