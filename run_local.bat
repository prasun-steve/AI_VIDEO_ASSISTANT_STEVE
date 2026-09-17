@echo off
setlocal
if exist "%~dp0assistant\Scripts\python.exe" (
    set "PROJECT_PYTHON=%~dp0assistant\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PROJECT_PYTHON=%~dp0.venv\Scripts\python.exe"
) else (
    echo No project virtual environment found. Create one using the README instructions.
    exit /b 1
)
"%PROJECT_PYTHON%" -m streamlit run "%~dp0app.py"
