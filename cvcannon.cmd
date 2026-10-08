@echo off
rem Windows entry point for cvcannon. Takes the same arguments as make, for example:
rem   cvcannon.cmd install
rem   cvcannon.cmd build SLUG=acme-platform-engineer
rem Installs Python for the current user first when no Python 3.9+ is available.
setlocal EnableExtensions
set "CVCANNON_ROOT=%~dp0"
set "PY_VERSION=3.14.8"

call :find_python
if not defined CVCANNON_PY call :install_python
if not defined CVCANNON_PY call :find_python
if not defined CVCANNON_PY (
  echo ERROR: Python 3.9 or newer is required and could not be installed automatically. 1>&2
  echo Install it from https://www.python.org/downloads/windows/ and run this command again. 1>&2
  exit /b 1
)
%CVCANNON_PY% "%CVCANNON_ROOT%scripts\cv.py" %*
exit /b %ERRORLEVEL%

:find_python
set "CVCANNON_PY="
set "CHECK=import sys; sys.exit(sys.version_info < (3, 9))"
rem The Microsoft Store placeholder for python.exe fails this check and is skipped.
py -3 -c "%CHECK%" >nul 2>&1 && set "CVCANNON_PY=py -3" && exit /b 0
python -c "%CHECK%" >nul 2>&1 && set "CVCANNON_PY=python" && exit /b 0
rem A Python installed during this session is not on this terminal's PATH yet.
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
  if exist "%%D\python.exe" "%%D\python.exe" -c "%CHECK%" >nul 2>&1 && set CVCANNON_PY="%%D\python.exe"
)
exit /b 0

:install_python
set "PY_ARCH=amd64"
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "PY_ARCH=arm64"
set "PY_INSTALLER=%TEMP%\cvcannon-python-%PY_VERSION%-%PY_ARCH%.exe"
echo Python 3.9 or newer was not found. Installing Python %PY_VERSION% for the current user...
curl.exe -fsSL -o "%PY_INSTALLER%" "https://www.python.org/ftp/python/%PY_VERSION%/python-%PY_VERSION%-%PY_ARCH%.exe"
if errorlevel 1 (
  echo ERROR: could not download the Python installer. 1>&2
  exit /b 0
)
rem Per-user install: no administrator rights and no prompts.
"%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 InstallLauncherAllUsers=0 Include_test=0 Shortcuts=0
if errorlevel 1 echo ERROR: the Python installer failed with exit code %ERRORLEVEL%. 1>&2
del "%PY_INSTALLER%" >nul 2>&1
exit /b 0
