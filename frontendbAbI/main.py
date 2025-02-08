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
import torch
from transformers import OwlViTProcessor, OwlViTForObjectDetection

import cv2
import numpy as np
from fastapi import Response

from nicegui import Client, app, core, run, ui
from datetime import datetime

# In case you don't have a webcam, this will provide a black placeholder image.
black_1px = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjYGBg+A8AAQQBAHAgZQsAAAAASUVORK5CYII='
placeholder = Response(content=base64.b64decode(black_1px.encode('ascii')), media_type='image/png')

# Initialize the processor and model
processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")
model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32")

def constructClassList(filename):
    file = open(filename, "r")
    outputList = []
    # Read each line one by one
    for line in file:
        cat = line.strip()
        if cat[0] in ["a", "e", "i", "o", "u"]:
            outputList.append("picture of an " + cat)  # .strip() to remove newline characters
        else:
            outputList.append(" picture of a " + cat)
    # Close the file
    file.close()
    return [outputList]

def is_overlapping(box1, box2):
    # Unpack the bounding boxes
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    # Check if there is an overlap
    if x1_min < x2_max and x1_max > x2_min and y1_min < y2_max and y1_max > y2_min:
        return True
    return False

text_labels = constructClassList("../OWL_VIT/Dangerous_Objects.txt")

def convert(frame: np.ndarray) -> bytes:
    """Converts a frame from OpenCV to a JPEG image.

    This is a free function (not in a class or inner-function),
    to allow run.cpu_bound to pickle it and send it to a separate process.
    """
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    # Process the image and perform object detection
    inputs = processor(text=text_labels, images=image, return_tensors="pt")
    outputs = model(**inputs)

        # Target image sizes (height, width) to rescale box predictions [batch_size, 2]
    target_sizes = torch.tensor([(image.height, image.width)])
    # Convert outputs (bounding boxes and class logits) to Pascal VOC format (xmin, ymin, xmax, ymax)
    results = processor.post_process_grounded_object_detection(
        outputs=outputs, target_sizes=target_sizes, threshold=0.1, text_labels=text_labels
    )
    # Retrieve predictions for the first image for the corresponding text queries
    result = results[0]
    boxes, scores, result_labels = result["boxes"], result["scores"], result["text_labels"]

    baby_box = None
    baby_score = 0
    crib_box = None
    crib_score = 0
    # Draw the bounding boxes and labels on the frame
    for box, score, text_label in zip(boxes, scores, result_labels):
        if score.item() >= .2 or 'crib' in text_label:
            if ("baby" in text_label or "infant" in text_label or "person" in text_label or "child" in text_label) and score.item() > baby_score:
                baby_box = box
                baby_score = score.item()
            if "crib" in text_label and score.item() > crib_score:
                crib_box = box
                crib_score = score.item()
            box = [round(i, 2) for i in box.tolist()]
            cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (255, 0, 0), 2)
            cv2.putText(frame, f"{text_label[14:]}: {round(score.item(), 3)}", (int(box[0]), int(box[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    if crib_box != None and baby_box != None:
        if not is_overlapping(crib_box, baby_box):
            cv2.putText(frame, "DANGER", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            print("DANGER")
        else:
            cv2.putText(frame, "SAFE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            print("SAFE")

    _, imencode_image = cv2.imencode('.jpg', frame)
    return imencode_image.tobytes()


def setup() -> None:
    # OpenCV is used to access the webcam.
    video_capture = cv2.VideoCapture(0)

    @app.get('/video/frame')
    # Thanks to FastAPI's `app.get` it is easy to create a web route which always provides the latest image from OpenCV.
    async def grab_video_frame() -> Response:
        if not video_capture.isOpened():
            return placeholder
        # The `video_capture.read` call is a blocking function.
        # So we run it in a separate thread (default executor) to avoid blocking the event loop.
        _, frame = await run.io_bound(video_capture.read)
        if frame is None:
            return placeholder
        # `convert` is a CPU-intensive function, so we run it in a separate process to avoid blocking the event loop and GIL.
        jpeg = await run.cpu_bound(convert, frame)
        return Response(content=jpeg, media_type='image/jpeg')

    # For non-flickering image updates and automatic bandwidth adaptation an interactive image is much better than `ui.image()`.
    video_image = ui.interactive_image().classes('w-full h-full')
    # A timer constantly updates the source of the image.
    # Because data from same paths is cached by the browser,
    # we must force an update by adding the current timestamp to the source.
    ui.timer(interval=0.1, callback=lambda: video_image.set_source(f'/video/frame?{time.time()}'))

    async def disconnect() -> None:
        """Disconnect all clients from current running server."""
        for client_id in Client.instances:
            await core.sio.disconnect(client_id)

    def handle_sigint(signum, frame) -> None:
        # `disconnect` is async, so it must be called from the event loop; we use `ui.timer` to do so.
        ui.timer(0.1, disconnect, once=True)
        # Delay the default handler to allow the disconnect to complete.
        ui.timer(1, lambda: signal.default_int_handler(signum, frame), once=True)

    async def cleanup() -> None:
        # This prevents ugly stack traces when auto-reloading on code change,
        # because otherwise disconnected clients try to reconnect to the newly started server.
        await disconnect()
        # Release the webcam hardware so it can be used by other applications again.
        video_capture.release()

    app.on_shutdown(cleanup)
    # We also need to disconnect clients when the app is stopped with Ctrl+C,
    # because otherwise they will keep requesting images which lead to unfinished subprocesses blocking the shutdown.
    signal.signal(signal.SIGINT, handle_sigint)


# All the setup is only done when the server starts. This avoids the webcam being accessed
# by the auto-reload main process (see https://github.com/zauberzeug/nicegui/discussions/2321).

# Function to load CSV data
# def load_text():
#     try:
#         with open("crying_log.txt", "r", encoding="utf-8") as file:
#             content = file.read()
#         text_area.set_value(content)  # Display content in textarea
#     except FileNotFoundError:
#         ui.notify("File not found!", level="error")

# ui.button("Load TXT File", on_click=load_text)

# text_area = ui.textarea(label="File Content", readonly=True).style("width: 100%; height: 300px;")


# def log_cry_event():
#     """Logs the current time when the baby cries."""
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     with open(LOG_FILE, "a") as f:
#         f.write(f"{timestamp}\n")  # Append timestamp to the log file
#     ui.notify(f"Baby cried at {timestamp}", color="red", position="top-right")
#     update_log_display()

# def read_log():
#     """Reads the log file and returns its contents."""
#     try:
#         with open(LOG_FILE, "r") as f:
#             return f.readlines()
#     except FileNotFoundError:
#         return ["No log entries yet."]

# def update_log_display():
#     """Updates the UI with the latest log contents."""
#     log_content.clear()
#     for line in read_log():
#         ui.label(line.strip()).style("font-size: 16px; margin-bottom: 5px;")

# with ui.card():
#     ui.label("Cry Log").style("font-size: 20px; font-weight: bold;")
#     log_content = ui.column()  # Placeholder for log entries
#     update_log_display()  # Populate log display on startup

def read_last_log_entry():
    """Reads the last entry from the crying_log.txt file."""
    try:
        with open("crying_log.txt", "r") as file:
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
    if sound:
        ui.run_javascript(f'playSound("{sound}");')
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

# Element('img') \
#     .props('src=logo2.png') \
#     .style('width: 200px; height: 200px; border: 1pt solid gray; object-fit:scale-down')

# Create the toolbar (hidden by default)
# toolbar = ui.column().style('position: absolute; top: 60px; left: 0; width: 200px; background-color: #f4f4f4; padding: 10px; border-radius: 5px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); display: none;')


# ui.button('Simulate Baby Crying', on_click=simulate_crying, color="#6a89a7").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; width: 100%; margin-bottom: 10px;')
# ui.button('Simulate Danger Zone Alert', on_click=simulate_danger, color="#6a89a7").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; width: 100%; margin-bottom: 10px;')
# ui.button('Simulate Motion Detection', on_click=simulate_motion, color="#6a89a7").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; width: 100%; margin-bottom: 10px;')
# ui.button('Clear Event Log', on_click=clear_log, color="gray").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; width: 100%; margin-bottom: 10px;')

# Toggle function for the toolbar
# def toggle_toolbar():
#     ui.run_javascript("""
#         let toolbar = document.getElementById('toolbar');
#         if (toolbar.style.display === 'none' || toolbar.style.display === '') {
#             toolbar.style.display = 'block';
#         } else {
#             toolbar.style.display = 'none';
#         }
#     """)

# menu_button.on('click', toggle_toolbar)

# UI Layout with background
# with ui.row().style('width: 85px; height: 85px; background-color: #c791db; padding: 10px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3); position: absolute; top: 10px; left: 20px; z-index: 9999;'):
#     ui.label('bAbI').style('font-family: "AmaticSC"; font-size: 30px; font-weight: bold; color: #FFF; text-align: center;')# Add a placeholder for the live camera feed (horizontal box)
# ui.image('https://app.brandmark.io/v3/#logo_data=%7B%22id%22%3A%22logo-5dfbea2a-c11e-416b-b5c1-b6bdd067cbea%22%2C%22layout%22%3A1%2C%22title%22%3A%22babi%22%2C%22titleFamily%22%3A%22Brandmark%20Serif%206%22%2C%22titleVariant%22%3A%22regular%22%2C%22titleColor%22%3A%5B%7B%22hex%22%3A%22%23c791db%22%2C%22location%22%3A0%7D%2C%7B%22hex%22%3A%22%23971efc%22%2C%22location%22%3A0.25%7D%2C%7B%22hex%22%3A%22%23971efc%22%2C%22location%22%3A0.5%7D%2C%7B%22hex%22%3A%22%23ddd3e4%22%2C%22location%22%3A0.75%7D%2C%7B%22hex%22%3A%22%23971efc%22%2C%22location%22%3A1%7D%5D%2C%22titleScale%22%3A2.5%2C%22titleLetterSpace%22%3A0%2C%22titleLineSpace%22%3A1.1%2C%22titleBoldness%22%3A0%2C%22titleX%22%3A0%2C%22titleY%22%3A0%2C%22titleAlign%22%3A%22center%22%2C%22slogan%22%3A%22%22%2C%22sloganFamily%22%3A%22Lora%22%2C%22sloganVariant%22%3A%22italic%22%2C%22sloganColor%22%3A%5B%7B%22hex%22%3A%22%23971efc%22%7D%5D%2C%22sloganScale%22%3A2.5%2C%22sloganLetterSpace%22%3A0%2C%22sloganLineSpace%22%3A1.1%2C%22sloganBoldness%22%3A0%2C%22sloganAlign%22%3A%22center%22%2C%22sloganX%22%3A0%2C%22sloganY%22%3A0%2C%22icon%22%3A%7B%22id%22%3A%2224381%22%2C%22type%22%3A%22noun%22%2C%22preview%22%3A%22https%3A%2F%2Fapp.brandmark.io%2Fnounpreview%2F24381.png%22%7D%2C%22showIcon%22%3Atrue%2C%22iconScale%22%3A1%2C%22iconColor%22%3A%5B%7B%22hex%22%3A%22%23971efc%22%7D%5D%2C%22iconContainer%22%3Anull%2C%22showIconContainer%22%3Afalse%2C%22iconContainerScale%22%3A1%2C%22iconContainerColor%22%3A%5B%7B%22hex%22%3A%22%23e2d3fc%22%7D%5D%2C%22iconSpace%22%3A1%2C%22iconX%22%3A0%2C%22iconY%22%3A0%2C%22nthChar%22%3A0%2C%22container%22%3Anull%2C%22showContainer%22%3Afalse%2C%22containerScale%22%3A1%2C%22containerColor%22%3A%5B%7B%22hex%22%3A%22%23e2d3fc%22%7D%5D%2C%22containerX%22%3A0%2C%22containerY%22%3A0%2C%22backgroundColor%22%3A%5B%7B%22hex%22%3A%22%23fcfcfc%22%7D%5D%2C%22palette%22%3A%5B%22%23fcfcfc%22%2C%22%23971efc%22%2C%22%239f3ffc%22%2C%22%23a760fc%22%2C%22%23af82fd%22%5D%2C%22keywords%22%3A%5B%22baby%22%2C%22kindness%22%2C%22watchful%22%2C%22soft%22%2C%22caring%22%5D%7D')
camera_placeholder = ui.row().style('width: 100%; height: 400px; background-color: #dcdcdc; margin-top: 100px; margin-bottom: 20px; border-radius: 15px; justify-content: center; align-items: center;')
with camera_placeholder:
    ui.label("🔴 Live Camera Feed Placeholder").style('font-size: 24px; font-weight: bold; color: #333;')

# Buttons for Simulated Events with improved style
with ui.row().style('gap: 15px; justify-content: center; margin-top: 40px;'):
    ui.button('Simulate Baby Crying', on_click=simulate_crying, color="#c791db").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
    ui.button('Simulate Danger Zone Alert', on_click=simulate_danger, color="#c791db").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
    ui.button('Simulate Motion Detection', on_click=simulate_motion, color="#c791db").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')
    ui.button('Clear Event Log', on_click=clear_log, color="gray").style('font-size: 18px; color: #FFF; border-radius: 12px; padding: 10px 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);')

# Start the app
ui.run()