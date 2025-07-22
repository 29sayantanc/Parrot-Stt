import keyboard
import time

def on_shift_press():
    print("Shift key pressed!")

def on_shift_release():
    print("Shift key released!")

print("Attempting to register 'shift' as a hotkey. Press Shift to test. Press Ctrl+C to exit.")

# Register 'shift' for press and release
keyboard.add_hotkey('shift', on_shift_press, suppress=True)
keyboard.add_hotkey('shift', on_shift_release, suppress=True, trigger_on_release=True)

try:
    # Keep the script running to listen for hotkeys
    keyboard.wait('esc') # Wait indefinitely until 'esc' is pressed
except KeyboardInterrupt:
    print("Exiting.")
finally:
    keyboard.unhook_all() # Clean up hotkeys on exit
