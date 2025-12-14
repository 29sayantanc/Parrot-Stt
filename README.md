# 🦜 Parrot Transcriber

<p align="center">
  <img width="150" height="150" alt="parrot-logo" src="https://github.com/user-attachments/assets/aa92592a-258d-4271-818d-3f83387b26b5">
</p>

<p align="center">
  <strong>Your personal AI-powered speech-to-text assistant </strong>
</p>

---

Parrot Transcriber is a lightweight, background-running Windows desktop application that provides on-demand, real-time speech-to-text transcription. Simply press and hold a customizable hotkey, speak, and upon release, your words are instantly typed wherever your cursor is.

What makes Parrot special is its optional **AI-powered writing assistance**, which uses a local multimodal AI model to rewrite your spoken text with context from your screen, making your writing more coherent and effective.

<!-- TODO: Add a GIF of the application in action! -->
<!-- ![Parrot Transcriber in action](link_to_your_gif_here.gif) -->

## ✨ Features

*   **Background Operation:** Runs silently in your system tray, ready when you need it.
*   **Customizable Hotkey:** Trigger transcription with your preferred key combination.
*   **Instant Transcription:** Converts spoken words to text and types them directly into any active application.
*   **Visual Feedback:** A subtle, pulsing pop-up indicates when recording is active.
*   **Offline Transcription:** Powered by the Whisper ASR model, ensuring privacy and speed without an internet connection.
*   **AI-Powered Writing Assistance:** (Optional) Enhances your speech with context-aware rewriting using local multimodal AI models.
*   **Easy Installation:** Simple setup with a batch script.

---

## 🚀 Installation

Getting started with Parrot Transcriber is easy. Just follow these steps:

1.  **Download the Code:**
    *   Clone this repository or download the source code as a ZIP file and extract it.

2.  **Run the Installer:**
    *   Navigate to the application directory.
    *   Double-click the `install.bat` file.
    *   This script will automatically create a virtual environment and install all the necessary dependencies.

    > **Note:** The script will check if you have Python installed and added to your system's PATH. If not, it will prompt you to install it from [python.org](https://www.python.org/).

3.  **Run the Application:**
    *   Once the installation is complete, double-click the `run.bat` file.
    *   The application will start and its icon will appear in your system tray.

    > **Important:** The first time you run the application, it may need to download the Whisper model, which can take a few moments.

---

## 🤖 AI-Powered Writing Assistance (Optional)

To unlock the full power of Parrot, you can enable AI-assisted writing. This feature analyzes a screenshot of your active window to provide context-aware suggestions, improving your grammar, tone, and coherence.

### Requirements

This feature relies on **Ollama**, a powerful tool for running large language models locally.

1.  **Install Ollama:**
    *   Download and install Ollama from the [official website](https://ollama.com/).

2.  **Install a Vision Model:**
    *   Parrot needs a **multimodal (vision)** model to analyze screenshots. Open your command prompt or terminal and pull a model. We recommend starting with a smaller, fast model like  `qwen`.
    *   Run the following command:
        ```bash
        ollama pull <your model name>
        ```
        or
        ```bash
        ollama pull qwen2.5vl:3b
        ```

### How It Works

1.  **Context Analysis:** When enabled, the application takes a screenshot when you release the hotkey and analyzes the platform, conversation history, and appropriate writing style.
2.  **Intelligent Enhancement:** The AI preserves your meaning while improving sentence structure, vocabulary, and coherence.
3.  **Privacy-First:** All processing happens locally on your machine. No data ever leaves your computer.

---

## 💡 Usage

1.  **Start the Application:** Run `run.bat`. The Parrot icon will appear in your system tray.
2.  **Access Menu:** Right-click the system tray icon to access "Configure Hotkey," "AI Writing Settings," or "Quit."
3.  **Transcribe:**
    *   Place your cursor in any text field.
    *   **Press and hold** your configured hotkey.
    *   A "Recording..." pop-up will appear. Speak clearly.
    *   **Release** the hotkey.
    *   Your transcribed (or AI-enhanced) text will be typed automatically.

## ⚙️ Configuration

You can customize Parrot's settings from the system tray menu.

*   **Hotkey:** Set your preferred key combination to trigger recording.
*   **AI Writing Settings:**
    *   Enable or disable the feature.
    *   Select the Ollama model you want to use.
    *   Configure other AI-related parameters.

---

## troubleshooting

*   **Hotkey Not Working:** Ensure you are running the application with administrator privileges if you encounter issues with global hotkey detection.
*   **Transcription is Gibberish:** Check that your microphone is properly configured in Windows sound settings.
*   **AI Processing Issues:**
    *   Make sure Ollama is running in the background.
    *   Verify that you have successfully pulled a vision model.
*   **Application Not Quitting:** Always use the "Quit" option from the system tray menu to shut down the application cleanly.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
