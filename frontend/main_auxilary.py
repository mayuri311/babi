import cv2
import numpy as np
from fastapi import Response
from contextlib import asynccontextmanager

from nicegui import Client, app, core, run, ui
from nicegui.events import ValueChangeEventArguments
from datetime import datetime
from webcam_detection import detect_boxes


video_capture = cv2.VideoCapture(0)

def convert(frame: np.ndarray) -> bytes:
    """Converts a frame from OpenCV to a JPEG image."""
    _, imencode_image = cv2.imencode('.jpg', frame)
    return imencode_image.tobytes()

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
        frame =  detect_boxes(frame)
        jpeg = await run.cpu_bound(convert, frame)
        return Response(content=jpeg, media_type='image/jpeg')
    
    @app.get('/cryinglog')
    async def cryinglog():
        with open("cryinglog.txt", "r") as f:
            lines = f.readlines()
        return lines
        
    
    @asynccontextmanager
    async def shutdown_event():
    # Release the webcam hardware so it can be used by other applications again.
        video_capture.release()
    
thereallyjankfunction()