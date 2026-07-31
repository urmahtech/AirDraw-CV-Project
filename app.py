import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
import cv2

from src.hand_tracker import HandTracker
from src.canvas_utils import Canvas
from src import config


st.set_page_config(
    page_title="AirDraw",
    layout="wide"
)

st.title("✍️ AirDraw")
st.write("Draw in the air using your hand.")
class AirDrawProcessor(VideoProcessorBase):

    def __init__(self):

        self.tracker = HandTracker()

        self.canvas = None
        self.clear_hold_counter = 0

        self.smooth_x = None
        self.smooth_y = None

    def recv(self, frame):

        img = frame.to_ndarray(format="bgr24")

        if config.FLIP_CAMERA:
            img = cv2.flip(img, 1)

        h, w, _ = img.shape

        if self.canvas is None:
            self.canvas = Canvas(w, h)

        img = self.tracker.find_hands(img, draw=False)
        landmarks = self.tracker.get_landmark_positions(img)

        toolbar_boxes = self.canvas.draw_toolbar(img)
        if landmarks:

            fingers = self.tracker.fingers_up(landmarks)

            gesture = self.tracker.get_gesture(fingers)

            index_x, index_y = landmarks[8][1], landmarks[8][2]
            middle_x, middle_y = landmarks[12][1], landmarks[12][2]
            if gesture == config.GESTURE_SELECT:
                self.canvas.reset_stroke()
                self.smooth_x = None
                self.smooth_y = None

                mid_x = (index_x + middle_x) // 2
                mid_y = (index_y + middle_y) // 2

                cv2.circle(img, (mid_x, mid_y), 12, (255, 255, 255), 2)

                if mid_y < config.TOOLBAR_HEIGHT:
                    self.canvas.check_toolbar_selection(
                        mid_x,
                        mid_y,
                        toolbar_boxes,
                    )

                self.clear_hold_counter = 0

            elif gesture == config.GESTURE_DRAW:

                if self.smooth_x is None:
                    self.smooth_x = index_x
                    self.smooth_y = index_y
                else:
                    self.smooth_x += (
                        index_x - self.smooth_x
                    ) / config.SMOOTHENING

                    self.smooth_y += (
                        index_y - self.smooth_y
                    ) / config.SMOOTHENING

                draw_x = int(self.smooth_x)
                draw_y = int(self.smooth_y)

                cv2.circle(
                    img,
                    (draw_x, draw_y),
                    8,
                    self.canvas.current_color,
                    -1,
                )

                if draw_y > config.TOOLBAR_HEIGHT:
                    self.canvas.draw_line(draw_x, draw_y)
                else:
                    self.canvas.reset_stroke()
                    self.smooth_x = None
                    self.smooth_y = None

                self.clear_hold_counter = 0

            elif gesture == config.GESTURE_CLEAR:

                self.clear_hold_counter += 1

                self.canvas.reset_stroke()

                self.smooth_x = None
                self.smooth_y = None

                if self.clear_hold_counter >= config.CLEAR_HOLD_FRAMES:
                    self.canvas.clear()
                    self.clear_hold_counter = 0

            else:

                self.canvas.reset_stroke()

                self.smooth_x = None
                self.smooth_y = None

                self.clear_hold_counter = 0

        else:

            self.canvas.reset_stroke()

            self.smooth_x = None
            self.smooth_y = None

            self.clear_hold_counter = 0

        output = self.canvas.merge_with_frame(img)

        cv2.putText(
            output,
            f"Tool: {self.canvas.current_tool_name}",
            (10, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        return av.VideoFrame.from_ndarray(
            output,
            format="bgr24",
        )
webrtc_streamer(
    key="airdraw",
    video_processor_factory=AirDrawProcessor,
    media_stream_constraints={
        "video": True,
        "audio": False,
    },
    rtc_configuration={
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]}
        ]
    },
)