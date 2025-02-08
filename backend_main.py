import sys
import threading
import time
import pyaudio
import wave
import cv2
import os


from audio import live_segmentation as ap
import threadedAudioProcessing as tap

stop_threads = False
audio_segment_length = 10

# Audio sampling task
def audio_sampling():
    global stop_threads
    global audio_segment_length
    ap.segmentMake(audio_segment_length, lambda: stop_threads)

# Audio processing task (example: simple print statement for now)
def audio_processing():
    global stop_threads
    global audio_segment_length

    wav_path = os.path.join(os.getcwd(), "audio/Segments")

    while not stop_threads:
        # Simulate audio processing (e.g., analyzing the saved wav file)

        tap.processTopAudioFile(wav_path)
        print("Processing audio...")

        time.sleep(1)  # Placeholder for processing time

# Image processing task
def image_processing():
    global stop_threads

    cap = cv2.VideoCapture(0)  # Capture from webcam

    while not stop_threads:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Webcam Feed", frame)
        
        # Add your image processing logic here
        # (e.g., detecting movement, baby posture, etc.)

        if cv2.waitKey(1) & 0xFF == ord('q') or stop_threads:
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

try:
    # Main loop to keep the program running until interrupted
    while True:
        time.sleep(1)
        print(stop_threads)
except KeyboardInterrupt:
    # When Ctrl+C is pressed, set the stop flag
    stop_threads = True
    print("Stopping all tasks...")

# Wait for all threads to finish
audio_sampling_thread.join()
audio_processing_thread.join()
image_processing_thread.join()

print("Tasks quit successfully")