"""
config.py
----------
Central configuration for the AirDraw application.
All tunable constants live here so the rest of the codebase stays clean.
"""

# ---------------------------------------------------------------------------
# Camera / Window Settings
# ---------------------------------------------------------------------------
CAM_WIDTH = 1280
CAM_HEIGHT = 720
CAM_INDEX = 0
FLIP_CAMERA = True  # Mirror the webcam feed for a natural drawing experience

# ---------------------------------------------------------------------------
# MediaPipe Hand Detection Settings
# ---------------------------------------------------------------------------
MAX_NUM_HANDS = 1
DETECTION_CONFIDENCE = 0.75
TRACKING_CONFIDENCE = 0.75

# ---------------------------------------------------------------------------
# Drawing Settings
# (These will be used in Day 3 when the drawing canvas is added.)
# ---------------------------------------------------------------------------
BRUSH_THICKNESS = 8
ERASER_THICKNESS = 60
SMOOTHENING = 5          # Higher value = smoother but slightly slower strokes
CANVAS_SAVE_DIR = "saved_drawings"

# ---------------------------------------------------------------------------
# Color Palette
# Colors are stored in BGR format because OpenCV uses BGR instead of RGB.
# ---------------------------------------------------------------------------
COLOR_PALETTE = [
    ("Red",    (0, 0, 255)),
    ("Green",  (0, 255, 0)),
    ("Blue",   (255, 0, 0)),
    ("Yellow", (0, 255, 255)),
    ("Purple", (255, 0, 255)),
    ("White",  (255, 255, 255)),
    ("Eraser", (0, 0, 0)),
]

# ---------------------------------------------------------------------------
# UI / Gesture Timing Settings
# ---------------------------------------------------------------------------
# Reserved height (in pixels) for the toolbar that will be added in Day 3.
TOOLBAR_HEIGHT = 80

# Margin around toolbar buttons.
TOOLBAR_BOX_MARGIN = 20

# Number of consecutive frames the "clear" gesture must be held
# before the application clears the canvas.
CLEAR_HOLD_FRAMES = 30

# ---------------------------------------------------------------------------
# Gesture Constants
# These gesture names are returned by HandTracker.get_gesture().
# ---------------------------------------------------------------------------
GESTURE_DRAW = "draw"        # Index finger only
GESTURE_SELECT = "select"    # Index + Middle fingers
GESTURE_ERASE = "erase"      # Closed fist
GESTURE_CLEAR = "clear"      # Open palm (all five fingers)
GESTURE_IDLE = "idle"        # Any other hand pose