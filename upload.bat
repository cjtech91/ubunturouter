@echo off
:MENU
CLS
ECHO ==========================================
ECHO   Ubuntu Router Uploader
ECHO ==========================================
ECHO 1. Upload to GitHub (Git Push)
ECHO 2. Upload directly to Device (SCP)
ECHO 3. Exit
ECHO.
SET /P M=Type 1, 2, or 3 then press ENTER: 
IF %M%==1 GOTO GIT
IF %M%==2 GOTO SCP
IF %M%==3 GOTO EOF

:GIT
ECHO.
ECHO --- Git Push ---
set /p commit_msg="Enter commit message (default: 'Update'): "
if "%commit_msg%"=="" set commit_msg=Update
ECHO.
ECHO Adding files...
git add .
ECHO Committing...
git commit -m "%commit_msg%"
ECHO Pushing...
git push
ECHO.
ECHO Git Upload Complete.
PAUSE
GOTO MENU

:SCP
ECHO.
ECHO --- Direct SCP Upload ---
ECHO Note: This will copy source files to the device.
ECHO It excludes 'venv' and '.git' to save time.
ECHO.
set /p target_ip="Enter Device IP: "
set /p target_user="Enter Username (default: root): "
if "%target_user%"=="" set target_user=root
set /p target_dir="Enter Remote Directory (default: ~/ubuntu-router): "
if "%target_dir%"=="" set target_dir=~/ubuntu-router

ECHO.
ECHO Uploading files to %target_user%@%target_ip%:%target_dir% ...
ECHO (You may be asked for the device password)
ECHO.
scp -r app config scripts gunicorn_config.py run.py requirements.txt %target_user%@%target_ip%:%target_dir%
ECHO.
ECHO SCP Upload Complete.
PAUSE
GOTO MENU

:EOF
