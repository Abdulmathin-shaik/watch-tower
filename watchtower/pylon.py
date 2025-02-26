from pypylon import pylon
import cv2
import numpy as np

# Connect to the first available camera
try:
    # Create an instant camera object with the camera device
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())

    # Open the camera
    camera.Open()

    # Set some basic camera parameters if needed
    camera.ExposureTime.SetValue(5000)  # Adjust exposure time (in microseconds) if needed
    camera.Gain.SetValue(0)  # Optional: Adjust gain if the image is too dark or bright

    # Grab a single frame
    grab_result = camera.GrabOne(4000)  # Timeout in milliseconds

    if grab_result.GrabSucceeded():
        # Convert the image to a numpy array
        img = grab_result.Array

        # Display the image
        cv2.imshow("Captured Image", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        # Optional: Save the image
        cv2.imwrite("captured_image.png", img)
    else:
        print("Failed to grab image")

    # Release the camera
    camera.Close()

except Exception as e:
    print(f"Error: {e}")