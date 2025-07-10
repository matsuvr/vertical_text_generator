# 日本語縦書きレンダリングAPI

HTML/CSS + Playwright (Chrome Headless) を使用した高品質な日本語縦書きテキストレンダリングAPIです。

## 特徴

- 🎨 **高品質レンダリング**: Chrome Headlessによる正確な縦書き表示
- 📝 **日本語最適化**: 縦中横、三点リーダー、約物の適切な処理
- 🔤 **フォント対応**: 源暎アンチックフォント内蔵（Noto Sans CJK JPフォールバック）
- ✂️ **自動改行**: BudouXによる自然な日本語改行
- 📐 **自動調整**: テキスト量に応じた画像サイズ自動調整
- 🖼️ **透明背景**: 背景透明のPNG画像生成
- 🔒 **API認証**: Bearerトークンによるシンプルな認証

## 動作環境

- Docker
- Docker Compose

## クイックスタート

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/vertical-text-generator.git
cd vertical-text-generator
```

### 2. 環境変数の設定

`.env`ファイルを作成し、APIトークンを設定します：

```bash
cp .env.example .env
```

`.env`ファイルを編集：
```
API_TOKEN=your-secure-random-token-here
```

セキュアなトークンの生成例：
```bash
openssl rand -hex 32
```

### 3. フォントファイルの配置（オプション）

源暎アンチックフォントを使用する場合は、`fonts`ディレクトリに配置：

```bash
mkdir -p fonts
# GenEiAntiqueNv5-M.ttf を fonts/ ディレクトリに配置
```

### 4. 起動

```bash
docker-compose up -d
```

### 5. API使用例

```bash
# テキストをレンダリング
curl -X POST http://localhost:8000/render \
  -H "Authorization: Bearer your-secure-random-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "こんにちは、世界！\n日本語の縦書きです。",
    "font_size": 24,
    "max_chars_per_line": 10
  }'
```

## Google Cloud Runへのデプロイ

### 前提条件

- Google Cloud Platform アカウント
- gcloud CLI インストール済み
- プロジェクトID設定済み

### デプロイ手順

#### 1. プロジェクトの設定

```bash
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID
```

#### 2. Artifact Registry の設定

```bash
# Artifact Registryを有効化
gcloud services enable artifactregistry.googleapis.com

# リポジトリ作成（初回のみ）
gcloud artifacts repositories create vertical-text-api \
  --repository-format=docker \
  --location=asia-northeast1 \
  --description="Vertical Text API Docker images"
```

#### 3. Docker イメージのビルドとプッシュ

```bash
# 認証設定
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# イメージのビルド
docker build -t asia-northeast1-docker.pkg.dev/$PROJECT_ID/vertical-text-api/app:latest .

# イメージのプッシュ
docker push asia-northeast1-docker.pkg.dev/$PROJECT_ID/vertical-text-api/app:latest
```

#### 4. Cloud Run へのデプロイ

```bash
gcloud run deploy vertical-text-api \
  --image asia-northeast1-docker.pkg.dev/$PROJECT_ID/vertical-text-api/app:latest \
  --platform managed \
  --region asia-northeast1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 10 \
  --port 8000 \
  --allow-unauthenticated \
  --set-env-vars API_TOKEN=your-secure-production-token
```

### 重要な注意事項 ⚠️

#### 1. メモリとCPUの設定
- **最小推奨**: メモリ 2GB、CPU 2コア
- Chrome Headlessは多くのリソースを使用します
- 同時実行数は10程度に制限することを推奨

#### 2. タイムアウト設定
- デフォルトの60秒では不十分な場合があります
- 300秒以上に設定することを推奨

#### 3. 環境変数の安全な管理

本番環境では、Secret Managerを使用することを強く推奨します：

```bash
# シークレットの作成
echo -n "your-secure-production-token" | gcloud secrets create api-token --data-file=-

# Cloud Runサービスアカウントに権限付与
gcloud secrets add-iam-policy-binding api-token \
  --member="serviceAccount:$(gcloud run services describe vertical-text-api --region=asia-northeast1 --format='value(spec.template.spec.serviceAccountName)')" \
  --role="roles/secretmanager.secretAccessor"

# シークレットを使用してデプロイ
gcloud run deploy vertical-text-api \
  --image asia-northeast1-docker.pkg.dev/$PROJECT_ID/vertical-text-api/app:latest \
  --platform managed \
  --region asia-northeast1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 10 \
  --port 8000 \
  --allow-unauthenticated \
  --set-secrets="API_TOKEN=api-token:latest"
```

#### 4. コールドスタート対策
- 最小インスタンス数の設定を検討：
  ```bash
  --min-instances 1
  ```
- ただし、コストが増加することに注意

#### 5. ヘルスチェックの設定
```bash
--set-env-vars "PORT=8000" \
--health-check-path="/health"
```

### デプロイ後の確認

```bash
# サービスURLの取得
SERVICE_URL=$(gcloud run services describe vertical-text-api --region=asia-northeast1 --format='value(status.url)')

# ヘルスチェック
curl $SERVICE_URL/health

# APIテスト
curl -X POST $SERVICE_URL/render \
  -H "Authorization: Bearer your-secure-production-token" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Cloud Runで動作確認",
    "font_size": 20
  }'
```

## API仕様

### エンドポイント

#### POST /render
縦書きテキストをレンダリング（要認証）

**リクエスト:**
```json
{
  "text": "レンダリングするテキスト",
  "font_size": 20,
  "width": 300,
  "height": 400,
  "line_height": 1.6,
  "letter_spacing": 0.05,
  "padding": 20,
  "auto_height": true,
  "auto_trim": true,
  "use_tategaki_js": false,
  "max_chars_per_line": 15
}
```

**レスポンス:**
```json
{
  "image_base64": "...",
  "width": 300,
  "height": 400,
  "processing_time_ms": 1234.5,
  "trimmed": true
}
```

#### GET /health
ヘルスチェック（認証不要）

#### GET /
API情報（認証不要）

## トラブルシューティング

### Cloud Runでのよくある問題

1. **メモリ不足エラー**
   - メモリを4GBに増やす
   - 同時実行数を減らす

2. **タイムアウトエラー**
   - タイムアウトを600秒に増やす
   - 画像サイズを小さくする

3. **フォントが表示されない**
   - Dockerイメージに正しくフォントが含まれているか確認
   - ビルド時にfontsディレクトリが存在するか確認

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを作成して変更内容を議論してください。
