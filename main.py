import sys
import threading
import time
import pyaudio
import wave
import cv2

from audio import live_segmentation as ap

# Audio sampling task
def audio_sampling():
    ap.segmentMake(5)

# Audio processing task (example: simple print statement for now)
def audio_processing():
    while True:
        # Simulate audio processing (e.g., analyzing the saved wav file)
        print("Processing audio...")
        time.sleep(5)  # Placeholder for processing time

# Image processing task
def image_processing():
    cap = cv2.VideoCapture(0)  # Capture from webcam

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Webcam Feed", frame)
        
        # Add your image processing logic here
        # (e.g., detecting movement, baby posture, etc.)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Create threads for each task
audio_sampling_thread = threading.Thread(target=audio_sampling)
audio_processing_thread = threading.Thread(target=audio_processing)
image_processing_thread = threading.Thread(target=image_processing)

# Start the threads
audio_sampling_thread.start()
audio_processing_thread.start()
image_processing_thread.start()


# Wait for all threads to finish
audio_sampling_thread.join()
audio_processing_thread.join()
image_processing_thread.join()
