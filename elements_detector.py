import cv2 as cv
import numpy as np
import copy
import base64
import io
from PIL import Image

def process_image(image_base64, element_to_analyze ='likes'):
    elements_locations = {
        'search': {'screen_part': 'top-right','element_path': '/Users/lomakin/Downloads/search_final.png'},
        'comments': {'screen_part': 'right','element_path': '/Users/lomakin/Downloads/coment2_tiktok.png'},
        'likes': {'screen_part': 'right','element_path': '/Users/dennybalon/Documents/like_comments.png'},
    }
    spinner_path = elements_locations[element_to_analyze]['element_path']
    spinner_image = cv.imread(spinner_path)
    gray_spinner = cv.cvtColor(spinner_image, cv.COLOR_BGR2GRAY)
    # Load your target image
    image_data_base64 = base64.b64decode(image_base64)
    image_pil = Image.open(io.BytesIO(image_data_base64)).convert('RGB')
    image = np.array(image_pil)
    height, width = image.shape[:2]

    #Select part of screen related to searching element
    def select_roi(image, element_name, elements_locations):
        height, width = image.shape[:2]
        screen_part = elements_locations[element_name]['screen_part']
        
        if screen_part == 'right':
            start_x = width - (width // 3)
            start_y = height// 3
            roi = image[start_y:height, start_x:width]
        elif screen_part == 'top-right':
            # Assuming top-left(25%) means 25% from top and left
            start_x = width - (width // 6)  # Adjust according to your definition
            end_y = height // 6
            roi = image[0:end_y, start_x:width]
        else:
            roi = image  # Default to full image if no specific part is defined
            screen_part = 'full'  # Indicate that the full image is used
        
        return roi, screen_part


    # Choose an element to analyze
    roi, screen_part = select_roi(image, element_to_analyze, elements_locations)
    offset_x, offset_y = 0, 0
    if screen_part == 'right':
        offset_x = width - (width // 3)  # Calculate offset for the right third
        offset_y = height// 3
    elif 'top-right' in screen_part:
        offset_x = width - (width // 6)  # Calculate offset for the right third
        offset_y = 0


    # Contrast image
    image_float = roi.astype(np.float32)
    # Scale the pixel values to be between 0 and 1
    image_normalized = image_float / 255.0
    # Apply the contrast factor
    contrast_factor = 10.0  # Change this value to adjust the contrast
    image_contrasted = cv.pow(image_normalized, contrast_factor)
    # Scale back to 0-255 and change to uint8
    image_contrasted = image_contrasted * 255.0
    image_contrasted = image_contrasted.astype(np.uint8)
    #cv.imshow('image_contrasted', image_contrasted)
    #cv.waitKey(0)
    #cv.destroyAllWindows()


    if element_to_analyze != "likes":
        try:
            # Get foreground image
            height, width = image_contrasted.shape[:2]
            # Initialize the mask
            mask = np.zeros(image_contrasted.shape[:2],np.uint8)
            # Define background and foreground models (used by the GrabCut algorithm)
            bgdModel = np.zeros((1,65),np.float64)
            fgdModel = np.zeros((1,65),np.float64)
            # Define the rectangle around the foreground area
            rect = (10, 10, width - 30, height - 50) # You need to choose this rectangle manually
            # Apply GrabCut
            cv.grabCut(image_contrasted,mask,rect,bgdModel,fgdModel,5,cv.GC_INIT_WITH_RECT)
            # Set all definite background and probable background pixels to 0, others to 1
            mask2 = np.where((mask==0)|(mask==2),0,1).astype('uint8')
            # Multiply the image with the new mask to get the foreground
            Foreground = roi*mask2[:,:,np.newaxis]
            # Filter image by white color

            # Define the range of white color in HSV
            lower_white = np.array([228, 228, 228])
            upper_white = np.array([255, 255, 255])
            # Create the mask
            mask = cv.inRange(Foreground, lower_white, upper_white)
        except:
            pass

    # Crop the ROI from the image
    screenshot = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)
    if screenshot is None:
        print("Could not load the screenshot.")

    # Prepare template image to select contours    
    final_img_cv_figure = np.array(gray_spinner)
    _, thresh_spinner = cv.threshold(final_img_cv_figure, 200, 255, cv.THRESH_BINARY)
    kernel3 = np.ones((1, 1), np.uint8)
    opened_img_figure = cv.morphologyEx(thresh_spinner, cv.MORPH_OPEN, kernel3)
    kernel4 = np.ones((3, 3), np.uint8)
    img_dilated_figure = cv.dilate(opened_img_figure, kernel4, iterations=1)
    if element_to_analyze != "likes":
        edged_spiner = cv.Canny(img_dilated_figure, 200, 255)
    else:
        edged_spiner = cv.Canny(final_img_cv_figure, 200, 255)
    
    contours_spinner, _ = cv.findContours(edged_spiner, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    #Select biggest contour
    spinner_contour = max(contours_spinner, key=cv.contourArea)
    x, y, w, h = cv.boundingRect(spinner_contour)
    aspect_ratio_template = float(w) / h
    area_template = cv.contourArea(spinner_contour)
    hull_template = cv.convexHull(spinner_contour)
    hull_area_template = cv.contourArea(hull_template)
    solidity_template = float(area_template) / hull_area_template

    final_image_spiner = spinner_image.copy()
    final_image_spiner2 = cv.drawContours(final_image_spiner, spinner_contour, -1, ( 0, 0, 255), 3)
    #cv.imshow('Final Image with Matched Contour', final_image_spiner2)
    #cv.waitKey(0)
    #cv.destroyAllWindows()


    # Prepare screenshot image to get countours
    if element_to_analyze != "likes":
        final_img_cv = np.array(mask)
    else:
        final_img_cv = np.array(image_contrasted)
    
    #cv.imshow('final_img_cv', final_img_cv)
    #cv.waitKey(0)
    #cv.destroyAllWindows()
    
    _, binary_image = cv.threshold(final_img_cv, 200, 255, cv.THRESH_BINARY)
    kernel = np.ones((3, 3), np.uint8)
    opened_img = cv.morphologyEx(binary_image, cv.MORPH_OPEN, kernel)
    kernel2 = np.ones((3, 3), np.uint8)
    img_dilated = cv.dilate(opened_img, kernel2, iterations=1)
    edged = cv.Canny(img_dilated, 200, 255)

    if element_to_analyze != "likes":
        edged = cv.Canny(img_dilated, 200, 255)
    else:
        edged = cv.Canny(final_img_cv, 200, 255)
    
    contours, _ = cv.findContours(edged, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)

    filtered_contours = []
    for contour in contours:
        x, y, width, height = cv.boundingRect(contour)
        if element_to_analyze != "likes" and width >= 30 and width <= 90 and height >= 30 and height <= 90:
            area = cv.contourArea(contour)
            hull = cv.convexHull(contour)
            hull_area = cv.contourArea(hull)
            solidity = float(area) / hull_area
            if abs(solidity_template - solidity) < 0.5:
                 filtered_contours.append(contour)
        else:
            filtered_contours.append(contour)

    final_image = roi.copy()
    final_image2 = cv.drawContours(final_image, filtered_contours, -1, ( 0, 0, 255), 3)
    #cv.imshow('roi', final_image2)
    #cv.waitKey(0)
    #cv.destroyAllWindows()

    # Initialize variables to keep track of the best match
    aspect_ratio_threshold = 0.1
    best_match_value = 0.1
    best_match_contour = None


    for contour in filtered_contours:
        x, y, w, h = cv.boundingRect(contour)
        aspect_ratio = float(w) / h
        if abs(aspect_ratio - aspect_ratio_template) < aspect_ratio_threshold:
            match_value = cv.matchShapes(spinner_contour, contour, 1, 0.0)
            if match_value < best_match_value:
                best_match_value = match_value
                best_match_contour = contour
    print(best_match_value)
    # Check if a best match was found and draw it
    if best_match_contour is not None:
        matched_contour_global = np.array(best_match_contour) + np.array([offset_x, offset_y])
        final_image = image.copy()
        final_image2 = cv.drawContours(final_image, [matched_contour_global], -1, ( 0, 0, 255), 8)
        x, y, w, h = cv.boundingRect(matched_contour_global)
        x_min, y_min, x_max, y_max = x, y, x + w, y + h 
        #cv.rectangle(final_image, (x, y), (x + w, y + h), (0, 255, 0), 3)
        #cv.imshow('Final Image with Matched Contour', final_image2)
        #cv.waitKey(0)
        #cv.destroyAllWindows()
        return[x_min, y_min, x_max, y_max]
    else:
        print("No matching contour found.")
        return None
    

if __name__ == "__main__":
    # Sample base64 string or load image and convert to base64
    # For example:
    with open("/Users/lomakin/Downloads/IMG_2893.PNG", "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

    #image_base64 = 'your_base64_string_here'  # Replace with your base64 string

    # Call the function with the sample base64 string and cropping option
    coordinates = process_image(image_base64, element_to_analyze ='likes')
    print(coordinates)