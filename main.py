import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import threading
import json
import keyboard # New hotkey library
import sounddevice as sd
import whisper
import pyperclip
import numpy as np
import scipy.io.wavfile as wav
import io
import soundfile as sf # Ensure soundfile is imported
from scipy.signal import resample_poly # New import for resampling
import tkinter as tk # New import for pop-up
import queue # New import for inter-thread communication

# --- Configuration and State ---
def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

config = load_config()
HOTKEY = config.get("hotkey", "f8") # Ensure F8 is set
MODEL_NAME = config.get("whisper_model", "base")

is_recording = False
recording_data = []
model = None
stream = None

# Tkinter pop-up window variables
popup_root = None
popup_label = None
popup_queue = queue.Queue() # Queue for Tkinter commands
pulse_direction = 1 # 1 for increasing, -1 for decreasing
pulse_value = 0 # Current pulse value (0-100)

# --- Icon Creation ---
def create_image(color1, color2):
    image = Image.new('RGB', (64, 64), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (32, 0, 64, 32),
        fill=color2)
    dc.rectangle(
        (0, 32, 32, 64),
        fill=color2)
    return image

# --- Pop-up Window Functions ---
def create_popup_window():
    global popup_root, popup_label
    popup_root = tk.Tk()
    popup_root.withdraw() # Hide initially
    popup_root.overrideredirect(True) # Remove window decorations
    popup_root.attributes('-topmost', True) # Always on top
    popup_root.attributes('-alpha', 0.9) # Slightly less transparent

    # Position the window in the bottom-right corner
    screen_width = popup_root.winfo_screenwidth()
    screen_height = popup_root.winfo_screenheight()
    window_width = 250 # Increased width
    window_height = 60 # Increased height
    padding = 20 # Margin from screen edges
    x = screen_width - window_width - padding
    y = screen_height - window_height - padding
    popup_root.geometry(f'{window_width}x{window_height}+{x}+{y}')

    popup_label = tk.Label(popup_root, text="Recording...", bg="#21130d", fg="#f0c674", font=("Arial", 18, "bold")) # Custom colors
    popup_label.pack(expand=True, fill="both")

    # Start checking the queue periodically
    popup_root.after(100, check_popup_queue)
    # Start pulsing animation
    popup_root.after(40, pulse_text_color) # Slower pulse

def check_popup_queue():
    try:
        while True:
            command = popup_queue.get_nowait()
            if command == "show":
                popup_root.deiconify()
            elif command == "hide":
                popup_root.withdraw()
            elif command == "destroy":
                popup_root.destroy()
                break # Exit the loop and thread
    except queue.Empty:
        pass # No commands in queue
    finally:
        if popup_root and popup_root.winfo_exists(): # Only reschedule if window still exists
            popup_root.after(100, check_popup_queue)

def pulse_text_color():
    global pulse_direction, pulse_value
    if not popup_root or not popup_root.winfo_exists():
        return

    # Adjust pulse value
    pulse_value += pulse_direction * 7 # Change by 7 each step for smoother fade
    if pulse_value >= 100:
        pulse_value = 100
        pulse_direction = -1
    elif pulse_value <= 0:
        pulse_value = 0
        pulse_direction = 1

    # Calculate new color based on original text color (#f0c674)
    # Convert hex to RGB
    original_r = int("f0", 16)
    original_g = int("c6", 16)
    original_b = int("74", 16)

    # Scale RGB components based on pulse_value
    scaled_r = int(original_r * (pulse_value / 100.0))
    scaled_g = int(original_g * (pulse_value / 100.0))
    scaled_b = int(original_b * (pulse_value / 100.0))

    new_color = f"#{scaled_r:02x}{scaled_g:02x}{scaled_b:02x}"
    popup_label.config(fg=new_color)

    # Reschedule the pulse
    popup_root.after(40, pulse_text_color) # Slower pulse

def run_popup_loop():
    create_popup_window()
    popup_root.mainloop()

# --- Core Application Logic ---
def start_recording():
    global is_recording, recording_data
    if not is_recording:
        print("DEBUG: Hotkey pressed. Starting recording...")
        is_recording = True
        recording_data = []
        # Update icon to indicate recording
        icon.icon = create_image('red', 'white')
        # Send command to show pop-up
        popup_queue.put("show")

def stop_recording_and_transcribe():
    global is_recording
    if is_recording:
        print("DEBUG: Hotkey released. Stopping recording...")
        is_recording = False
        # Update icon to normal state
        icon.icon = create_image('black', 'white')
        # Send command to hide pop-up
        popup_queue.put("hide")

        # Process and transcribe audio
        if recording_data:
            print("DEBUG: Processing audio data...")
            # Convert to numpy array
            audio_data = np.concatenate(recording_data, axis=0)
            
            # Save to a temporary in-memory wav file
            # Use the actual recording samplerate for writing the WAV
            recording_samplerate = 48000 # User's mic records at 48000 Hz
            byte_io = io.BytesIO()
            wav.write(byte_io, recording_samplerate, audio_data)
            byte_io.seek(0)

            # Read the BytesIO object into a NumPy array using soundfile
            audio_np, current_samplerate = sf.read(byte_io)

            # Convert audio data to float32, as Whisper expects
            audio_np = audio_np.astype(np.float32)

            # Resample to 16000 Hz if necessary
            if current_samplerate != 16000:
                print(f"DEBUG: Resampling audio from {current_samplerate} Hz to 16000 Hz...")
                audio_np = resample_poly(audio_np, 16000, current_samplerate)

            # Transcribe
            print("DEBUG: Transcribing... (This may take a moment)")
            try:
                result = model.transcribe(audio_np, fp16=False) # Pass NumPy array
                transcribed_text = result["text"]
                print(f"SUCCESS: Transcription complete. Text written to active window.")
                print(f"Text: {transcribed_text}")

                # Write to active window
                keyboard.write(transcribed_text)
            except Exception as e:
                print(f"ERROR: An error occurred during transcription: {e}")
        else:
            print("DEBUG: No audio data recorded.")

# --- Hotkey Handling ---
# The keyboard library handles press and release events differently.
# We'll use a single hotkey registration that triggers on press,
# and then wait for the release within the recording function.

# --- Audio Recording ---
def callback(indata, frames, time, status):
    if is_recording:
        recording_data.append(indata.copy())

# --- System Tray ---
def on_quit(icon, item):
    print("DEBUG: Quit requested. Shutting down...")
    # Stop the audio stream
    if stream:
        stream.stop()
        stream.close()
    # Send command to destroy pop-up window
    popup_queue.put("destroy")
    icon.stop()

icon = pystray.Icon(
    'whisper_stt',
    icon=create_image('black', 'white'),
    title='Whisper STT',
    menu=pystray.Menu(
        item('Quit', on_quit)
    )
)

# --- Main Execution ---
def main():
    global model, stream
    print("DEBUG: Loading Whisper model...")
    model = whisper.load_model(MODEL_NAME)
    print("SUCCESS: Whisper model loaded.")

    # Start Tkinter pop-up window in a separate thread
    popup_thread = threading.Thread(target=run_popup_loop, daemon=True)
    popup_thread.start()

    # Setup audio stream
    print("DEBUG: Starting audio stream...")
    # Use 48000 Hz for recording as per user's microphone
    stream = sd.InputStream(callback=callback, samplerate=48000, channels=1)
    stream.start()
    print("SUCCESS: Audio stream started.")

    # Register hotkey using the keyboard library
    print(f"DEBUG: Registering hotkey: {HOTKEY}")
    keyboard.add_hotkey(HOTKEY, start_recording, suppress=True)
    keyboard.add_hotkey(HOTKEY, stop_recording_and_transcribe, suppress=True, trigger_on_release=True)
    print("SUCCESS: Hotkey registered.")

    # Run the system tray icon on the main thread (this is a blocking call)
    icon.run()

if __name__ == "__main__":
    main()