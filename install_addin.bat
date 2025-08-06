@echo off
setlocal

REM Get the directory where this script is running
set "SOURCE_ADDIN_PATH=%~dp0"
REM Remove trailing backslash
if "%SOURCE_ADDIN_PATH:~-1%"=="\" set "SOURCE_ADDIN_PATH=%SOURCE_ADDIN_PATH:~0,-1%"

REM Extract folder name only (last folder in path)
for %%a in ("%SOURCE_ADDIN_PATH%") do set "FOLDER_NAME=%%~nxa"

REM Fusion 360 AddIns destination directory on Windows
set "DEST_ADDINS_PATH=%APPDATA%\Autodesk\Fusion 360\API\AddIns\%FOLDER_NAME%"

REM Check if source folder exists
if not exist "%SOURCE_ADDIN_PATH%" (
    echo Source add-in folder does not exist: %SOURCE_ADDIN_PATH%
    exit /b 1
)

REM Create destination directory if it doesn't exist
if not exist "%DEST_ADDINS_PATH%" (
    mkdir "%DEST_ADDINS_PATH%"
)

REM Copy the add-in folder recursively (replace existing)
xcopy /E /I /Y "%SOURCE_ADDIN_PATH%\*" "%DEST_ADDINS_PATH%\"

if %ERRORLEVEL% equ 0 (
    echo Add-in copied successfully to %DEST_ADDINS_PATH%
) else (
    echo Failed to copy add-in.
    exit /b 1
)

endlocal
