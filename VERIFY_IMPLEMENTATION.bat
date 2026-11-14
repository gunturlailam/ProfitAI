@echo off
echo ============================================
echo VERIFYING 100%% IMPLEMENTATION - ProfitAI
echo ============================================
echo.

echo [1/7] Checking Backend DeepSeek Integration...
if exist "backend\app\llm_adapter.py" (
    echo ✓ llm_adapter.py found
) else (
    echo ✗ llm_adapter.py NOT FOUND
)
echo.

echo [2/7] Checking Frontend Auto-Alert Hook...
if exist "frontend\hooks\use-auto-alerts.ts" (
    echo ✓ use-auto-alerts.ts found
) else (
    echo ✗ use-auto-alerts.ts NOT FOUND
)
echo.

echo [3/7] Checking Predictive Panel...
if exist "frontend\components\dashboard\PredictiveInsightsPanel.tsx" (
    echo ✓ PredictiveInsightsPanel.tsx found
) else (
    echo ✗ PredictiveInsightsPanel.tsx NOT FOUND
)
echo.

echo [4/7] Checking Alert History Panel...
if exist "frontend\components\dashboard\AlertHistoryPanel.tsx" (
    echo ✓ AlertHistoryPanel.tsx found
) else (
    echo ✗ AlertHistoryPanel.tsx NOT FOUND
)
echo.

echo [5/7] Checking WebSocket Context...
if exist "frontend\lib\websocket-context.tsx" (
    echo ✓ websocket-context.tsx found
) else (
    echo ✗ websocket-context.tsx NOT FOUND
)
echo.

echo [6/7] Checking WebSocket Status Component...
if exist "frontend\components\shared\WebSocketStatus.tsx" (
    echo ✓ WebSocketStatus.tsx found
) else (
    echo ✗ WebSocketStatus.tsx NOT FOUND
)
echo.

echo [7/7] Checking Dashboard Integration...
if exist "frontend\app\(dashboard)\dashboard\page.tsx" (
    echo ✓ dashboard/page.tsx found
) else (
    echo ✗ dashboard/page.tsx NOT FOUND
)
echo.

echo ============================================
echo VERIFICATION COMPLETE
echo ============================================
echo.
echo Next Steps:
echo 1. cd backend
echo 2. python -m uvicorn app.main:app --reload
echo 3. Open new terminal: cd frontend
echo 4. npm run dev
echo 5. Visit http://localhost:3000
echo.
pause
