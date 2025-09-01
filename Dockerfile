# Google Cloud Run用 Dockerfile
FROM python:3.11-slim

# 必要なシステムパッケージをインストール（最小構成）
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-liberation \
    # Build dependencies for Pillow[raqm]
    gcc g++ pkg-config libfreetype6-dev libharfbuzz-dev libfribidi-dev \
    # Dependencies required by headless Chromium/Playwright
    libnss3 libxss1 libasound2 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxrandr2 libgbm1 \
    fontconfig ca-certificates lsb-release wget dbus \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# フォントディレクトリを作成
RUN mkdir -p /app/fonts

# Pythonの依存関係とPlaywrightブラウザをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install --with-deps chromium

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

