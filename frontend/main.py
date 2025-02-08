from nicegui import ui
import time
from fontTools.ttLib import TTFont
from PIL import ImageFont
from nicegui.element import Element
import base64
import signal
import time
import sys
from PIL import Image
# import torch
# from transformers import OwlViTProcessor, OwlViTForObjectDetection
import cv2
import numpy as np
from fastapi import Response
import main_auxilary

import cry_plotter_test as cryplot

from nicegui import Client, app, core, run, ui
from datetime import datetime

# In case you don't have a webcam, this will provide a black placeholder image.
black_1px = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjYGBg+A8AAQQBAHAgZQsAAAAASUVORK5CYII='
placeholder = Response(content=base64.b64decode(black_1px.encode('ascii')), media_type='image/png')


# def is_overlapping(box1, box2):
#     # Unpack the bounding boxes
#     x1_min, y1_min, x1_max, y1_max = box1
#     x2_min, y2_min, x2_max, y2_max = box2
#     # Check if there is an overlap
#     if x1_min < x2_max and x1_max > x2_min and y1_min < y2_max and y1_max > y2_min:
#         return True
#     return False

# text_labels = constructClassList("../OWL_VIT/Dangerous_Objects.txt")


def setup() -> None:

    image_frame = 'http://172.26.119.17:8080/video/frame'

    # For non-flickering image updates and automatic bandwidth adaptation an interactive image is much better than `ui.image()`.
    with ui.column().style('gap: 20px; justify-content: center; align-items: center;'):

        # Webcam feed at the top
        video_image = ui.interactive_image().classes('w-full h-full')
        video_image.style('width: 960px; height: 540px; margin_top: 20px; border-radius: 15px; justify-content: center; align-items: center;')

        # Timer to update the webcam feed
        ui.timer(interval=0.1, callback=lambda: video_image.set_source(f'/video/frame?{time.time()}'))

        # Buttons below the webcam feed
        ui.button('Simulate Baby Crying', on_click=simulate_crying, color="#c791db").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
        ui.button('Simulate Danger Zone Alert', on_click=simulate_danger, color="#c791db").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
        ui.button('Simulate Motion Detection', on_click=simulate_motion, color="#c791db").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
        ui.button('Clear Event Log', on_click=clear_log, color="gray").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')

        cryplot.plotCryLogGraph()

        ui.image('crying_detections.png').style('width: 960px; height: 540px; margin_top: 20px; border-radius: 15px; justify-content: center; align-items: center;')
    async def disconnect() -> None:
        """Disconnect all clients from current running server."""
        for client_id in Client.instances:
            await core.sio.disconnect(client_id)

    def handle_sigint(signum, frame) -> None:
        # `disconnect` is async, so it must be called from the event loop; we use `ui.timer` to do so.
        ui.timer(0.1, disconnect, once=True)
        # Delay the default handler to allow the disconnect to complete.
        ui.timer(1, lambda: signal.default_int_handler(signum, frame), once=True)


    app.on_shutdown(main_auxiliary.shutdown_event)
    signal.signal(signal.SIGINT, handle_sigint)
    # We also need to disconnect clients when the app is stopped with Ctrl+C,
    # because otherwise they will keep requesting images which lead to unfinished subprocesses blocking the shutdown.
    signal.signal(signal.SIGINT, handle_sigint)


# All the setup is only done when the server starts. This avoids the webcam being accessed
# by the auto-reload main process (see https://github.com/zauberzeug/nicegui/discussions/2321).

# Function to load CSV data

def read_last_log_entry():
    """Reads the last entry from the crying_log.txt file."""
    try:
        with open("/frontend/crying_log.txt", "r") as file:
            lines = file.readlines()
            if lines:
                return lines[-1].strip()  # Get the last line (most recent cry)
            else:
                return "No entries yet."
    except FileNotFoundError:
        return "Log file not found."

app.on_startup(setup)

ui.add_css(f"""
@font-face {{
    font-family: 'AmaticSC';
    src: url('/static/font-amatic-sc-0.0.4/font_amatic_sc/files/AmaticSC-Bold.ttf');
}}
""")


# Create a placeholder for the event log
event_log = ui.column().style('max-height: 200px; overflow-y: auto; position: absolute; bottom: 40px; left: 20px; right: 20px;')

def log_event(message, color="blue", timestamp=None):
    """Logs an event in the UI."""
    timestamp = read_last_log_entry()
    message = f"{message} - at: {timestamp}"
    with event_log:
        ui.label(message).style(f'background-color: rgba(230, 230, 230, 0.7); color: rgba(100, 100, 100, 1); font-family: "AmaticSC"; font-size: 16px; margin-bottom: 8px; padding: 10px 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
    # if sound:
    #     ui.run_javascript(f'playSound("{sound}");')
def simulate_crying():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current timestamp
    log_event("🚨Baby is crying!", "red")
    ui.notify("Baby is crying!", color= "#red", position="top-right")  # Top-right position for notification


def simulate_danger():
    log_event("⚠️ Baby near a danger zone!", "orange")
    ui.notify("Danger detected!", color="orange", position="top-right")  # Top-right position for notification

def simulate_motion():
    log_event("📹 Motion detected!", "green")
    ui.notify("Motion detected!", color="green", position="top-right")  # Top-right position for notification

def clear_log():
    """Clears the event log."""
    event_log.clear()

# Create a menu bar (top left corner)
ui.row().style('width: 100%; height: 100px; position: absolute; top: 0; left: 0; background-color: #ddd3e4; padding: 10px; border-radius: 5px; z-index: 1;')
    # menu_button = ui.button('☰ Menu').style('font-size: 18px; color: white; background-color: #333; border: none;')

ui.image('logo2.png').style('width: 175px; height: 55px; position: absolute; top: 60; left: 0; background-color: #ddd3e4; padding: 10px; border-radius: 5px; z-index: 1;')


# UI Layout with background
# with ui.row().style('width: 85px; height: 85px; background-color: #c791db; padding: 10px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); position: absolute; top: 10px; left: 20px; z-index: 9999;'):
#     ui.label('bAbI').style('font-family: "AmaticSC"; font-size: 30px; font-weight: bold; color: #FFF; text-align: center;')# Add a placeholder for the live camera feed (horizontal box)
# ui.image('https://app.brandmark.io/v3/#logo_data=%7B%22id%22%3A%22logo-5dfbea2a-c11e-416b-b5c1-b6bdd067cbea%22%2C%22layout%22%3A1%2C%22title%22%3A%22babi%22%2C%22titleFamily%22%3A%22Brandmark%20Serif%206%22%2C%22titleVariant%22%3A%22regular%22%2C%22titleColor%22%3A%5B%7B%22hex%22%3A%22%23c791db%22%2C%22location%22%3A0%7D%2C%7B%22hex%22%3A%22%23971efc%22%2C%22location%22%3A0.25%7D%2C%7B%22hex%22%3A%22%23971efc%22%2C%22location%22%3A0.5%7D%2C%7B%22hex%22%3A%22%23ddd3e4%22%2C%22location%22%3A0.75%7D%2C%7B%22hex%22%3A%22%23971efc%22%2C%22location%22%3A1%7D%5D%2C%22titleScale%22%3A2.5%2C%22titleLetterSpace%22%3A0%2C%22titleLineSpace%22%3A1.1%2C%22titleBoldness%22%3A0%2C%22titleX%22%3A0%2C%22titleY%22%3A0%2C%22titleAlign%22%3A%22center%22%2C%22slogan%22%3A%22%22%2C%22sloganFamily%22%3A%22Lora%22%2C%22sloganVariant%22%3A%22italic%22%2C%22sloganColor%22%3A%5B%7B%22hex%22%3A%22%23971efc%22%7D%5D%2C%22sloganScale%22%3A2.5%2C%22sloganLetterSpace%22%3A0%2C%22sloganLineSpace%22%3A1.1%2C%22sloganBoldness%22%3A0%2C%22sloganAlign%22%3A%22center%22%2C%22sloganX%22%3A0%2C%22sloganY%22%3A0%2C%22icon%22%3A%7B%22id%22%3A%2224381%22%2C%22type%22%3A%22noun%22%2C%22preview%22%3A%22https%3A%2F%2Fapp.brandmark.io%2Fnounpreview%2F24381.png%22%7D%2C%22showIcon%22%3Atrue%2C%22iconScale%22%3A1%2C%22iconColor%22%3A%5B%7B%22hex%22%3A%22%23971efc%22%7D%5D%2C%22iconContainer%22%3Anull%2C%22showIconContainer%22%3Afalse%2C%22iconContainerScale%22%3A1%2C%22iconContainerColor%22%3A%5B%7B%22hex%22%3A%22%23e2d3fc%22%7D%5D%2C%22iconSpace%22%3A1%2C%22iconX%22%3A0%2C%22iconY%22%3A0%2C%22nthChar%22%3A0%2C%22container%22%3Anull%2C%22showContainer%22%3Afalse%2C%22containerScale%22%3A1%2C%22containerColor%22%3A%5B%7B%22hex%22%3A%22%23e2d3fc%22%7D%5D%2C%22containerX%22%3A0%2C%22containerY%22%3A0%2C%22backgroundColor%22%3A%5B%7B%22hex%22%3A%22%23fcfcfc%22%7D%5D%2C%22palette%22%3A%5B%22%23fcfcfc%22%2C%22%23971efc%22%2C%22%239f3ffc%22%2C%22%23a760fc%22%2C%22%23af82fd%22%5D%2C%22keywords%22%3A%5B%22baby%22%2C%22kindness%22%2C%22watchful%22%2C%22soft%22%2C%22caring%22%5D%7D')
# camera_placeholder = ui.row().style('width: 100%; height: 400px; background-color: #dcdcdc; margin-top: 100px; margin-bottom: 20px; border-radius: 15px; justify-content: center; align-items: center;')
# with camera_placeholder:
#     ui.label("🔴 Live Camera Feed Placeholder").style('font-size: 24px; font-weight: bold; color: #333;')

# Buttons for Simulated Events with improved style
# with ui.column().style('gap: 15px; justify-content: center; margin-top: 20px;'):
#     ui.button('Simulate Baby Crying', on_click=simulate_crying, color="#c791db").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
#     ui.button('Simulate Danger Zone Alert', on_click=simulate_danger, color="#c791db").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
#     ui.button('Simulate Motion Detection', on_click=simulate_motion, color="#c791db").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
#     ui.button('Clear Event Log', on_click=clear_log, color="gray").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')

# Start the app
ui.run()