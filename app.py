import streamlit as st
import subprocess
import sys

st.set_page_config(
    page_title="AirDraw",
    page_icon="✍️",
    layout="wide"
)

st.title("✍️ AirDraw")
st.write("Draw in the air using your webcam and hand gestures.")

if st.button("Start AirDraw"):
    st.success("Starting AirDraw...")

    try:
        subprocess.Popen([sys.executable, "-m", "src.main"])
        st.info("AirDraw has been launched. Check the webcam window.")
    except Exception as e:
        st.error(f"Error: {e}")