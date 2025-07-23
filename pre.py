import os
import cv2
import numpy as np

def auto_crop_only(img):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 40, 255])

    mask = cv2.inRange(img_hsv, lower_white, upper_white)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15,15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("No circular part detected.")
        return None

    largest_contour = max(contours, key=cv2.contourArea)
    x,y,w,h = cv2.boundingRect(largest_contour)

    cropped = img[y:y+h, x:x+w]
    return cropped

def enhance_defects(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced_gray = clahe.apply(gray)
    enhanced_img = cv2.merge([enhanced_gray]*3)
    return enhanced_img

def process_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for fname in os.listdir(input_folder):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            input_path = os.path.join(input_folder, fname)
            img = cv2.imread(input_path)
            if img is None:
                print(f"Failed to read {fname}")
                continue

            cropped = auto_crop_only(img)
            if cropped is None:
                print(f"Skipping {fname}, no circular part detected.")
                continue

            enhanced = enhance_defects(cropped)
            output_path = os.path.join(output_folder, fname)
            cv2.imwrite(output_path, enhanced)
            print(f"Processed and saved: {fname}")

if __name__ == "__main__":
    input_folder = "test\defective"   # change to your folder path
    output_folder = "masks" # folder to save cropped + enhanced images

    process_folder(input_folder, output_folder)
