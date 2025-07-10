# Dockerfile
FROM python:3.11-slim

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    # Playwright/Chrome用
    wget \
    gnupg \
    # Inkscape
    inkscape \
    # 日本語フォント
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    # その他の依存関係
    gcc \
    g++ \
    libfreetype6-dev \
    curl \
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
RUN playwright install-deps

# アプリケーションファイルをコピー
COPY . .

# 源暎アンチックフォントをダウンロード（オプション）
# 注意：実際のフォントファイルがfontsディレクトリにある場合はこの部分は不要
# RUN curl -L "https://github.com/ButTaiwan/genei-font/releases/download/v1.002/GenEiAntique_v5.zip" -o GenEiAntique.zip && \
#     unzip GenEiAntique.zip -d /app/fonts/ && \
#     rm GenEiAntique.zip && \
#     mv /app/fonts/GenEiAntique_v5/*.ttf /app/fonts/ && \
#     rm -rf /app/fonts/GenEiAntique_v5

# ポート公開
EXPOSE 8000

# アプリケーション起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]