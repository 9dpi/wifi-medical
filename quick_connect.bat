@echo off
:: Copyright 2025 - 2026 Vu Quang Cuong
:: Wifi-Censor Quick Connect Setup Tool
:: Hỗ trợ cấu hình nhanh và đồng bộ 1-Click cho Desktop App & Web Dashboard

chcp 65001 > nul
title 📡 Wifi-Censor - Cấu Hình Kết Nối Nhanh 1-Click
cls

echo ======================================================================
echo           📡 HỆ THỐNG GIÁM SÁT AN TOÀN SỨC KHỎE WIFI-CENSOR
echo             CÔNG CỤ CẤU HÌNH & KẾT NỐI TỰ ĐỘNG 1-CLICK
echo ======================================================================
echo.
echo Công cụ này giúp bạn thiết lập kết nối đồng bộ giữa:
echo   [Desktop App (PC/Laptop)] ^<---^> [GitHub Cloud] ^<---^> [Web Dashboard]
echo chỉ trong một lần nhập duy nhất!
echo.
echo ⚠️  YÊU CẦU: Bạn cần chuẩn bị sẵn mã GitHub Personal Access Token (PAT).
echo ======================================================================
echo.

:INPUT_TOKEN
set /p TOKEN="👉 1. Nhập GitHub Personal Access Token (PAT): "
if "%TOKEN%"=="" (
    echo [Lỗi] Token không được để trống!
    goto INPUT_TOKEN
)

:INPUT_USER
set /p GH_USER="👉 2. Nhập Tên tài khoản GitHub (Username): "
if "%GH_USER%"=="" (
    echo [Lỗi] Tên tài khoản không được để trống!
    goto INPUT_USER
)

:INPUT_REPO
set /p GH_REPO="👉 3. Nhập Tên Repository đã tạo (ví dụ: wifi-medical): "
if "%GH_REPO%"=="" (
    echo [Lỗi] Tên repository không được để trống!
    goto INPUT_REPO
)

echo.
echo ----------------------------------------------------------------------
echo Đang tiến hành lưu cấu hình vào Desktop App...
echo ----------------------------------------------------------------------

:: Sử dụng PowerShell để cập nhật file wificensor_config.json một cách an toàn
powershell -Command ^
    "$configPath = 'desktop/wificensor_config.json';" ^
    "if (Test-Path $configPath) {" ^
    "    $json = Get-Content $configPath -Raw | ConvertFrom-Json;" ^
    "} else {" ^
    "    $json = @{};" ^
    "}" ^
    "$json.github_sync_enabled = $true;" ^
    "$json.github_token = '%TOKEN%';" ^
    "$json.github_username = '%GH_USER%';" ^
    "$json.github_repo = '%GH_REPO%';" ^
    "$json.github_device_id = 'desktop';" ^
    "$json.github_branch = 'main';" ^
    "$json.json_export_enabled = $true;" ^
    "$json | ConvertTo-Json -Depth 10 | Set-Content $configPath;" ^
    "Write-Output '[OK] Đã cập nhật thành công cấu hình wificensor_config.json!'"

if %ERRORLEVEL% NEQ 0 (
    echo [Lỗi] Không thể ghi file cấu hình. Vui lòng kiểm tra quyền thư mục!
    pause
    exit /b
)

echo.
echo ----------------------------------------------------------------------
echo Đang tạo liên kết tự động tới Web Dashboard...
echo ----------------------------------------------------------------------
echo.

set WEB_URL=https://%GH_USER%.github.io/%GH_REPO%/index.html?token=%TOKEN%^&owner=%GH_USER%^&repo=%GH_REPO%^&device=desktop

echo Liên kết Web của bạn: %WEB_URL%
echo.
echo [TỰ ĐỘNG HÓA CHUYÊN NGHIỆP]:
echo Ứng dụng sẽ tự động mở trình duyệt Web Dashboard và tự động lưu Token,
echo Tài khoản, Repo của bạn vào LocalStorage của trình duyệt. 
echo Bạn sẽ không cần phải nhập tay bất cứ thông tin nào trên Web nữa!
echo.

choice /M "🤔 Bạn có muốn mở Web Dashboard tự động ngay bây giờ không?"
if %ERRORLEVEL%==2 goto NO_OPEN

echo Mở trình duyệt web kết nối...
start "" "%WEB_URL%"
goto SUCCESS

:NO_OPEN
echo Bạn có thể tự copy link trên và mở trên trình duyệt bất cứ lúc nào.

:SUCCESS
echo.
echo ======================================================================
echo  🎉🎉 CẤU HÌNH THÀNH CÔNG! HỆ THỐNG ĐÃ SẴN SÀNG KẾT NỐI! 🎉🎉
echo ======================================================================
echo.
echo 👉 Hướng dẫn tiếp theo:
echo   1. Nhấp đúp vào file 'run_desktop.bat' (hoặc chạy 'python desktop/main.py')
echo      để khởi động Desktop Guard giám sát.
echo   2. Hệ thống sẽ bắt đầu thu thập sóng, suy luận nhịp tim, nhiệt độ
echo      và đẩy dữ liệu trực tiếp lên Web Dashboard của bạn!
echo.
pause
