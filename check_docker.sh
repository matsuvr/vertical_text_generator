#!/bin/bash

echo "=== Docker環境チェックスクリプト ==="
echo ""

# Dockerが実行中か確認
echo "1. Docker Desktopの状態確認..."
docker version > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Dockerは実行中です"
else
    echo "✗ Dockerが実行されていません"
    echo "  Docker Desktopを起動してください"
    exit 1
fi

echo ""
echo "2. 実行中のコンテナ確認..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "3. svg-vertical-apiコンテナの詳細..."
docker ps -a | grep svg-vertical-api

echo ""
echo "4. docker-composeの状態..."
docker-compose -f docker-compose-svg.yml ps

echo ""
echo "5. コンテナのログ（エラーチェック）..."
docker-compose -f docker-compose-svg.yml logs --tail=10 | grep -E "(ERROR|error|Error|FAIL|fail|Fail)"

echo ""
echo "6. ポート使用状況の確認..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash)
    netstat -an | grep ":8000" | grep "LISTEN"
else
    # Linux/Mac
    netstat -an | grep ":8000"
fi

echo ""
echo "=== 推奨アクション ==="
echo "問題がある場合:"
echo "1. コンテナを完全に削除して再作成:"
echo "   docker-compose -f docker-compose-svg.yml down -v"
echo "   docker-compose -f docker-compose-svg.yml up -d --build"
echo ""
echo "2. ログを詳しく確認:"
echo "   docker-compose -f docker-compose-svg.yml logs -f"