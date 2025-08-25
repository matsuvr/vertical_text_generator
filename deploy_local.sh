#!/bin/bash

# 家庭内サーバーへのデプロイスクリプト
# Usage: ./deploy_local.sh [server_ip]

set -e

# デフォルトのサーバーIP
SERVER_IP=${1:-"192.168.1.45"}
SERVER_USER="yuichi"
SSH_KEY="C:/Users/Owner/.ssh/id_ed25519"
PROJECT_NAME="vertical_text_generator"
REMOTE_DIR="/home/$SERVER_USER/$PROJECT_NAME"

echo "🚀 家庭内サーバーへのデプロイを開始します"
echo "サーバー: $SERVER_USER@$SERVER_IP"
echo "プロジェクト: $PROJECT_NAME"
echo ""

# 1. サーバー接続確認
echo "📡 サーバー接続確認中..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "echo 'Connection OK'"; then
    echo "❌ サーバーに接続できません: $SERVER_USER@$SERVER_IP"
    echo "SSH設定を確認してください"
    exit 1
fi

# 2. 必要なディレクトリの作成
echo "📁 リモートディレクトリを準備中..."
ssh -i "$SSH_KEY" $SERVER_USER@$SERVER_IP "mkdir -p $REMOTE_DIR"

# 3. プロジェクトファイルをアップロード
echo "📤 プロジェクトファイルをアップロード中..."
# rsyncが無い場合はscpとtarを使用
tar --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='test_output' \
    --exclude='test_results' \
    --exclude='.venv' \
    --exclude='node_modules' \
    --exclude='project.tar.gz' \
    -czf project.tar.gz ./
scp -i "$SSH_KEY" project.tar.gz $SERVER_USER@$SERVER_IP:$REMOTE_DIR/
ssh -i "$SSH_KEY" $SERVER_USER@$SERVER_IP "cd $REMOTE_DIR && tar -xzf project.tar.gz && rm project.tar.gz"
rm project.tar.gz

# 4. リモートサーバーでDockerコンテナを構築・起動
echo "🐳 リモートサーバーでDockerコンテナを構築・起動中..."
ssh -i "$SSH_KEY" $SERVER_USER@$SERVER_IP "cd $REMOTE_DIR && docker compose -f docker-compose.local.yml down --remove-orphans && docker compose -f docker-compose.local.yml up --build -d"

# 5. ヘルスチェック
echo "🏥 サービス起動確認中..."
sleep 15  # サービス起動を少し待つ

for i in {1..10}; do
    if ssh -i "$SSH_KEY" $SERVER_USER@$SERVER_IP "curl -s http://localhost:8000/health > /dev/null"; then
        echo "✅ サービスが正常に起動しました！"
        echo ""
        echo "🎉 デプロイ完了！"
        echo "アクセス URL: http://$SERVER_IP:8000"
        echo "ヘルスチェック: http://$SERVER_IP:8000/health"
        echo "API ドキュメント: http://$SERVER_IP:8000/docs"
        echo ""
        echo "📋 APIトークン: $(cat .env | grep API_TOKEN | cut -d'=' -f2)"
        exit 0
    fi
    echo "⏳ サービス起動待機中... ($i/10)"
    sleep 3
done

echo "❌ サービスの起動確認に失敗しました"
echo "ログを確認してください:"
echo "ssh -i '$SSH_KEY' $SERVER_USER@$SERVER_IP \"cd $REMOTE_DIR && docker compose -f docker-compose.local.yml logs\""
exit 1
