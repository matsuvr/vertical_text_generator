# Google Cloud Run デプロイ手順

## 前提条件

1. **Google Cloud CLI のインストール**
   ```bash
   # Windows の場合
   https://cloud.google.com/sdk/docs/install

   # インストール後、認証
   gcloud auth login
   gcloud auth configure-docker
   ```

2. **Dockerのインストール**
   - Docker Desktop for Windows をインストール

3. **プロジェクトの設定**
   ```bash
   gcloud config set project manganamemaker
   ```

## 手動デプロイ手順

### 方法1: デプロイスクリプトを使用（推奨）

```bash
# Windows の場合
./deploy.bat

# Git Bash / WSL の場合
chmod +x deploy.sh
./deploy.sh
```

### 方法2: 手動でのデプロイ

1. **必要なAPIを有効化**
   ```bash
   gcloud services enable containerregistry.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

2. **Dockerイメージをビルド**
   ```bash
   docker build -t gcr.io/manganamemaker/vertical-text-api .
   ```

3. **Container Registryにプッシュ**
   ```bash
   docker push gcr.io/manganamemaker/vertical-text-api
   ```

4. **Cloud Runにデプロイ**
   ```bash
   gcloud run deploy vertical-text-api \
     --image gcr.io/manganamemaker/vertical-text-api \
     --platform managed \
     --region asia-northeast1 \
     --allow-unauthenticated \
     --memory 4Gi \
     --cpu 2 \
     --timeout 300 \
     --max-instances 100 \
     --min-instances 0 \
     --concurrency 10 \
     --set-env-vars "API_TOKEN=manganamemaker-secret-token" \
     --port 8080
   ```

## CI/CDパイプライン（GitHub Actions使用）

### Cloud Buildを使用した自動デプロイ

1. **Cloud Build トリガーの作成**
   ```bash
   gcloud builds triggers create github \
     --repo-name=vertical_text_generator \
     --repo-owner=matsuvr \
     --branch-pattern="^main$" \
     --build-config=cloudbuild.yaml
   ```

2. **GitHubにプッシュすると自動デプロイ**
   ```bash
   git add .
   git commit -m "Deploy to Cloud Run"
   git push origin main
   ```

## APIの使用方法

### 基本的な使用例

```bash
# ヘルスチェック
curl https://vertical-text-api-xxxxxxx-an.a.run.app/health

# 縦書きテキストの生成
curl -X POST "https://vertical-text-api-xxxxxxx-an.a.run.app/render" \
  -H "Authorization: Bearer manganamemaker-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "こんにちは、世界！\n日本語の縦書きです。",
    "font_size": 24,
    "max_chars_per_line": 10
  }'
```

### Pythonでの使用例

```python
import requests
import base64

url = "https://vertical-text-api-xxxxxxx-an.a.run.app/render"
headers = {
    "Authorization": "Bearer manganamemaker-secret-token",
    "Content-Type": "application/json"
}

data = {
    "text": "吾輩は猫である。名前はまだ無い。",
    "font_size": 20,
    "max_chars_per_line": 15
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    result = response.json()

    # Base64画像をデコードして保存
    image_data = base64.b64decode(result["image_base64"])
    with open("vertical_text.png", "wb") as f:
        f.write(image_data)

    print(f"サイズ: {result['width']}x{result['height']}")
    print(f"処理時間: {result['processing_time_ms']:.2f}ms")
```

## 環境変数

- `API_TOKEN`: API認証用のトークン
- `PORT`: サーバーのポート番号（Cloud Runが自動設定）

## リソース設定

- **CPU**: 2コア
- **メモリ**: 4GB
- **タイムアウト**: 300秒
- **同時実行数**: 10
- **最大インスタンス数**: 100
- **最小インスタンス数**: 0（コールドスタート対応）

## ログの確認

```bash
# リアルタイムログ
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=vertical-text-api"

# 過去のログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertical-text-api" --limit 100
```

## トラブルシューティング

### よくある問題

1. **デプロイ時のメモリ不足**
   - Dockerfileでapt cacheをクリーンアップしているか確認

2. **フォントが見つからない**
   - フォントのダウンロードとコピーが正常に行われているか確認

3. **認証エラー**
   - API_TOKENが正しく設定されているか確認

### デバッグコマンド

```bash
# サービスの詳細確認
gcloud run services describe vertical-text-api --region asia-northeast1

# 最新のリビジョン確認
gcloud run revisions list --service vertical-text-api --region asia-northeast1
```
