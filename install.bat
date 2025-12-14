@echo off
echo "Checking for Python..."
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo "Error: Python is not found in your PATH."
    echo "Please install Python from https://www.python.org/ and ensure it's added to your PATH."
    pause
    exit /b 1
)

echo "Creating virtual environment 'venv'..."
python -m venv venv

echo "Installing dependencies from requirements.txt..."
call venv\Scripts\pip.exe install -r requirements.txt

echo "Installation complete!"
echo "You can now run the application using run.bat"
pause
