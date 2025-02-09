import pyaudio
import wave
import os

def segmentMake(segmentLength, stop_flag):
    # Audio configuration
    CHUNK = 1024  # Block size
    FORMAT = pyaudio.paInt16  # Format
    CHANNELS = 1  # Mono audio
    RATE = 48000  # Sample rate (Hz)
    RECORD_SECONDS = segmentLength  # Length of each recording in seconds
    OUTPUT_FOLDER = "Segments"  # Folder where .wav files will be saved
    i = 0  # File counter

    # Create the output folder if it doesn't exist
    script_directory = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
    output_path = os.path.join(script_directory, OUTPUT_FOLDER)  # Build path to output folder

    for filename in os.listdir(output_path):
        file_path = os.path.join(output_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

    if not os.path.exists(output_path):
        os.makedirs(output_path)  # Create the folder if it doesn't exist

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open stream for recording
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    # print("Recording...")

    # print("Initial Stop Flag in Audio Segmentation", stop_flag())

    try:
        while not stop_flag():
            # print("Recording Segment")
            frames = []

            # Read and store audio data
            for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

            # Save the audio data to a .wav file in the output folder
            output_file = os.path.join(output_path, f"seg_{i}.wav")
            wf = wave.open(output_file, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()

            print(f"Saved {output_file}")
            i += 1

    finally:
        print(f"In Audio Segmentation, stop flag is: {stop_flag()}")
        print("Recording stopped")
        stream.stop_stream()
        stream.close()
        p.terminate()
        # Clean up
