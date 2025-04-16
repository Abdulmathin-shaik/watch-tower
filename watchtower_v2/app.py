from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from torchvision.models.detection import fasterrcnn_resnet50_fpn_v2, FasterRCNN_ResNet50_FPN_V2_Weights
from PIL import Image
import io
import cv2
import numpy as np
import base64
import pytesseract
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Analytics storage
analytics = {
    'object': {'total': 0, 'common_objects': {}},
    'classify': {'total': 0, 'common_classes': {}},
    'anomaly': {'total': 0, 'defects': 0},
    'ocr': {'total': 0, 'chars': 0}
}

# Load models
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Object Detection - Using improved FasterRCNN V2
detection_weights = FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT
detection_model = fasterrcnn_resnet50_fpn_v2(weights=detection_weights)
detection_model.eval()
detection_model.to(device)

COCO_CLASSES = detection_weights.meta["categories"]

# Image Classification - Using ResNet152
classify_model = models.resnet152(weights=models.ResNet152_Weights.DEFAULT)
classify_model.eval()
classify_model.to(device)

# Preprocessing transforms
preprocess_classify = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

preprocess_detect = transforms.Compose([
    transforms.ToTensor(),
])

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/api/inspect', methods=['POST'])
def inspect():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded.'}), 400

    try:
        image_file = request.files['image']
        inspection_type = request.form['type']
        image = Image.open(io.BytesIO(image_file.read())).convert('RGB')
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        if inspection_type == 'object':
            img_tensor = preprocess_detect(image).to(device)
            with torch.no_grad():
                predictions = detection_model([img_tensor])[0]
            
            labels = predictions['labels'].cpu().numpy()
            scores = predictions['scores'].cpu().numpy()
            threshold = 0.5
            boxes = predictions['boxes'].cpu().numpy()
            detections = [(COCO_CLASSES[label], score, box) for label, score, box in zip(labels, scores, boxes) if score > threshold]
            
            # Draw bounding boxes
            for name, score, box in detections:
                x1, y1, x2, y2 = map(int, box)
                cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img_cv, f'{name} ({score:.2f})', (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Convert to base64
            _, buffer = cv2.imencode('.jpg', img_cv)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            if detections:
                analytics['object']['total'] += 1
                for name, _, _ in detections:
                    analytics['object']['common_objects'][name] = analytics['object']['common_objects'].get(name, 0) + 1
                output = f"Detected {len(detections)} objects"
            else:
                output = "No objects detected above threshold."
                
            return jsonify({
                'result': output,
                'image': f'data:image/jpeg;base64,{img_base64}'
            })

        elif inspection_type == 'classify':
            input_tensor = preprocess_classify(image).unsqueeze(0).to(device)
            with torch.no_grad():
                output = classify_model(input_tensor)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)
                top_probs, top_catids = probabilities.topk(3)  # Get top 3 predictions
                
                # Read ImageNet classes
                with open('imagenet_classes.txt', 'r') as f:
                    categories = [s.strip() for s in f.readlines()]
                
                predictions = []
                for prob, idx in zip(top_probs, top_catids):
                    predictions.append(f"{categories[idx]} ({prob:.2%})")
                
                analytics['classify']['total'] += 1
                analytics['classify']['common_classes'][categories[top_catids[0]]] = \
                    analytics['classify']['common_classes'].get(categories[top_catids[0]], 0) + 1
                
            return jsonify({'result': f"Top predictions: {', '.join(predictions)}"})

        elif inspection_type == 'anomaly':
            # Convert to grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Draw defects and analyze
            defect_count = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # Minimum area threshold
                    defect_count += 1
                    cv2.drawContours(img_cv, [contour], -1, (0, 0, 255), 2)
                    # Add bounding box
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(img_cv, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    cv2.putText(img_cv, f'Defect {defect_count}', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            # Convert result image to base64
            _, buffer = cv2.imencode('.jpg', img_cv)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            analytics['anomaly']['total'] += 1
            analytics['anomaly']['defects'] += defect_count
            output = f"Found {defect_count} potential defects" if defect_count > 0 else "No defects detected"
            return jsonify({
                'result': output,
                'image': f'data:image/jpeg;base64,{img_base64}'
            })

        elif inspection_type == 'ocr':
            # Preprocess for OCR
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            # Apply thresholding to get better OCR results
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Run OCR
            text = pytesseract.image_to_string(binary)
            text = text.strip()
            
            # Draw text regions
            boxes = pytesseract.image_to_boxes(binary)
            h, w, _ = img_cv.shape
            for b in boxes.splitlines():
                b = b.split()
                cv2.rectangle(img_cv, (int(b[1]), h - int(b[2])), (int(b[3]), h - int(b[4])), (0, 255, 0), 2)
            
            # Convert result image to base64
            _, buffer = cv2.imencode('.jpg', img_cv)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            analytics['ocr']['total'] += 1
            analytics['ocr']['chars'] += len(text)
            
            if text:
                output = f"Extracted text: '{text}'"
            else:
                output = "No text detected."
                
            return jsonify({
                'result': output,
                'image': f'data:image/jpeg;base64,{img_base64}'
            })

        return jsonify({'error': 'Invalid inspection type.'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0', threaded=True)