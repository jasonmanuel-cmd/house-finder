@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First-time setup: installing the project environment with uv.
  uv venv --python 3.11 .venv
  if errorlevel 1 goto fail
  uv pip install --python .venv\Scripts\python.exe -r requirements.txt
  if errorlevel 1 goto fail
)
echo Open http://127.0.0.1:5000 in your browser. Keep this window open.
".venv\Scripts\python.exe" serve.py
if errorlevel 1 goto fail
exit /b 0
:fail
echo Startup failed. Read the error above.
pause
exit /b 1
