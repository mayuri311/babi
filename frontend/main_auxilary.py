import cv2
import numpy as np
from fastapi import Response
from contextlib import asynccontextmanager

from nicegui import Client, app, core, run, ui
from nicegui.events import ValueChangeEventArguments
from datetime import datetime

import sys
import threading
import time
import pyaudio
import wave
import cv2
import os
from fastapi import Response, status

from audio import live_segmentation as ap
import threadedAudioProcessing as tap

# Comment out if running without OwlViT
from webcam_detection import detect_boxes


video_capture = cv2.VideoCapture(0)

def convert(frame: np.ndarray) -> bytes:
    """Converts a frame from OpenCV to a JPEG image."""
    _, imencode_image = cv2.imencode('.jpg', frame)
    return imencode_image.tobytes()

async def owl_vit_detection(value):
    if not video_capture.isOpened():
        return placeholder
    # The `video_capture.read` call is a blocking function.
    # So we run it in a separate thread (default executor) to avoid blocking the event loop.
    _, frame = await run.io_bound(video_capture.read)
    if frame is None:
        return placeholder

    # Comment out to run without OwlViT
    safety = detect_boxes(frame)
    return safety

# async def update_image(value):
#     # Start the threads
#     audio_sampling_thread.start()
#     audio_processing_thread.start()

def thereallyjankfunction():
    # OpenCV is used to access the webcam.

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
        
    @asynccontextmanager
    async def shutdown_event():
    # Release the webcam hardware so it can be used by other applications again.
        video_capture.release()
    

thereallyjankfunction()

# stop_threads = False
# audio_segment_length = 10


# # Audio sampling task
# def audio_sampling():
#     global stop_threads
#     global audio_segment_length
#     ap.segmentMake(audio_segment_length, lambda: stop_threads)

# # Audio processing task (example: simple print statement for now)
# def audio_processing():
#     global stop_threads
#     global audio_segment_length

#     wav_path = os.path.join(os.getcwd(), "audio/Segments")

#     while not stop_threads:
#         # Simulate audio processing (e.g., analyzing the saved wav file)

#         tap.processTopAudioFile(wav_path)
#         print("Processing audio...")

#         time.sleep(1)  # Placeholder for processing time

# # Image processing task
# # def image_processing():
# #     global stop_threads

# #     thereallyjankfunction()

# # Create threads for each task
# audio_sampling_thread = threading.Thread(target=audio_sampling)
# audio_processing_thread = threading.Thread(target=audio_processing)
# # image_processing_thread = threading.Thread(target=image_processing)

# # Start the threads
# audio_sampling_thread.start()
# audio_processing_thread.start()
# # image_processing_thread.start()
# update_image()
# print("here")
# thereallyjankfunction()
# # try:
# #     # Main loop to keep the program running until interrupted
# #     while True:
# #         time.sleep(1)
# # except KeyboardInterrupt:
# #     # When Ctrl+C is pressed, set the stop flag
# #     stop_threads = True
# #     print("Stopping all tasks...")

# # Wait for all threads to finish
# audio_sampling_thread.join()
# audio_processing_thread.join()
# #image_processing_thread.join()

# print("Tasks quit successfully")