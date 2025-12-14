# Product Requirements Document (PRD): Parrot Transcriber

## 1. Introduction

This document outlines the requirements for the **Parrot Transcriber** application, a lightweight Windows desktop utility designed to provide seamless, on-demand speech-to-text transcription. The primary goal is to enhance user productivity by allowing quick and accurate voice input into any active text field.

## 2. Goals

*   To provide a fast and reliable method for converting spoken language into text.
*   To integrate seamlessly into the user's existing workflow without being intrusive.
*   To offer a customizable and intuitive user experience.
*   To operate efficiently in the background with minimal resource consumption.
*   To be distributable as a standalone executable for ease of use.

## 3. User Stories

As a user, I want to:
*   ...run the application in the background so it's always ready when I need it.
*   ...press and hold a hotkey to start recording my voice.
*   ...see a clear visual cue that my voice is being recorded.
*   ...release the hotkey to stop recording and trigger transcription.
*   ...have the transcribed text automatically typed into the application where my cursor is.
*   ...be able to easily change the hotkey combination through a user interface.
*   ...have the application remember my chosen hotkey across sessions.
*   ...be able to quit the application cleanly from the system tray.
*   ...use the application offline for privacy and speed.
*   ...distribute and install the application easily without needing Python installed.
*   ...optionally enhance my speech with AI-powered writing assistance that understands the context of what I'm writing.
*   ...configure AI settings including model selection and context window size.
*   ...see visual feedback when AI processing is occurring.

## 4. Functional Requirements

### 4.1. Core Transcription
*   **FR1.1:** The application SHALL transcribe spoken audio to text using the Whisper ASR model.
*   **FR1.2:** The application SHALL support offline transcription.
*   **FR1.3:** The transcribed text SHALL be automatically typed into the currently active text input field.

### 4.2. Hotkey Management
*   **FR2.1:** The application SHALL allow users to define a custom global hotkey combination to initiate and terminate recording.
*   **FR2.2:** The hotkey SHALL be configurable via a graphical user interface (GUI).
*   **FR2.3:** The application SHALL save the configured hotkey persistently (e.g., in a configuration file).
*   **FR2.4:** The application SHALL load the saved hotkey upon startup.
*   **FR2.5:** The hotkey configuration UI SHALL provide clear instructions and feedback during hotkey capture.
*   **FR2.6:** The hotkey configuration UI SHALL warn users against using single modifier keys as standalone hotkeys.

### 4.3. Audio Input
*   **FR3.1:** The application SHALL capture audio from the system's default microphone.
*   **FR3.2:** The application SHALL dynamically detect and adapt to the microphone's sample rate.
*   **FR3.3:** The application SHALL resample captured audio to 16kHz before passing it to the Whisper model.

### 4.4. User Interface (UI) & Experience (UX)
*   **FR4.1:** The application SHALL run in the Windows system tray.
*   **FR4.2:** The system tray icon SHALL provide a menu for configuration and exit options.
*   **FR4.3:** A visual cue (e.g., a small, pulsing pop-up window) SHALL appear when recording is active.
*   **FR4.4:** The visual cue SHALL disappear when recording stops.
*   **FR4.5:** The pop-up window SHALL be positioned in the bottom-right corner of the screen.
*   **FR4.6:** The pop-up window SHALL have customizable background and text colors.
*   **FR4.7:** The pop-up window's text SHALL have a pulsing effect.

### 4.5. Application Lifecycle
*   **FR5.1:** The application SHALL start minimized to the system tray.
*   **FR5.2:** The application SHALL provide a clean exit mechanism via the system tray menu.
*   **FR5.3:** The application SHALL be distributable as a single executable file for Windows.

### 4.6. AI-Powered Writing Assistance
*   **FR6.1:** The application SHALL provide optional AI-powered text enhancement.
*   **FR6.2:** When enabled, the application SHALL capture a screenshot upon hotkey release.
*   **FR6.3:** The application SHALL send the screenshot and transcribed text to a local Ollama model.
*   **FR6.4:** The application SHALL display "Processing with AI..." in the popup during AI processing.
*   **FR6.5:** The application SHALL provide configuration options for AI model selection and context size.
*   **FR6.6:** The application SHALL preserve the original meaning while enhancing text structure and coherence.
*   **FR6.7:** The application SHALL analyze the platform and conversation context from the screenshot.
*   **FR6.8:** The application SHALL limit screenshot retention to the last 20 screenshots for privacy.

## 5. Non-Functional Requirements

### 5.1. Performance
*   **NFR1.1:** Transcription latency SHALL be minimal (ideally < 2 seconds for short phrases).
*   **NFR1.2:** Resource consumption (CPU, RAM) SHALL be low when idle.
*   **NFR1.3:** Audio processing and resampling SHALL be efficient.

### 5.2. Reliability
*   **NFR2.1:** The hotkey detection and release SHALL be robust and consistent.
*   **NFR2.2:** The application SHALL handle common errors gracefully (e.g., microphone not found, transcription errors).
*   **NFR2.3:** The application SHALL shut down cleanly without leaving orphaned processes or icons.

### 5.3. Security
*   **NFR3.1:** The application SHALL require administrator privileges for global hotkey registration.
*   **NFR3.2:** No sensitive user data SHALL be transmitted over the network.

### 5.4. Maintainability
*   **NFR4.1:** The codebase SHALL be well-structured and commented.
*   **NFR4.2:** Dependencies SHALL be clearly listed.

### 5.5. AI Processing Performance
*   **NFR5.1:** AI processing latency SHALL be reasonable (ideally < 10 seconds for typical use cases).
*   **NFR5.2:** The application SHALL provide visual feedback during AI processing.
*   **NFR5.3:** The application SHALL gracefully fall back to original transcription if AI processing fails.
*   **NFR5.4:** Screenshot capture and processing SHALL respect user privacy settings.

## 6. Technical Considerations

*   **Language:** Python
*   **Libraries:** `pystray`, `keyboard`, `sounddevice`, `openai-whisper`, `pyperclip`, `numpy`, `scipy`, `soundfile`, `tkinter`, `queue`, `threading`, `json`, `time`, `Pillow`, `requests`.
*   **Packaging:** PyInstaller (for Windows .exe)
*   **Whisper Model:** `base` model (configurable to `tiny`, `small`, etc. in `config.json`)
*   **AI Models:** Multimodal models via Ollama (e.g., `qwen2.5-vl`)

## 7. Future Considerations (Out of Scope for Initial Release)

*   Support for multiple microphone devices.
*   Customizable pop-up text/messages.
*   Integration with cloud-based ASR services (optional, for higher accuracy/larger models).
*   Cross-platform compatibility (macOS, Linux).
*   Installer package (MSI).
*   User-selectable Whisper model size from UI.
*   Option to save transcription to a file instead of typing.
