from flask import Flask, request, jsonify
from flask_cors import CORS  # Add this import
import torch
from torchvision import models, transforms
from PIL import Image
import io
import base64
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)  # Add this line to enable CORS

# Load Faster R-CNN for object detection
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
detector = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
detector.eval()
detector.to(device)

# Load MobileNetV2 for image classification
classifier = models.mobilenet_v2(pretrained=True)
classifier.eval()
classifier.to(device)

# ImageNet class labels for classification
with open("imagenet_classes.txt", "r") as f:  # You'll need to download this file
    imagenet_labels = [line.strip() for line in f.readlines()]

# Preprocessing for object detection
def preprocess_detection(image):
    transform = transforms.Compose([transforms.ToTensor()])
    return transform(image).unsqueeze(0).to(device)

# Preprocessing for classification
def preprocess_classification(image):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return transform(image).unsqueeze(0).to(device)

# COCO class names for object detection
COCO_NAMES = [
    '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
    'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag',
    'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite',
    'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana',
    'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
    'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table',
    'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock',
    'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

# Process object detection
def detect_objects(image_tensor, threshold=0.5):
    with torch.no_grad():
        predictions = detector(image_tensor)[0]
    
    boxes = predictions["boxes"].cpu().numpy()
    labels = predictions["labels"].cpu().numpy()
    scores = predictions["scores"].cpu().numpy()

    # Filter by confidence threshold
    mask = scores >= threshold
    boxes = boxes[mask]
    labels = labels[mask]
    scores = scores[mask]

    return boxes, labels, scores

# Draw bounding boxes and labels on image
def draw_boxes(image, boxes, labels, scores):
    img = np.array(image)[:, :, ::-1].copy()  # Convert PIL RGB to OpenCV BGR
    for box, label, score in zip(boxes, labels, scores):
        x1, y1, x2, y2 = box.astype(int)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label_text = f"{COCO_NAMES[label]}: {score:.2f}"
        cv2.putText(img, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Convert back to base64
    _, buffer = cv2.imencode(".jpg", img)
    return base64.b64encode(buffer).decode("utf-8")

# Process image classification
def classify_image(image_tensor):
    with torch.no_grad():
        output = classifier(image_tensor)
        _, pred = torch.max(output, 1)
        return imagenet_labels[pred.item()]

@app.route("/api/process", methods=["POST"])
def process_image():
    if "image" not in request.files or "model" not in request.form:
        return jsonify({"error": "Missing image or model type"}), 400

    image_file = request.files["image"]
    model_type = request.form["model"]

    image = Image.open(image_file).convert("RGB")

    if model_type == "defect":  # Object detection
        image_tensor = preprocess_detection(image)
        boxes, labels, scores = detect_objects(image_tensor)
        annotated_image = draw_boxes(image, boxes, labels, scores)
        result = {
            "annotated_image": f"data:image/jpeg;base64,{annotated_image}",
            "detections": [
                {"label": COCO_NAMES[label], "score": float(score), "box": box.tolist()}
                for box, label, score in zip(boxes, labels, scores)
            ]
        }
    elif model_type == "classify":  # Image classification
        image_tensor = preprocess_classification(image)
        label = classify_image(image_tensor)
        result = {"label": label}
    else:
        return jsonify({"error": "Unsupported model type"}), 400

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)