"""
main.py
--------
AirDraw — draw in the air using just your index finger and a webcam.

Gestures (default, finger-counting based):
    Index finger only up      -> Draw
    Index + Middle up         -> Hover / select color on toolbar
    Fist (all folded)         -> Pause / eraser stops connecting strokes
    Open palm (all 5 up, held)-> Clear canvas
    Eraser tool selected      -> Draw acts as an eraser instead of ink

Keyboard shortcuts:
    q  -> quit
    c  -> clear canvas
    s  -> save current drawing to ./saved_drawings/
"""

import cv2

from src import config
from src.hand_tracker import HandTracker
from src.canvas_utils import Canvas


def main():
    cap = cv2.VideoCapture(config.CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)

    tracker = HandTracker()
    canvas = None
    clear_hold_counter = 0
    smooth_x, smooth_y = None, None  # smoothed draw-point, reset on pen-lift

    while True:
        success, frame = cap.read()
        if not success:
            print("Camera frame not received. Exiting.")
            break

        if config.FLIP_CAMERA:
            frame = cv2.flip(frame, 1)

        h, w, _ = frame.shape
        if canvas is None:
            canvas = Canvas(w, h)

        frame = tracker.find_hands(frame, draw=False)
        landmarks = tracker.get_landmark_positions(frame)

        toolbar_boxes = canvas.draw_toolbar(frame)

        if landmarks:
            fingers = tracker.fingers_up(landmarks)
            gesture = tracker.get_gesture(fingers)

            index_x, index_y = landmarks[8][1], landmarks[8][2]
            middle_x, middle_y = landmarks[12][1], landmarks[12][2]

            if gesture == config.GESTURE_SELECT:
                canvas.reset_stroke()
                smooth_x, smooth_y = None, None
                mid_x = (index_x + middle_x) // 2
                mid_y = (index_y + middle_y) // 2
                cv2.circle(frame, (mid_x, mid_y), 12, (255, 255, 255), 2)
                if mid_y < config.TOOLBAR_HEIGHT:
                    canvas.check_toolbar_selection(mid_x, mid_y, toolbar_boxes)
                clear_hold_counter = 0

            elif gesture == config.GESTURE_DRAW:
                # Exponential smoothing on the raw landmark point: without
                # this the line is visibly shaky frame-to-frame because raw
                # landmark detections jitter by a few pixels even when the
                # hand is perfectly still. Higher config.SMOOTHENING = less
                # jitter but a touch more lag, matching the comment in
                # config.py.
                if smooth_x is None:
                    smooth_x, smooth_y = index_x, index_y
                else:
                    smooth_x += (index_x - smooth_x) / config.SMOOTHENING
                    smooth_y += (index_y - smooth_y) / config.SMOOTHENING
                draw_x, draw_y = int(smooth_x), int(smooth_y)

                cv2.circle(frame, (draw_x, draw_y), 8, canvas.current_color, -1)
                if draw_y > config.TOOLBAR_HEIGHT:  # don't draw over the toolbar
                    canvas.draw_line(draw_x, draw_y)
                else:
                    canvas.reset_stroke()
                    smooth_x, smooth_y = None, None
                clear_hold_counter = 0

            elif gesture == config.GESTURE_CLEAR:
                clear_hold_counter += 1
                canvas.reset_stroke()
                smooth_x, smooth_y = None, None
                if clear_hold_counter >= config.CLEAR_HOLD_FRAMES:
                    canvas.clear()
                    clear_hold_counter = 0

            else:  # erase-fist / idle
                canvas.reset_stroke()
                smooth_x, smooth_y = None, None
                clear_hold_counter = 0
        else:
            canvas.reset_stroke()
            smooth_x, smooth_y = None, None
            clear_hold_counter = 0

        output = canvas.merge_with_frame(frame)

        cv2.putText(output, f"Tool: {canvas.current_tool_name}",
                    (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("AirDraw - Press Q to quit", output)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            canvas.clear()
        elif key == ord('s'):
            path = canvas.save()
            print(f"Drawing saved to: {path}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()