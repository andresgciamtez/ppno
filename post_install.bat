@echo off
:: Post-install script: installs ppno from the bundled wheel.
:: --no-deps: conda already installed numpy, scipy, pygmo. Don't let pip touch them.
echo Installing PPNO...
"%PREFIX%\python.exe" -m pip install --no-index --find-links="%PREFIX%\pkgs_pip" --no-deps ppno
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install PPNO.
    exit /b 1
)
echo PPNO installed successfully.

:: Add Scripts folder to the user PATH so 'ppno' is available from any terminal
echo Adding %PREFIX%\Scripts to user PATH...
powershell -Command ^
  "$old = [Environment]::GetEnvironmentVariable('PATH','User'); ^
   $add = '%PREFIX%\Scripts'; ^
   if ($old -notlike '*' + $add + '*') { ^
     [Environment]::SetEnvironmentVariable('PATH', $old + ';' + $add, 'User') ^
   }"
echo Done. Open a new terminal and run: ppno ^<problem_file.ext^>
