"""
config.py
----------
Central configuration for the AirDraw application.
All tunable constants live here so the rest of the codebase stays clean.
"""

# ---------------------------------------------------------------------------
# Camera / Window settings
# ---------------------------------------------------------------------------
CAM_WIDTH = 1280
CAM_HEIGHT = 720
CAM_INDEX = 0
FLIP_CAMERA = True  # mirror the feed so it feels natural to draw

# ---------------------------------------------------------------------------
# MediaPipe Hands settings
# ---------------------------------------------------------------------------
MAX_NUM_HANDS = 1
DETECTION_CONFIDENCE = 0.75
TRACKING_CONFIDENCE = 0.75

# ---------------------------------------------------------------------------
# Drawing settings
# ---------------------------------------------------------------------------
BRUSH_THICKNESS = 8
ERASER_THICKNESS = 60
SMOOTHENING = 5          # higher = smoother but slightly laggier strokes
CANVAS_SAVE_DIR = "saved_drawings"

# Color palette shown on the top toolbar: (name, BGR color)
COLOR_PALETTE = [
    ("Red",    (0, 0, 255)),
    ("Green",  (0, 255, 0)),
    ("Blue",   (255, 0, 0)),
    ("Yellow", (0, 255, 255)),
    ("Purple", (255, 0, 255)),
    ("White",  (255, 255, 255)),
    ("Eraser", (0, 0, 0)),
]

TOOLBAR_HEIGHT = 100
TOOLBAR_BOX_MARGIN = 20

# ---------------------------------------------------------------------------
# Gesture -> Action mapping
# ---------------------------------------------------------------------------
# These are the finger-state patterns (thumb, index, middle, ring, pinky)
# where 1 = extended, 0 = folded. This lightweight finger-counting logic
# drives the app in real time using MediaPipe landmarks.
#
# For a heavier, dataset-trained gesture classifier (e.g. trained on the
# HaGRID dataset: https://github.com/hukenovs/hagrid), see
# src/hagrid_classifier.py and docs/hagrid_integration.md
GESTURE_DRAW = "draw"          # index finger only up -> draw
GESTURE_SELECT = "select"      # index + middle up -> hover/select on toolbar
GESTURE_ERASE = "erase"        # fist (all folded) -> erase mode
GESTURE_CLEAR = "clear"        # all five fingers up (open palm) -> clear canvas
GESTURE_IDLE = "idle"          # anything else -> do nothing

CLEAR_HOLD_FRAMES = 25  # frames the open-palm gesture must be held to trigger clear