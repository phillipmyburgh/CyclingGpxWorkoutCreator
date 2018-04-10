@echo off
REM Set Working directory to current script directory
cd /D "%~dp0"

REM Get the apiKey
set /p apiKey=<ApiKey.txt

IF [%apiKey%] == [] GOTO NOKEY

:HAVEKEY
python ..\..\ShowGpxInformation.py %1 -a %apiKey%
GOTO END

:NOKEY
python ..\..\ShowGpxInformation.py %1
GOTO END

:END