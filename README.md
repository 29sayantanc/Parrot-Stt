# Parrot Transcriber

![App Icon Placeholder](https://via.placeholder.com/64x64?text=STT)

Parrot Transcriber is a lightweight, background-running Windows desktop application that provides on-demand, real-time speech-to-text transcription. Simply press and hold a customizable hotkey, speak, and upon release, your words are instantly typed wherever your cursor is.

## ✨ Features

*   **Background Operation:** Runs silently in your system tray, ready when you need it.
*   **Customizable Hotkey:** Trigger transcription with your preferred key combination.
*   **Instant Transcription:** Converts spoken words to text and types them directly into any active application.
*   **Visual Feedback:** A subtle, pulsing pop-up indicates when recording is active.
*   **Offline Transcription:** Powered by the Whisper ASR model, ensuring privacy and speed without an internet connection.
*   **Dynamic Microphone Support:** Automatically detects and adapts to your microphone's sample rate.

## 🚀 Installation (Coming Soon: Executable)

Currently, this application runs from its Python source code. For a simpler installation, a standalone executable (`.exe`) will be provided in the future.

**To run from source (for developers/advanced users):**

1.  **Clone the repository:**
    ```bash
    git clone <repository_url_here>
    cd STT
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the application (as Administrator):**
    Due to global hotkey requirements, the application needs administrator privileges.
    *   Search for "Command Prompt" or "PowerShell" in your Windows Start Menu.
    *   Right-click and select "Run as administrator."
    *   Navigate to the application directory:
        ```bash
        D:
        cd "AI works\Softwares\Created by me\STT"
        ```
    *   Run the application:
        ```bash
        python main.py
        ```

## 💡 Usage

1.  **Start the Application:** Run `main.py` (or the future `.exe`). The application will appear as a small icon in your Windows system tray.
2.  **Access Menu:** Right-click the system tray icon to access options like "Configure Hotkey" or "Quit."
3.  **Transcribe:**
    *   Place your cursor in any text field (e.g., Notepad, browser search bar, Word document).
    *   **Press and hold** your configured hotkey (default: `Ctrl+Shift+Space`).
    *   A small "Recording..." pop-up will appear in the bottom-right corner, pulsing to indicate active recording.
    *   Speak clearly.
    *   **Release** the hotkey.
    *   The pop-up will disappear, and your transcribed text will be typed automatically at your cursor's position.

## ⚙️ Configuration

To change the hotkey:

1.  Right-click the application icon in the system tray.
2.  Select "Configure Hotkey."
3.  In the "Configure Hotkey" window, click "Set New Hotkey."
4.  Press your desired key combination (e.g., `Ctrl+Alt+T`, `F12`).
    *   **Note:** Single modifier keys (like `Shift`, `Ctrl`, `Alt`) are not recommended as standalone hotkeys due to technical limitations. Please use a combination.
5.  Click "Save Hotkey."
    The application will automatically update and use your new hotkey.

##  troubleshooting

*   **Hotkey Not Working / Application Not Responding:**
    *   **Run as Administrator:** Ensure you are running the application with administrator privileges. This is required for global hotkey detection.
    *   **Check for Conflicts:** Other applications might be using the same hotkey. Try configuring a different, less common hotkey combination.
*   **Transcription is Gibberish:**
    *   Ensure your microphone is properly configured and selected as the default input device in Windows sound settings.
    *   Speak clearly and at a moderate pace.
    *   The application automatically handles microphone sample rates, but very unusual configurations might still cause issues.
*   **Application Not Quitting:**
    *   Right-click the system tray icon and select "Quit." This is the proper way to shut down the application.

## 🤝 Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE.md file for details.

## credits

*   Powered by [Whisper](https://openai.com/research/whisper) by OpenAI
*   Uses [pystray](https://pystray.readthedocs.io/) for system tray integration
*   Uses [keyboard](https://pypi.org/project/keyboard/) for global hotkey detection
*   Uses [sounddevice](https://python-sounddevice.readthedocs.io/) for audio input
*   Uses [pyperclip](https://pypi.org/project/pyperclip/) for clipboard operations
*   Uses [NumPy](https://numpy.org/) and [SciPy](https://scipy.org/) for audio processing
*   Uses [soundfile](https://pysoundfile.readthedocs.io/) for audio file handling
*   Uses [Tkinter](https://docs.python.org/3/library/tkinter.html) for UI elements
