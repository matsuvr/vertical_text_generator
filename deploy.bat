@echo off
setlocal

REM Google Cloud Runデプロイスクリプト (Windows版)

set PROJECT_ID=manganamemaker
set SERVICE_NAME=vertical-text-api
set REGION=asia-northeast1
set IMAGE_NAME=gcr.io/%PROJECT_ID%/%SERVICE_NAME%

echo 🚀 Google Cloud Runにデプロイを開始します...
echo プロジェクトID: %PROJECT_ID%
echo サービス名: %SERVICE_NAME%
echo リージョン: %REGION%
echo イメージ: %IMAGE_NAME%
echo.

REM Google Cloudプロジェクトを設定
echo 📋 Google Cloudプロジェクトを設定...
gcloud config set project %PROJECT_ID%

REM 必要なAPIを有効化
echo 🔧 必要なAPIを有効化...
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

REM Dockerイメージをビルドしてプッシュ
echo 🏗️  Dockerイメージをビルド中...
docker build -t %IMAGE_NAME% .

echo 📤 イメージをContainer Registryにプッシュ中...
docker push %IMAGE_NAME%

REM Cloud Runにデプロイ
echo 🚢 Cloud Runにデプロイ中...
gcloud run deploy %SERVICE_NAME% ^
  --image %IMAGE_NAME% ^
  --platform managed ^
  --region %REGION% ^
  --allow-unauthenticated ^
  --memory 4Gi ^
  --cpu 2 ^
  --timeout 300 ^
  --max-instances 100 ^
  --min-instances 0 ^
  --concurrency 10 ^
  --set-env-vars "API_TOKEN=manganamemaker-secret-token" ^
  --port 8080

REM デプロイ完了
echo.
echo ✅ デプロイ完了！
echo.
echo サービスURL:
for /f "tokens=*" %%i in ('gcloud run services describe %SERVICE_NAME% --region %REGION% --format "value(status.url)"') do set SERVICE_URL=%%i
echo %SERVICE_URL%
echo.
echo 🧪 テスト用コマンド:
echo curl %SERVICE_URL%/health
echo.
echo 📊 ログの確認:
echo gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=%SERVICE_NAME%" --limit 50 --format json

pause
