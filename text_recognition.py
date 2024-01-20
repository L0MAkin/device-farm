#text_recognition
import pytesseract
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import base64
import io

def process_image(image_base64, should_crop=False):
    # Path to tesseract executable
    pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
    
    image_data = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_data))

    if should_crop:
        full_width, full_height = image.size
        crop_box = (0, 0, full_width // 1, full_height // 3)
        image = image.crop(crop_box)
    
    threshold = 220
    filter_img = image.point(lambda p: p > threshold and 255)  
    filter_img = filter_img.filter(ImageFilter.MedianFilter())
    enhancer = ImageEnhance.Contrast(filter_img)
    filter_img = enhancer.enhance(2.0)
    enhancer = ImageEnhance.Sharpness(filter_img)
    filter_img = enhancer.enhance(2.0)
    #filter_img = ImageOps.invert(filter_img)

    final_img_cv = np.array(filter_img)
    final_img_cv = cv2.cvtColor(final_img_cv, cv2.COLOR_BGR2GRAY)

    # Use Tesseract to do OCR on the image
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(final_img_cv, output_type=pytesseract.Output.DICT)

    words_data = []
    for i in range(len(data['text'])):
        if int(data['conf'][i]) > 60:  # confidence threshold
            word_data = {
                "text": data['text'][i],
                "bounding_box": {
                    "x": data['left'][i],
                    "y": data['top'][i],
                    "width": data['width'][i],
                    "height": data['height'][i]
                }
            }
            words_data.append(word_data)
            (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            cv2.rectangle(final_img_cv, (x, y), (x + w, y + h), (0, 255, 0), 2)
    #print(words_data)
    #cv2.imshow('Image with Bounding Boxes', final_img_cv)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    return words_data

if __name__ == "__main__":
    # Sample base64 string or load image and convert to base64
    # For example:
    with open("/Users/lomakin/Downloads/IMG_58B6823E418C-1.jpeg", "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

    #image_base64 = 'your_base64_string_here'  # Replace with your base64 string

    # Call the function with the sample base64 string and cropping option
    process_image(image_base64, should_crop=True)



