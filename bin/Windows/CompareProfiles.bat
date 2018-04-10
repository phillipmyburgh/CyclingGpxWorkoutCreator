@echo off
REM Set Working directory to current script directory
cd /D "%~dp0"

REM Get the apiKey
set /p apiKey=<ApiKey.txt

IF [%apiKey%] == [] GOTO NOKEY

:HAVEKEY
python ..\..\CompareProfiles.py %* -a %apiKey%
GOTO END

:NOKEY
python ..\..\CompareProfiles.py %*
GOTO END

:END