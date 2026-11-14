@echo off
echo ============================================
echo ProfitAI - AI-Powered Financial Dashboard
echo 100%% Implementation Demo
echo ============================================
echo.
echo This script will start both backend and frontend.
echo Please make sure:
echo   1. Python virtual environment is activated (backend\venv)
echo   2. Node.js dependencies are installed (npm install in frontend)
echo.
pause
echo.
echo [1/2] Starting Backend (FastAPI + DeepSeek AI)...
start cmd /k "cd backend && python -m uvicorn app.main:app --reload"
echo Backend starting on http://localhost:8000
echo.
timeout /t 3 /nobreak >nul
echo.
echo [2/2] Starting Frontend (Next.js)...
start cmd /k "cd frontend && npm run dev"
echo Frontend starting on http://localhost:3000
echo.
echo ============================================
echo DEMO READY!
echo ============================================
echo.
echo Backend API: http://localhost:8000
echo API Docs:    http://localhost:8000/docs
echo Frontend:    http://localhost:3000
echo.
echo AI Features Enabled:
echo   ✓ DeepSeek Narrative Generation
echo   ✓ Auto Toast Notifications
echo   ✓ Predictive Insights Panel
echo   ✓ Alert History Tracking
echo   ✓ WebSocket Real-time Updates
echo.
echo Login credentials (demo):
echo   Email:    admin@profitai.dev
echo   Password: (check seed_demo.py)
echo.
echo Press any key to exit...
pause >nul
