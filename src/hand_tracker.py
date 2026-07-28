"""
hand_tracker.py
----------------
Thin wrapper around MediaPipe's Hand Landmarker (new Tasks API) that gives us:
  - landmark positions in pixel coordinates
  - finger up/down state
  - a simple named gesture derived from finger state

NOTE: Recent mediapipe builds (0.10.30+) no longer ship the old
`mediapipe.solutions` module, which is why `from mediapipe.solutions import
hands as mp_hands` used to fail with:
    ModuleNotFoundError: No module named 'mediapipe.solutions'
This version uses the modern `mediapipe.tasks` API instead, which is the
officially supported way to do hand landmark detection going forward.

On first run this will download a small (~10MB) hand_landmarker.task model
file into the assets/ folder. This requires an internet connection once;
after that it's cached locally and no further downloads happen.
"""

import os
import time
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.core.base_options import BaseOptions

from src import config

# Standard 21-point hand skeleton connections
# (equivalent to the old mp.solutions.hands.HAND_CONNECTIONS)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # index
    (5, 9), (9, 10), (10, 11), (11, 12),     # middle
    (9, 13), (13, 14), (14, 15), (15, 16),   # ring
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky
    (0, 17),                                 # palm base
]

_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "hand_landmarker.task",
)


def _ensure_model():
    """Download the hand landmark model once, on first run."""
    if os.path.exists(_MODEL_PATH):
        return
    os.makedirs(os.path.dirname(_MODEL_PATH), exist_ok=True)
    print("[AirDraw] Downloading hand landmark model (one-time, ~10 MB)...")
    urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
    print("[AirDraw] Model saved to", _MODEL_PATH)


class HandTracker:
    def __init__(self,
                 max_hands=config.MAX_NUM_HANDS,
                 detection_confidence=config.DETECTION_CONFIDENCE,
                 tracking_confidence=config.TRACKING_CONFIDENCE):
        _ensure_model()

        base_options = BaseOptions(model_asset_path=_MODEL_PATH)
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.landmarker = mp_vision.HandLandmarker.create_from_options(options)

        self.results = None
        self._start_time = time.time()

        # Landmark indices for fingertip and pip joints (MediaPipe hand model)
        self.tip_ids = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky

    def find_hands(self, frame, draw=True):
        """Run detection on a BGR frame and optionally draw landmarks on it."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int((time.time() - self._start_time) * 1000)
        self.results = self.landmarker.detect_for_video(mp_image, timestamp_ms)

        if self.results.hand_landmarks and draw:
            h, w, _ = frame.shape
            for hand_lms in self.results.hand_landmarks:
                points = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lms]
                for start_idx, end_idx in HAND_CONNECTIONS:
                    cv2.line(frame, points[start_idx], points[end_idx], (0, 255, 0), 2)
                for point in points:
                    cv2.circle(frame, point, 4, (0, 0, 255), -1)
        return frame

    def get_landmark_positions(self, frame, hand_index=0):
        """Return a list of [id, x, y] pixel positions for one detected hand."""
        landmark_list = []
        if self.results and self.results.hand_landmarks:
            if hand_index < len(self.results.hand_landmarks):
                hand = self.results.hand_landmarks[hand_index]
                h, w, _ = frame.shape
                for idx, lm in enumerate(hand):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    landmark_list.append([idx, cx, cy])
        return landmark_list

    def fingers_up(self, landmark_list):
        """
        Returns a list of 5 ints [thumb, index, middle, ring, pinky],
        1 if the finger is extended, 0 if folded.
        """
        if not landmark_list:
            return [0, 0, 0, 0, 0]

        fingers = []

        # Thumb: distance-based check instead of a raw x-coordinate compare.
        # A plain x-coordinate compare only works for ONE forearm rotation
        # (e.g. palm facing the camera) and flips incorrectly when the hand
        # is rotated to show the back of the hand instead. Comparing how far
        # the thumb TIP is from the hand's base (wrist) versus how far the
        # thumb's IP joint is from the wrist is rotation-independent: an
        # extended thumb is always farther from the wrist than a folded one,
        # regardless of which side of the hand faces the camera.
        wrist = landmark_list[0]
        thumb_tip = landmark_list[self.tip_ids[0]]
        thumb_ip = landmark_list[self.tip_ids[0] - 1]

        def _dist(a, b):
            return ((a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5

        if _dist(thumb_tip, wrist) > _dist(thumb_ip, wrist):
            fingers.append(1)
        else:
            fingers.append(0)

        # Other 4 fingers: rotation-independent distance check instead of a
        # plain y-coordinate compare. A pure y-compare only works when the
        # hand is held roughly upright facing the camera; as soon as the
        # hand tilts sideways (very common while actually drawing), the tip
        # can end up beside or below the PIP joint even though the finger
        # is genuinely extended, causing false "folded" reads and drawing
        # dropouts. Comparing distance-from-wrist instead (same principle
        # as the thumb check above) stays correct at any hand rotation.
        # `palm_size` scales the margin so it works whether the hand is
        # close to or far from the camera, and the margin itself prevents
        # flicker when the tip sits right on the border.
        palm_size = _dist(wrist, landmark_list[9])  # wrist -> middle MCP
        margin = 0.15 * palm_size

        for tip_id in self.tip_ids[1:]:
            tip = landmark_list[tip_id]
            pip = landmark_list[tip_id - 2]
            if _dist(tip, wrist) > _dist(pip, wrist) + margin:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def get_gesture(self, fingers):
        """Map a finger-state pattern to a named gesture used by config.py"""
        total_up = sum(fingers)

        if fingers == [0, 1, 0, 0, 0]:
            return config.GESTURE_DRAW
        elif fingers[1] == 1 and fingers[2] == 1 and total_up == 2:
            return config.GESTURE_SELECT
        elif total_up == 0:
            return config.GESTURE_ERASE
        elif total_up == 5:
            return config.GESTURE_CLEAR
        else:
            return config.GESTURE_IDLE