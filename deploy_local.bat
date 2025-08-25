@echo off
REM 家庭内サーバーへのデプロイスクリプト（Windows用）
REM Usage: deploy_local.bat [server_ip]

setlocal enabledelayedexpansion

REM デフォルトのサーバーIP
if "%1"=="" (
    set SERVER_IP=192.168.1.45
) else (
    set SERVER_IP=%1
)

set SERVER_USER=ubuntu
set PROJECT_NAME=vertical_text_generator
set REMOTE_DIR=/home/%SERVER_USER%/%PROJECT_NAME%

echo 🚀 家庭内サーバーへのデプロイを開始します
echo サーバー: %SERVER_USER%@%SERVER_IP%
echo プロジェクト: %PROJECT_NAME%
echo.

REM 1. サーバー接続確認
echo 📡 サーバー接続確認中...
ssh -o ConnectTimeout=10 %SERVER_USER%@%SERVER_IP% "echo 'Connection OK'" >nul 2>&1
if errorlevel 1 (
    echo ❌ サーバーに接続できません: %SERVER_USER%@%SERVER_IP%
    echo SSH設定を確認してください
    pause
    exit /b 1
)

REM 2. 必要なディレクトリの作成
echo 📁 リモートディレクトリを準備中...
ssh %SERVER_USER%@%SERVER_IP% "mkdir -p %REMOTE_DIR%"

REM 3. プロジェクトファイルをアップロード
echo 📤 プロジェクトファイルをアップロード中...
scp -r -o "UserKnownHostsFile=/dev/null" -o "StrictHostKeyChecking=no" ^
    --exclude=".git" --exclude="__pycache__" --exclude="test_output" ^
    --exclude="test_results" --exclude=".venv" --exclude="node_modules" ^
    ./* %SERVER_USER%@%SERVER_IP%:%REMOTE_DIR%/

REM 4. リモートサーバーでDockerコンテナを構築・起動
echo 🐳 リモートサーバーでDockerコンテナを構築・起動中...
ssh %SERVER_USER%@%SERVER_IP% "cd %REMOTE_DIR% && docker compose -f docker-compose.local.yml down --remove-orphans && docker compose -f docker-compose.local.yml up --build -d"

REM 5. ヘルスチェック
echo 🏥 サービス起動確認中...
timeout /t 15 /nobreak >nul

for /l %%i in (1,1,10) do (
    ssh %SERVER_USER%@%SERVER_IP% "curl -s http://localhost:8000/health" >nul 2>&1
    if not errorlevel 1 (
        echo ✅ サービスが正常に起動しました！
        echo.
        echo 🎉 デプロイ完了！
        echo アクセス URL: http://%SERVER_IP%:8000
        echo ヘルスチェック: http://%SERVER_IP%:8000/health
        echo API ドキュメント: http://%SERVER_IP%:8000/docs
        echo.
        for /f "tokens=2 delims==" %%a in ('findstr "API_TOKEN" .env') do echo 📋 APIトークン: %%a
        pause
        exit /b 0
    )
    echo ⏳ サービス起動待機中... (%%i/10)
    timeout /t 3 /nobreak >nul
)

echo ❌ サービスの起動確認に失敗しました
echo ログを確認してください:
echo ssh %SERVER_USER%@%SERVER_IP% "cd %REMOTE_DIR% && docker compose -f docker-compose.local.yml logs"
pause
exit /b 1
