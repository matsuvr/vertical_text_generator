# 家庭内サーバー用 Dockerfile（Playwright公式ベース）
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

# 依存パッケージ（日本語フォント等）
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-liberation \
    # Build dependencies for Pillow[raqm]
    pkg-config libfreetype6-dev libharfbuzz-dev libfribidi-dev \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# フォントディレクトリを作成
RUN mkdir -p /app/fonts

# Pythonの依存関係をインストール
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# フォントファイルを明示的にコピー（.gitignoreで除外されているため）
COPY fonts/ /app/fonts/

# 環境変数
ENV PORT=8000
ENV PYTHONPATH=/app
ENV PRELOAD_FONTS=1 \
    FONT_MEMORY_RESERVE_MB=128 \
    PAGE_POOL_SIZE=8 \
    PRECREATE_PAGES=1 \
    WARMUP_RENDER_ON_STARTUP=1

# ポート公開
EXPOSE 8000

# Gunicorn + Uvicorn workers で起動（環境変数でチューニング可能）
# - workers: WEB_CONCURRENCY（既定 4）
# - timeout: GUNICORN_TIMEOUT（既定 180）
# - graceful-timeout: GUNICORN_GRACEFUL_TIMEOUT（既定 30）
# - keep-alive: GUNICORN_KEEPALIVE（既定 5）
# - max-requests: GUNICORN_MAX_REQUESTS（既定 0 で無効）
ENV WEB_CONCURRENCY=4 \
    GUNICORN_TIMEOUT=180 \
    GUNICORN_GRACEFUL_TIMEOUT=30 \
    GUNICORN_KEEPALIVE=5 \
    GUNICORN_MAX_REQUESTS=0

# per-worker の Playwright ページ数（総ページは workers × PAGE_POOL_SIZE）
# gunicorn workers と合わせて調整（デフォルトは控えめに 2）
ENV PAGE_POOL_SIZE=2

CMD ["bash", "-lc", "gunicorn -k uvicorn.workers.UvicornWorker -w ${WEB_CONCURRENCY:-4} -b 0.0.0.0:${PORT:-8000} --timeout ${GUNICORN_TIMEOUT:-180} --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT:-30} --keep-alive ${GUNICORN_KEEPALIVE:-5} --max-requests ${GUNICORN_MAX_REQUESTS:-0} --preload main:app"]
