import torch
import cv2
import base64
import numpy as np
from PIL import Image
import io

# Ensure the YOLOv5 folder is in the Python path and you are in the YOLOv5 environment
# Load the YOLOv5 model
def run_yolo_object_detection(image_base64):
    model_path = '/Users/lomakin/yolov5/runs/train/exp5/weights/best.pt'
    model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=False)  # force_reload to ensure the latest model is loaded

    # Read the screenshot
    image_data_base64 = base64.b64decode(image_base64)
    # Open the image
    image_pil = Image.open(io.BytesIO(image_data_base64)).convert('RGB')
    # Convert PIL image to numpy array
    img = np.array(image_pil)

    image_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Now you can use the image_bgr with OpenCV functions
   
    if img is None:
        print(f"Failed to load image")
    else:
        print("Image loaded successfully")

    # Perform object detection
    results = model(image_bgr)

    # To access detection results programmatically:
    detected_objects = {}
    for *xyxy, conf, cls in results.xyxy[0]:  # xyxy: coordinates, conf: confidence, cls: class
        # Extract bounding box coordinates and other info
        x_min, y_min, x_max, y_max = map(int, xyxy)
        cls_id = int(cls)
        conf = float(conf)
        #if conf < 0.1:
        #    continue
        
        # Get class name
        class_name = model.names[cls_id]

        # Format label with class name and confidence
        label = f"{class_name}: {conf:.2f}"
        obj_data = {
            "coordinates": {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max},
            "label": label,
            "confidence": conf
        }
        
        # If the class name exists, append the object data; otherwise, create a new list
        if class_name not in detected_objects:
            detected_objects[class_name] = [obj_data]  # Initialize a new list for this class name
        else:
            detected_objects[class_name].append(obj_data)  # Append to existing list for this class name
        # Draw bounding box and label on the image
        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 4)
        (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 4)

        # Calculate the x position of the text to align it to the right
        text_x = x_max - text_width

        # Ensure that the text stays within the bounds of the image
        text_x = max(text_x, 0)

        # Adjust y position to avoid overlaying on the top edge of the rectangle
        text_y = y_min - 15
        text_y = max(text_y, text_height)  # Make sure text_y doesn't go beyond the upper edge of the image

        # Draw the text aligned to the right edge of the rectangle
        cv2.putText(img, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 4)

    # Display the modified image with detections
    #cv2.imshow('YOLOv5 Detections', img)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    return detected_objects

if __name__ == '__main__':
    with open("/Users/lomakin/Downloads/IMG_2757.PNG", "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    #image_base64 = 'your_base64_string_here'  # Replace with your base64 string
    detected_objects = run_yolo_object_detection(image_base64)
    print(detected_objects)

    