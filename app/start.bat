@echo off
cd /d "%~dp0"
echo.
echo ========================================
echo   SMT AOI Dashboard
echo ========================================
echo.

REM Проверяваме дали Python е инсталиран
python --version >nul 2>&1
if errorlevel 1 (
    echo [ГРЕШКА] Python не е намерен!
    echo Инсталирай Python от https://python.org
    pause
    exit /b 1
)

REM Инсталираме нужните пакети ако липсват
echo Проверка на зависимости...
pip install flask werkzeug --quiet

echo.
echo Стартиране на сървъра...
echo Отвори браузър на: http://localhost:5000
echo За спиране натисни Ctrl+C
echo.
start "" http://localhost:5000
python app.py
pause
