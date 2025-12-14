import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw, ImageGrab
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
import time # For sleep in monitoring thread
import os # New import for path handling
import sys # New import for path handling
import requests # New import for Ollama API
from datetime import datetime # New import for screenshot naming

# --- Helper function for PyInstaller path handling ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Configuration and State ---
def load_config():
    # Use resource_path to find config.json
    with open(resource_path("config.json"), "r") as f:
        return json.load(f)

def save_config(new_config):
    # Use resource_path to find config.json
    with open(resource_path("config.json"), "w") as f:
        json.dump(new_config, f, indent=2)

config = load_config()
HOTKEY = config.get("hotkey", "ctrl+shift+space") # Ensure F8 is set
MODEL_NAME = config.get("whisper_model", "base")

# AI Assisted Writing Configuration
AI_CONFIG = config.get("ai_assisted_writing", {})
AI_ENABLED = AI_CONFIG.get("enabled", False)
AI_MODEL = AI_CONFIG.get("model", "qwen2.5-vl")
AI_NUM_CTX = AI_CONFIG.get("num_ctx", 8192)
AI_SCREENSHOT_QUALITY = AI_CONFIG.get("screenshot_quality", 90)
AI_MAX_SCREENSHOTS = AI_CONFIG.get("max_screenshots", 20)
AI_HOTSTART = AI_CONFIG.get("hotstart", True)

is_recording = False
recording_data = []
model = None
stream = None
is_hotkey_held = False # New flag to track hotkey state

# Dynamically get the default input device's sample rate at module load time
device_info = sd.query_devices(None, 'input') # None for default device
input_samplerate = int(device_info['default_samplerate'])
print(f"DEBUG: Detected microphone sample rate: {input_samplerate} Hz (at module load)")

# Tkinter pop-up window variables
popup_root = None
popup_label = None
popup_queue = queue.Queue() # Queue for Tkinter commands
pulse_direction = 1 # 1 for increasing, -1 for decreasing
pulse_value = 0 # Current pulse value (0-100)

# Hotkey config window variables
hotkey_config_root = None
hotkey_label = None
save_hotkey_button = None # New: Save button
cancel_hotkey_button = None # New: Cancel button
is_capturing_hotkey = False # New: State for hotkey capture
captured_hotkey_string = "" # New: Stores the captured hotkey

# Global variables for main hotkey handles
main_hotkey_press_handle = None

# --- Icon Creation ---
# No need for create_image function, as we'll load directly from PNG
# Global variables for system tray icons
base_icon_image = Image.open(resource_path("systemicon.png")) # Load icon using resource_path

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

    popup_label = tk.Label(popup_root, text="Recording...", bg="#2c3232", fg="#64dddd", font=("Arial", 18, "bold")) # Custom colors
    popup_label.pack(expand=True, fill="both")

    # Start checking the queue periodically
    popup_root.after(100, check_popup_queue)
    # Start pulsing animation
    popup_root.after(40, pulse_text_color) # Slower pulse

def check_popup_queue():
    command = None # Initialize command to None
    try:
        while True:
            command = popup_queue.get_nowait()
            if command == "show":
                popup_root.deiconify()
            elif command == "hide":
                popup_root.withdraw()
            elif command == "ai_processing":
                if popup_root and popup_root.winfo_exists():
                    popup_label.config(text="Processing with AI...")
            elif command == "destroy":
                popup_root.destroy()
                break # Exit the loop and thread
    except queue.Empty:
        pass # No commands in queue
    finally:
        # Only reschedule if window still exists AND we haven't received a destroy command
        if popup_root and popup_root.winfo_exists() and command != "destroy":
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

    # Calculate new color based on original text color (#64dddd)
    # Convert hex to RGB
    original_r = int("64", 16)
    original_g = int("dd", 16)
    original_b = int("dd", 16)

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

# --- AI Assisted Writing Functions ---
def capture_screenshot():
    """Capture full screen as high-quality PNG"""
    try:
        screenshot = ImageGrab.grab()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG', quality=AI_SCREENSHOT_QUALITY)
        return img_byte_arr.getvalue()
    except Exception as e:
        print(f"ERROR: Failed to capture screenshot: {e}")
        return None

def manage_screenshots():
    """Manage screenshot retention - keep only last AI_MAX_SCREENSHOTS"""
    screenshots_dir = resource_path("screenshots")
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    
    # Get all screenshot files sorted by creation time
    files = [os.path.join(screenshots_dir, f) for f in os.listdir(screenshots_dir)
             if f.endswith('.png')]
    files.sort(key=lambda x: os.path.getctime(x))
    
    # Delete oldest files if we exceed the limit
    while len(files) > AI_MAX_SCREENSHOTS:
        try:
            os.remove(files[0])
            files.pop(0)
        except Exception as e:
            print(f"ERROR: Failed to delete old screenshot: {e}")
            break

def save_screenshot(screenshot_bytes):
    """Save screenshot to disk for debugging/retention"""
    if not AI_CONFIG.get("save_screenshots", False):
        return
    
    try:
        screenshots_dir = resource_path("screenshots")
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
        
        with open(filename, 'wb') as f:
            f.write(screenshot_bytes)
        
        # Manage screenshot retention
        manage_screenshots()
    except Exception as e:
        print(f"ERROR: Failed to save screenshot: {e}")

def initialize_ai_model():
    """Initialize the AI model if hotstart is enabled"""
    if not AI_ENABLED or not AI_HOTSTART:
        return False
    
    try:
        # Send a minimal request to warm up the model
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": AI_MODEL,
                "prompt": "Initializing model...",
                "stream": False
            },
            timeout=30
        )
        print(f"SUCCESS: AI model {AI_MODEL} initialized")
        return True
    except Exception as e:
        print(f"WARNING: AI model initialization failed: {e}")
        print("AI features will be disabled")
        return False

def enhance_text_with_ai(original_text, screenshot_bytes):
    """Send text and screenshot to Ollama for context-aware enhancement"""
    try:
        # Update popup to show AI processing
        popup_queue.put("ai_processing")
        
        prompt = f"""
        Analyze the attached screenshot and the following user text: '{original_text}'
        
        1. PLATFORM ANALYSIS:
        - Identify the application/platform shown in the screenshot
        - Determine if this is formal (email, document) or informal (chat, social media)
        - Note any specific platform conventions
        
        2. CONTEXT ANALYSIS:
        - Extract any previous messages or text visible in the screenshot
        - Identify what the user is replying to or continuing
        - Note any conversation history or thread context
        
        3. TEXT ENHANCEMENT:
        - Preserve the exact meaning of the user's spoken text
        - Improve sentence structure and grammar
        - Adjust vocabulary to match the platform and context
        - Ensure coherence with any previous text
        - Return ONLY the enhanced text, no explanations or markings
        
        Enhanced text:
        """
        
        files = {'image': ('screenshot.png', screenshot_bytes, 'image/png')}
        data = {
            'model': AI_MODEL,
            'prompt': prompt,
            'num_ctx': AI_NUM_CTX,
            'stream': False
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            files=files,
            data=data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', original_text)
        else:
            print(f"WARNING: AI processing failed with status {response.status_code}")
            return original_text
            
    except Exception as e:
        print(f"ERROR: AI processing failed: {e}")
        return original_text

# --- Hotkey Configuration Window Functions ---
def show_hotkey_config_window():
    global hotkey_config_root, hotkey_label, save_hotkey_button, cancel_hotkey_button, HOTKEY, is_capturing_hotkey

    if hotkey_config_root and hotkey_config_root.winfo_exists():
        hotkey_config_root.lift() # Bring to front if already open
        return

    hotkey_config_root = tk.Toplevel()
    hotkey_config_root.title("Configure Hotkey")
    hotkey_config_root.geometry("300x200") # Increased height for new buttons
    hotkey_config_root.attributes('-topmost', True)
    hotkey_config_root.protocol("WM_DELETE_WINDOW", on_hotkey_config_close) # Handle window close

    tk.Label(hotkey_config_root, text="Current Hotkey:").pack(pady=5)
    hotkey_label = tk.Label(hotkey_config_root, text=HOTKEY, font=("Arial", 12, "bold"))
    hotkey_label.pack(pady=5)

    set_button = tk.Button(hotkey_config_root, text="Set New Hotkey", command=start_hotkey_capture)
    set_button.pack(pady=10)

    save_hotkey_button = tk.Button(hotkey_config_root, text="Save Hotkey", command=save_new_hotkey, state=tk.DISABLED) # Initially disabled
    save_hotkey_button.pack(pady=5)

    cancel_hotkey_button = tk.Button(hotkey_config_root, text="Cancel", command=on_hotkey_config_close)
    cancel_hotkey_button.pack(pady=5)

    # Center the window
    hotkey_config_root.update_idletasks()
    x = hotkey_config_root.winfo_screenwidth() // 2 - hotkey_config_root.winfo_width() // 2
    y = hotkey_config_root.winfo_screenheight() // 2 - hotkey_config_root.winfo_height() // 2
    hotkey_config_root.geometry(f"+{x}+{y}")

    is_capturing_hotkey = False # Reset capture state

def start_hotkey_capture():
    global hotkey_label, is_capturing_hotkey, captured_hotkey_string
    hotkey_label.config(text="Press your desired hotkey combination...", fg="blue")
    save_hotkey_button.config(state=tk.DISABLED)
    is_capturing_hotkey = True
    captured_hotkey_string = "" # Clear previous capture
    keyboard.clear_all_hotkeys() # Clear existing hotkeys to avoid interference during capture
    # Start a new thread to listen for the hotkey using keyboard.read_hotkey()
    threading.Thread(target=listen_for_new_hotkey_in_config, daemon=True).start()

def listen_for_new_hotkey_in_config():
    global HOTKEY, captured_hotkey_string
    # keyboard.read_hotkey() waits for a hotkey to be pressed and released
    new_hotkey = keyboard.read_hotkey()

    if new_hotkey:
        captured_hotkey_string = new_hotkey
        if hotkey_config_root and hotkey_config_root.winfo_exists():
            hotkey_label.config(text=f"Captured: {captured_hotkey_string}", fg="green")
            save_hotkey_button.config(state=tk.NORMAL) # Enable save button

def save_new_hotkey():
    global HOTKEY, captured_hotkey_string
    if captured_hotkey_string:
        # Check if the new hotkey is a single modifier key
        if captured_hotkey_string in ['shift', 'ctrl', 'alt', 'windows']:
            if hotkey_config_root and hotkey_config_root.winfo_exists():
                hotkey_label.config(text="Please use a combination (e.g., Ctrl+Shift+Space)", fg="red")
            save_hotkey_button.config(state=tk.DISABLED)
            # Re-enable listening for a new hotkey
            threading.Thread(target=listen_for_new_hotkey_in_config, daemon=True).start()
            return

        HOTKEY = captured_hotkey_string
        # Save to config.json
        current_config = load_config()
        current_config["hotkey"] = HOTKEY
        save_config(current_config)
        print(f"DEBUG: Hotkey updated to: {HOTKEY}")

        # Clear all existing hotkeys and re-register the main application hotkeys
        keyboard.clear_all_hotkeys() # Ensure a clean slate
        register_main_hotkeys() # Call the new function to re-register
        print("SUCCESS: Hotkey re-registered.")

    on_hotkey_config_close() # Close the window

def on_hotkey_config_close():
    global is_capturing_hotkey
    is_capturing_hotkey = False
    # Re-register the main hotkeys in case capture was cancelled mid-way
    keyboard.clear_all_hotkeys() # Ensure a clean slate
    register_main_hotkeys()
    if hotkey_config_root and hotkey_config_root.winfo_exists():
        hotkey_config_root.destroy()

# --- AI Configuration Window Functions ---
ai_config_root = None
ai_model_var = None
ai_ctx_var = None
ai_enabled_var = None
ai_hotstart_var = None
ai_save_screenshots_var = None

def show_ai_config_window():
    global ai_config_root, ai_model_var, ai_ctx_var, ai_enabled_var, ai_hotstart_var, ai_save_screenshots_var
    
    if ai_config_root and ai_config_root.winfo_exists():
        ai_config_root.lift()
        return
    
    ai_config_root = tk.Toplevel()
    ai_config_root.title("AI Writing Settings")
    ai_config_root.geometry("400x350")
    ai_config_root.attributes('-topmost', True)
    ai_config_root.protocol("WM_DELETE_WINDOW", on_ai_config_close)
    
    # Enable AI Assistance
    ai_enabled_var = tk.BooleanVar(value=AI_ENABLED)
    tk.Checkbutton(ai_config_root, text="Enable AI Writing Assistance", 
                   variable=ai_enabled_var, font=("Arial", 10, "bold")).pack(pady=10, anchor='w', padx=20)
    
    # Model Selection
    tk.Label(ai_config_root, text="AI Model:", font=("Arial", 10)).pack(pady=(10, 0), anchor='w', padx=20)
    ai_model_var = tk.StringVar(value=AI_MODEL)
    model_dropdown = tk.OptionMenu(ai_config_root, ai_model_var, 
                                   "qwen2.5-vl", "llava", "bakllava", "moondream")
    model_dropdown.pack(pady=5, anchor='w', padx=20)
    
    # Context Size
    tk.Label(ai_config_root, text="Context Size (num_ctx):", font=("Arial", 10)).pack(pady=(10, 0), anchor='w', padx=20)
    ai_ctx_var = tk.StringVar(value=str(AI_NUM_CTX))
    ctx_entry = tk.Entry(ai_config_root, textvariable=ai_ctx_var)
    ctx_entry.pack(pady=5, anchor='w', padx=20)
    
    # Hotstart
    ai_hotstart_var = tk.BooleanVar(value=AI_HOTSTART)
    tk.Checkbutton(ai_config_root, text="Hotstart Model (reduce latency)", 
                   variable=ai_hotstart_var).pack(pady=10, anchor='w', padx=20)
    
    # Save Screenshots (for debugging)
    ai_save_screenshots_var = tk.BooleanVar(value=AI_CONFIG.get("save_screenshots", False))
    tk.Checkbutton(ai_config_root, text="Save Screenshots (for debugging)", 
                   variable=ai_save_screenshots_var).pack(pady=10, anchor='w', padx=20)
    
    # Save Button
    save_button = tk.Button(ai_config_root, text="Save Settings", 
                           command=save_ai_settings, bg="#4CAF50", fg="white")
    save_button.pack(pady=20)
    
    # Center window
    ai_config_root.update_idletasks()
    x = ai_config_root.winfo_screenwidth() // 2 - ai_config_root.winfo_width() // 2
    y = ai_config_root.winfo_screenheight() // 2 - ai_config_root.winfo_height() // 2
    ai_config_root.geometry(f"+{x}+{y}")

def save_ai_settings():
    global AI_ENABLED, AI_MODEL, AI_NUM_CTX, AI_HOTSTART, AI_CONFIG
    
    # Update global variables
    AI_ENABLED = ai_enabled_var.get()
    AI_MODEL = ai_model_var.get()
    AI_NUM_CTX = int(ai_ctx_var.get())
    AI_HOTSTART = ai_hotstart_var.get()
    
    # Update config
    AI_CONFIG = {
        "enabled": AI_ENABLED,
        "model": AI_MODEL,
        "num_ctx": AI_NUM_CTX,
        "screenshot_quality": AI_SCREENSHOT_QUALITY,
        "max_screenshots": AI_MAX_SCREENSHOTS,
        "hotstart": AI_HOTSTART,
        "save_screenshots": ai_save_screenshots_var.get()
    }
    
    # Save to config file
    current_config = load_config()
    current_config["ai_assisted_writing"] = AI_CONFIG
    save_config(current_config)
    
    print(f"SUCCESS: AI settings saved. Model: {AI_MODEL}, Context: {AI_NUM_CTX}, Enabled: {AI_ENABLED}")
    
    # Initialize model if hotstart is enabled
    if AI_ENABLED and AI_HOTSTART:
        threading.Thread(target=initialize_ai_model, daemon=True).start()
    
    on_ai_config_close()

def on_ai_config_close():
    global ai_config_root
    if ai_config_root and ai_config_root.winfo_exists():
        ai_config_root.destroy()

# --- Core Application Logic ---
def register_main_hotkeys():
    global main_hotkey_press_handle
    # No need to remove_hotkey here, as clear_all_hotkeys() will be called before this function

    # Register new hotkeys
    main_hotkey_press_handle = keyboard.add_hotkey(HOTKEY, start_recording, suppress=True)
    print(f"DEBUG: Main hotkey '{HOTKEY}' registered.")

def monitor_hotkey_release():
    global is_hotkey_held
    while is_hotkey_held:
        if not keyboard.is_pressed(HOTKEY):
            stop_recording_and_transcribe()
            break
        time.sleep(0.05) # Check every 50ms

def start_recording():
    global is_recording, recording_data, is_hotkey_held
    if not is_recording:
        print("DEBUG: Hotkey pressed. Starting recording...")
        is_recording = True
        is_hotkey_held = True # Set flag
        recording_data = []
        # Update icon to indicate recording
        icon.icon = base_icon_image # Use the loaded PNG as the base icon
        # Send command to show pop-up
        popup_queue.put("show")
        # Start monitoring thread
        threading.Thread(target=monitor_hotkey_release, daemon=True).start()

def stop_recording_and_transcribe():
    global is_recording, is_hotkey_held
    if is_recording:
        print("DEBUG: Hotkey released. Stopping recording...")
        is_recording = False
        is_hotkey_held = False # Reset flag
        # Update icon to normal state
        icon.icon = base_icon_image # Revert to base icon
        # Send command to hide pop-up
        popup_queue.put("hide")

        # Process and transcribe audio
        if recording_data:
            print("DEBUG: Processing audio data...")
            # Convert to numpy array
            audio_data = np.concatenate(recording_data, axis=0)
            
            # Save to a temporary in-memory wav file
            # Use the dynamically detected input_samplerate for writing the WAV
            byte_io = io.BytesIO()
            wav.write(byte_io, input_samplerate, audio_data) # Use module-level input_samplerate
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
                print(f"SUCCESS: Transcription complete.")
                print(f"Original text: {transcribed_text}")

                # AI Processing (if enabled)
                final_text = transcribed_text
                if AI_ENABLED:
                    print("DEBUG: Capturing screenshot for AI processing...")
                    screenshot_bytes = capture_screenshot()
                    
                    if screenshot_bytes:
                        print("DEBUG: Sending to AI model for enhancement...")
                        final_text = enhance_text_with_ai(transcribed_text, screenshot_bytes)
                        print(f"Enhanced text: {final_text}")
                    else:
                        print("WARNING: Screenshot capture failed, using original text")
                
                # Write to active window
                print("DEBUG: Writing text to active window...")
                keyboard.write(final_text)
                
                # Hide popup after processing
                popup_queue.put("hide")
                
            except Exception as e:
                print(f"ERROR: An error occurred during transcription: {e}")
                # Make sure popup is hidden on error
                popup_queue.put("hide")
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
    # Destroy hotkey config window if open
    if hotkey_config_root and hotkey_config_root.winfo_exists():
        hotkey_config_root.destroy()
    # Unhook all keyboard listeners
    keyboard.unhook_all()
    icon.stop()

icon = pystray.Icon(
    'parrot_transcriber',
    icon=base_icon_image, # Use the loaded PNG as the base icon
    title='Parrot Transcriber',
    menu=pystray.Menu(
        item('Configure Hotkey', show_hotkey_config_window),
        item('AI Writing Settings', show_ai_config_window),
        item('Quit', on_quit)
    )
)

# --- Main Execution ---
def main():
    global model, stream # input_samplerate is now a module-level global
    print("DEBUG: Loading Whisper model...")
    model = whisper.load_model(MODEL_NAME)
    print("SUCCESS: Whisper model loaded.")

    # Load base icon image
    base_icon_image = Image.open(resource_path("systemicon.png"))

    # Start Tkinter pop-up window in a separate thread
    popup_thread = threading.Thread(target=run_popup_loop, daemon=True)
    popup_thread.start()

    # Setup audio stream
    print("DEBUG: Starting audio stream...")
    # Use the module-level input_samplerate
    stream = sd.InputStream(callback=callback, samplerate=input_samplerate, channels=1)
    stream.start()
    print("SUCCESS: Audio stream started.")

    # Register hotkey using the keyboard library
    register_main_hotkeys() # Initial registration
    
    # Initialize AI model if enabled and hotstart is on
    if AI_ENABLED and AI_HOTSTART:
        print("DEBUG: Initializing AI model...")
        threading.Thread(target=initialize_ai_model, daemon=True).start()
    
    # Run the system tray icon on the main thread (this is a blocking call)
    icon.run()

if __name__ == "__main__":
    main()