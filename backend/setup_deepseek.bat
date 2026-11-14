@echo off
echo ========================================
echo SETUP DEEPSEEK INTEGRATION
echo ========================================
echo.

echo Step 1: Uninstall old packages...
pip uninstall -y google-generativeai google-genai

echo.
echo Step 2: Install OpenAI package...
pip install openai requests

echo.
echo Step 3: Test DeepSeek integration...
python test_deepseek.py

echo.
echo ========================================
echo SETUP COMPLETE
echo ========================================
pause
