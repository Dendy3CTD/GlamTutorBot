@echo off
echo Zapusk GlamTutorBot...
echo.
REM 1) py launcher
py -3 main.py 2>nul
if not errorlevel 1 goto :ok
REM 2) python in PATH
python main.py 2>nul
if not errorlevel 1 goto :ok
REM 3) standard path (Python 3.13 у вас найден здесь)
"%LOCALAPPDATA%\Programs\Python\Python313\python.exe" main.py 2>nul
if not errorlevel 1 goto :ok
REM 4) any Python3xx
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    "%%d\python.exe" main.py 2>nul
    if not errorlevel 1 goto :ok
)
echo.
echo Python ne najden. Zapustite run.ps1 ili ustanovite Python.
pause
exit /b 1
:ok
pause
