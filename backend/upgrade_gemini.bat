@echo off
echo ========================================
echo UPGRADE GEMINI INTEGRATION
echo ========================================
echo.

echo Step 1: Uninstall old deprecated package...
pip uninstall -y google-generativeai

echo.
echo Step 2: Install new google-genai package...
pip install google-genai

echo.
echo Step 3: Test new integration...
python test_gemini_new_api.py

echo.
echo ========================================
echo UPGRADE COMPLETE
echo ========================================
pause
