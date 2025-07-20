import time
from pynput import keyboard

HOTKEY = keyboard.Key.f8

def on_press(key):
    if key == HOTKEY:
        print(f"--- Hotkey Pressed: {key} ---")

def on_release(key):
    if key == HOTKEY:
        print(f"--- Hotkey Released: {key} ---")

print("Starting minimal hotkey listener...")
print(f"Listening for F8 key. Press Ctrl+C to exit.")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    try:
        listener.join()
    except KeyboardInterrupt:
        print("\nExiting listener.")
