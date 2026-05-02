import cv2
import os
import shutil
import tempfile
import numpy as np
import mediapipe as mp
from fastapi import FastAPI, File, UploadFile
from models.squat import SquatAnalyzer

mp_pose = mp.solutions.pose

app = FastAPI()

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
              np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return angle if angle <= 180.0 else 360 - angle

def calculate_back_angle(shoulder, hip):
    dx = shoulder[0] - hip[0]
    dy = shoulder[1] - hip[1]
    return np.degrees(np.arctan2(abs(dx), abs(dy)))

def get_side_landmarks(landmarks, side="LEFT"):
    p = mp_pose.PoseLandmark
    if side.upper() == "RIGHT":
        sh, hip, kn, ank, toe = p.RIGHT_SHOULDER, p.RIGHT_HIP, p.RIGHT_KNEE, p.RIGHT_ANKLE, p.RIGHT_FOOT_INDEX
    else:
        sh, hip, kn, ank, toe = p.LEFT_SHOULDER, p.LEFT_HIP, p.LEFT_KNEE, p.LEFT_ANKLE, p.LEFT_FOOT_INDEX

    return {
        "shoulder": [landmarks[sh].x, landmarks[sh].y],
        "hip":      [landmarks[hip].x, landmarks[hip].y],
        "knee":     [landmarks[kn].x,  landmarks[kn].y],
        "ankle":    [landmarks[ank].x, landmarks[ank].y],
        "toe":      [landmarks[toe].x, landmarks[toe].y],
        "vis":      (landmarks[sh].visibility + landmarks[hip].visibility) / 2
    }

@app.post("/analyze")
async def analyze_squats(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        shutil.copyfileobj(file.file, temp_video)
        temp_path = temp_video.name

    analyzer = SquatAnalyzer()
    cap = cv2.VideoCapture(temp_path)

    frame_idx = 0
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            frame_idx += 1
            current_time = frame_idx / fps

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                left  = get_side_landmarks(landmarks, "LEFT")
                right = get_side_landmarks(landmarks, "RIGHT")

                shoulder_width = np.linalg.norm(np.array(left["shoulder"]) - np.array(right["shoulder"]))
                active_side    = left if left["vis"] > right["vis"] else right
                hip_length     = np.linalg.norm(np.array(active_side["hip"]) - np.array(active_side["knee"]))

                is_side_view = hip_length > (shoulder_width * 0.9) or (abs(left["vis"] - right["vis"]) > 0.3)

                if is_side_view:
                    active     = left if left["vis"] > right["vis"] else right
                    knee_angle = calculate_angle(active["hip"], active["knee"], active["toe"])
                    back_angle = calculate_back_angle(active["shoulder"], active["hip"])

                    analyzer.update_side(knee_angle, back_angle, current_time)

    cap.release()

    try:
        os.remove(temp_path)
    except Exception:
        pass

    clean_reps_data = []
    for rep in analyzer.side.reps_data:
        clean_rep = {}
        for key, value in rep.items():
            if hasattr(value, "item"):
                clean_rep[key] = value.item()
            else:
                clean_rep[key] = value
        clean_reps_data.append(clean_rep)

    analyzer.save_report()

    return {
        "filename":   file.filename,
        "total_reps": int(analyzer.counter),
        "details":    clean_reps_data
    }