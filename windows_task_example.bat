@echo off
REM ============================================================================
REM Příklad BAT skriptu pro Windows Task Scheduler
REM Job Scraper - Automatické spouštění
REM ============================================================================

REM Nastavení cest - UPRAVTE PODLE VAŠÍ INSTALACE
SET PROJECT_DIR=C:\Users\YourUsername\scrape_pracovni_nabidky
SET PYTHON_EXE=C:\Users\YourUsername\scrape_pracovni_nabidky\venv\Scripts\python.exe
SET SCRIPT_PATH=%PROJECT_DIR%\main.py
SET LOG_FILE=%PROJECT_DIR%\windows_task.log

REM Volitelné: Nastavení environment variables pro LinkedIn
REM SET LINKEDIN_EMAIL=your-email@example.com
REM SET LINKEDIN_PASSWORD=your-password

REM Přesun do projektového adresáře
cd /d %PROJECT_DIR%

REM Spuštění scraperu
echo ============================================ >> %LOG_FILE%
echo Job Scraper Run - %date% %time% >> %LOG_FILE%
echo ============================================ >> %LOG_FILE%

%PYTHON_EXE% %SCRIPT_PATH% >> %LOG_FILE% 2>&1

REM Kontrola exit kódu
if %ERRORLEVEL% EQU 0 (
    echo Scraper dokoncen uspesne >> %LOG_FILE%
) else (
    echo CHYBA: Scraper selhal s exit kodem %ERRORLEVEL% >> %LOG_FILE%
)

echo. >> %LOG_FILE%
