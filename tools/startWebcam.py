import cv2


def get_adjustable_parameters(camera_index=0):
    # Open the camera
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # List of property IDs for adjustable camera parameters
    property_ids = [
        cv2.CAP_PROP_BRIGHTNESS,
        cv2.CAP_PROP_CONTRAST,
        cv2.CAP_PROP_SATURATION,
        cv2.CAP_PROP_HUE,
        cv2.CAP_PROP_GAIN,
        cv2.CAP_PROP_EXPOSURE,
        cv2.CAP_PROP_AUTO_EXPOSURE,
        # Add more property IDs as needed
    ]

    adjustable_parameters = {}

    for prop_id in range(20):
        value = cap.get(prop_id)
        adjustable_parameters[prop_id] = value

    # Release the camera
    cap.release()

    return adjustable_parameters

def main():
    # Open the default camera (usually the built-in webcam)
    camera_index=0
    camera_index="/dev/video0"
    if 0:
        parameters = get_adjustable_parameters(camera_index)
        
        print("Adjustable Camera Parameters:")
        for prop_id, value in parameters.items():
            print(f"Property ID {prop_id}: {value}")

    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Set the exposure time (in milliseconds)
    exposure_time = 10  # Adjust this value as needed

    ## Set the exposure property
    #cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
    #cap.set(cv2.CAP_PROP_EXPOSURE, exposure_time)
    #cap.set( cv2.CAP_PROP_GAIN, 1)
    cap.set(3, 320)
    cap.set(4, 240)
    while True:
        # Read a frame from the camera
        ret, frame = cap.read()

        if not ret:
            print("Error: Could not read a frame.")
            break

        # Display the frame in a window
        cv2.imshow("Webcam with Exposure Adjustment", frame)

        # Check for user input to exit
        key = cv2.waitKey(1)
        if key == 27:  # Press 'Esc' to exit
            break

    # Release the camera and close the OpenCV window
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
