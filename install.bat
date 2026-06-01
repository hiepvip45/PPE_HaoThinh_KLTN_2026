@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════╗
echo ║     PPE Guardian - Cài đặt tự động       ║
echo ╚══════════════════════════════════════════╝
echo.

:: Kiểm tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LỖI] Chưa cài Python! Tải tại: https://www.python.org/downloads/
    pause & exit /b 1
)
echo [OK] Python đã cài đặt

:: Tạo virtual environment
if not exist "venv" (
    echo [INFO] Tạo virtual environment...
    python -m venv venv
)

:: Kích hoạt venv
call venv\Scripts\activate.bat

:: Cài thư viện
echo [INFO] Đang cài đặt thư viện (có thể mất 5-10 phút)...
pip install --upgrade pip -q
pip install -r requirements.txt

echo.
echo ╔══════════════════════════════════════════╗
echo ║  Cài đặt hoàn tất!                       ║
echo ║  Chạy app: run.bat                        ║
echo ╚══════════════════════════════════════════╝
pause
