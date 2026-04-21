@echo off
echo ========================================
echo   PPNO - AUTO EXECUTION OF EXAMPLES
echo ========================================

echo [1/3] Running Hanoi Network Example...
ppno ppno/examples/example_1.ext 2>&1 | powershell -Command "$input | Tee-Object -FilePath 'example_1.txt'"

echo [2/3] Running Balerma Irrigation Network Example...
ppno ppno/examples/example_2.ext 2>&1 | powershell -Command "$input | Tee-Object -FilePath 'example_2.txt'"

echo [3/3] Running New York Network Example...
ppno ppno/examples/example_3.ext 2>&1 | powershell -Command "$input | Tee-Object -FilePath 'example_3.txt'"

echo ========================================
echo   Execution finished.
echo   Logs have been displayed and saved to:
echo   - example_1.txt
echo   - example_2.txt
echo   - example_3.txt
echo ========================================
pause
