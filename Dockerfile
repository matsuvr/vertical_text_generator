# Google Cloud Run用 Dockerfile
FROM python:3.11-slim

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    # Playwright/Chrome用
    wget \
    gnupg \
    ca-certificates \
    # 日本語フォント
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-liberation \
    # その他の依存関係
    gcc \
    g++ \
    libfreetype6-dev \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# フォントディレクトリを作成
RUN mkdir -p /app/fonts

# Pythonの依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwrightのブラウザをインストール
RUN playwright install chromium
RUN playwright install-deps chromium

# アプリケーションファイルをコピー
COPY . .

# プロジェクトのfontsディレクトリにフォントファイルが存在することを確認
RUN if [ -d "./fonts" ] && [ "$(ls -A ./fonts/*.ttf 2>/dev/null)" ]; then \
        echo "フォントファイルが見つかりました: $(ls ./fonts/)"; \
        ls -la ./fonts/; \
    else \
        echo "警告: プロジェクトのfontsディレクトリにTTFファイルが見つかりません"; \
        echo "システムフォント (Noto CJK) を使用します"; \
    fi

# 環境変数設定
ENV PORT=8080
ENV PYTHONPATH=/app

# ポート公開（Cloud Runは$PORTを使用）
EXPOSE 8080

# アプリケーション起動（Cloud Run用にポート番号を環境変数から取得）
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]