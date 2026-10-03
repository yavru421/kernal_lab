@echo off
rem kernel_host build: MSVC 14.44 + CUDA 12.6 + libduckdb v1.5.6 + NVML. No CMake, no interpreter.
rem Output: host\bin\kernel_host.exe (+ duckdb.dll copied beside it). Build log: host\bin\build.log
setlocal
set HOST=%~dp0
set CUDA=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6
set TP=%HOST%third_party
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul || exit /b 10
if not exist "%HOST%bin" mkdir "%HOST%bin"
"%CUDA%\bin\nvcc.exe" -std=c++17 -O2 -Xcompiler "/EHa /W3" ^
  -I"%TP%" -I"%CUDA%\include" ^
  "%HOST%src\kernel_host.cpp" -o "%HOST%bin\kernel_host.exe" ^
  -L"%TP%" -L"%CUDA%\lib\x64" -lduckdb -lnvml -lcudart -lbcrypt > "%HOST%bin\build.log" 2>&1
set RC=%ERRORLEVEL%
type "%HOST%bin\build.log"
if not %RC%==0 exit /b %RC%
copy /y "%TP%\duckdb.dll" "%HOST%bin\" >nul || exit /b 11
exit /b 0
