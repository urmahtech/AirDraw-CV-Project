"""
canvas_utils.py
----------------
Handles the persistent drawing canvas, the color/tool toolbar overlay,
and blending the canvas on top of the live webcam feed.
"""

import os
import time
import cv2
import numpy as np
from src import config


class Canvas:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.canvas = np.zeros((height, width, 3), np.uint8)
        self.current_color = config.COLOR_PALETTE[0][1]
        self.current_tool_name = config.COLOR_PALETTE[0][0]
        self.prev_x, self.prev_y = 0, 0

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------
    def draw_toolbar(self, frame):
        """Draw color swatches across the top of the frame and return
        a list of (name, color, (x1, y1, x2, y2)) boxes for hit-testing."""
        boxes = []
        n = len(config.COLOR_PALETTE)
        box_width = self.width // n

        for i, (name, color) in enumerate(config.COLOR_PALETTE):
            x1 = i * box_width + config.TOOLBAR_BOX_MARGIN // 2
            x2 = (i + 1) * box_width - config.TOOLBAR_BOX_MARGIN // 2
            y1, y2 = 10, config.TOOLBAR_HEIGHT - 10

            swatch_color = color if name != "Eraser" else (50, 50, 50)
            cv2.rectangle(frame, (x1, y1), (x2, y2), swatch_color, -1)

            if color == self.current_color and name == self.current_tool_name:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 3)

            cv2.putText(frame, name, (x1 + 5, y2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            boxes.append((name, color, (x1, y1, x2, y2)))
        return boxes

    def check_toolbar_selection(self, x, y, boxes):
        """If (x, y) falls inside a toolbar box, switch tool/color."""
        for name, color, (x1, y1, x2, y2) in boxes:
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.current_tool_name = name
                self.current_color = color
                return True
        return False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw_line(self, x, y):
        if self.prev_x == 0 and self.prev_y == 0:
            self.prev_x, self.prev_y = x, y

        thickness = (config.ERASER_THICKNESS
                     if self.current_tool_name == "Eraser"
                     else config.BRUSH_THICKNESS)
        color = (0, 0, 0) if self.current_tool_name == "Eraser" else self.current_color

        cv2.line(self.canvas, (self.prev_x, self.prev_y), (x, y), color, thickness)
        self.prev_x, self.prev_y = x, y

    def reset_stroke(self):
        """Call this when the pen lifts (not in draw mode) so the next
        stroke doesn't jump-connect to the last point."""
        self.prev_x, self.prev_y = 0, 0

    def clear(self):
        self.canvas = np.zeros((self.height, self.width, 3), np.uint8)

    # ------------------------------------------------------------------
    # Compositing
    # ------------------------------------------------------------------
    def merge_with_frame(self, frame):
        """Overlay the drawing canvas onto the live camera frame."""
        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, inv_mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY_INV)
        inv_mask = cv2.cvtColor(inv_mask, cv2.COLOR_GRAY2BGR)

        frame_bg = cv2.bitwise_and(frame, inv_mask)
        merged = cv2.bitwise_or(frame_bg, self.canvas)
        return merged

    def save(self):
        os.makedirs(config.CANVAS_SAVE_DIR, exist_ok=True)
        filename = f"drawing_{int(time.time())}.png"
        path = os.path.join(config.CANVAS_SAVE_DIR, filename)
        cv2.imwrite(path, self.canvas)
        return path