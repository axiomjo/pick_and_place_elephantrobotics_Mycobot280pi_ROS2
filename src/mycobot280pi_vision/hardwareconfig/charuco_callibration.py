import cv2
import cv2.aruco as aruco
import numpy as np
import yaml
import glob
import os

# --- 1. Define your ChArUco board ---
squares_horizontally = 10
squares_vertically = 10
square_length = 0.038  # in meters
marker_length = 0.028  # in meters
dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
board = aruco.CharucoBoard((squares_horizontally, squares_vertically),
                           square_length, marker_length, dictionary)
aruco_params = aruco.DetectorParameters()

all_charuco_corners = []
all_charuco_ids = []
image_size = None

# --- 2. Load your calibration images ---
image_folder = "calibration_images"
image_files = glob.glob(os.path.join(image_folder, "*.jpg"))
image_files.extend(glob.glob(os.path.join(image_folder, "*.jpeg")))
image_files.extend(glob.glob(os.path.join(image_folder, "*.png")))

if not image_files:
    print(f"❌ No images found in the '{image_folder}' folder.")
    exit()

print(f"✅ Found {len(image_files)} images for calibration.")

for image_path in image_files:
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if image_size is None:
        image_size = gray.shape[::-1]

    # Detect ArUco markers
    marker_corners, marker_ids, rejected_markers = aruco.detectMarkers(
        gray, dictionary, parameters=aruco_params)

    if len(marker_corners) > 0:
        retval, charuco_corners, charuco_ids = aruco.interpolateCornersCharuco(
            marker_corners, marker_ids, gray, board)

        if retval:
            all_charuco_corners.append(charuco_corners)
            all_charuco_ids.append(charuco_ids)

# --- 3. Run calibration ---
if len(all_charuco_corners) > 0:
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = aruco.calibrateCameraCharuco(
        all_charuco_corners, all_charuco_ids, board, image_size, None, None)

    if ret:
        print("✅ Calibration successful!")
        print("Camera matrix:\n", camera_matrix)
        print("\nDistortion coefficients:\n", dist_coeffs)

        # Helper function to deeply convert all numpy types to native python
        def to_python_type(x):
            if isinstance(x, np.ndarray):
                return x.tolist()
            elif isinstance(x, (np.float32, np.float64, np.int32, np.int64)):
                return float(x)
            elif isinstance(x, list):
                return [to_python_type(y) for y in x]
            else:
                return x

        calib_data = {
            "image_width": int(image_size[0]),
            "image_height": int(image_size[1]),
            "camera_name": "my_camera",
            "camera_matrix": {
                "rows": 3,
                "cols": 3,
                "data": to_python_type(camera_matrix.flatten())
            },
            "distortion_model": "plumb_bob",
            "distortion_coefficients": {
                "rows": 1,
                "cols": len(to_python_type(dist_coeffs.flatten())),
                "data": to_python_type(dist_coeffs.flatten())
            },
            "rectification_matrix": {
                "rows": 3,
                "cols": 3,
                "data": [1, 0, 0, 0, 1, 0, 0, 0, 1]
            },
            "projection_matrix": {
                "rows": 3,
                "cols": 4,
                "data": to_python_type([
                    camera_matrix[0, 0], 0, camera_matrix[0, 2], 0,
                    0, camera_matrix[1, 1], camera_matrix[1, 2], 0,
                    0, 0, 1, 0
                ])
            }
        }

        with open("camera_calibration.yaml", "w") as f:
            yaml.safe_dump(calib_data, f, default_flow_style=False)

        print("📂 Saved calibration to camera_calibration.yaml")

    else:
        print("❌ Calibration failed.")
else:
    print("❌ Not enough ChArUco corners detected for calibration.")
