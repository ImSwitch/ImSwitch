import os
import subprocess
import numpy as np

# we have to run this script as root

def detect_external_drives():
    # Run 'df' command to get disk usage and filter only mounted devices
    df_result = subprocess.run(['df', '-h'], stdout=subprocess.PIPE)
    output = df_result.stdout.decode('utf-8')

    # Split the output by lines
    lines = output.splitlines()

    external_drives = []

    # Iterate through each line
    for line in lines:
        # Check if the line contains '/media' (common mount point for external drives)
        if '/media/' in line:
            # Split the line by spaces and get the second column (which contains the mount point)
            drive_info = line.split()
            mount_point = " ".join(drive_info[5:])  # Assuming the mount point is at index 5
            external_drives.append(mount_point)

    return external_drives

def create_folder_on_drive(drive, folder_name):
    folder_path = os.path.join(drive, folder_name)
    
    # Check if the folder already exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder '{folder_name}' on {drive}")
    else:
        print(f"Folder '{folder_name}' already exists on {drive}")

    return folder_path

def save_file_in_folder(folder_path):
    file_content = "Hello, World!"

    file_name = "example.txt"
    file_path = os.path.join(folder_path, file_name)

    with open(file_path, 'w') as file:
        file.write(file_content)

    print(f"Saved file '{file_name}' in '{folder_path}'")


# Test the function
external_drives = detect_external_drives()
print("External drives detected:", external_drives)

# Example usage:
if external_drives:
    # Assume we want to create a folder on the first detected external drive
    drive_to_use = external_drives[0]
    folder_path = create_folder_on_drive(drive_to_use, "test"+np.random.randint(1000))

# Example usage:
if folder_path:
    save_file_in_folder(folder_path)

