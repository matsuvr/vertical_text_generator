#!/bin/bash

# Google Cloud Runデプロイスクリプト
set -e

# 設定
PROJECT_ID="manganamemaker"
SERVICE_NAME="vertical-text-api"
REGION="asia-northeast1"  # 東京リージョン
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Google Cloud Runにデプロイを開始します..."
echo "プロジェクトID: $PROJECT_ID"
echo "サービス名: $SERVICE_NAME"
echo "リージョン: $REGION"
echo "イメージ: $IMAGE_NAME"
echo ""

# Google Cloudプロジェクトを設定
echo "📋 Google Cloudプロジェクトを設定..."
gcloud config set project $PROJECT_ID

# Container Registry APIを有効化
echo "🔧 必要なAPIを有効化..."
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Dockerイメージをビルドしてプッシュ
echo "🏗️  Dockerイメージをビルド中..."
docker build -t $IMAGE_NAME .

echo "📤 イメージをContainer Registryにプッシュ中..."
docker push $IMAGE_NAME

# Cloud Runにデプロイ
echo "🚢 Cloud Runにデプロイ中..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 100 \
  --min-instances 0 \
  --concurrency 10 \
  --set-env-vars "API_TOKEN=manganamemaker-secret-token" \
  --port 8080

# デプロイ完了
echo ""
echo "✅ デプロイ完了！"
echo ""
echo "サービスURL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
echo ""
echo "🧪 テスト用コマンド:"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "curl $SERVICE_URL/health"
echo ""
echo "📊 ログの確認:"
echo "gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME' --limit 50 --format json"
